#!/bin/python3
import subprocess
import time
import os
import RoveComm_Python.rovecomm as rovecomm
import tomllib
import threading
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(
    logging.Formatter(
        "%(funcName)s:%(lineno)d [%(levelname)s] %(asctime)s - %(message)s",
        "%H:%M:%S",
    )
)
logger.addHandler(ch)

rovecomm_logger = logging.getLogger(rovecomm.__file__)
rovecomm_formatter = logging.Formatter(
    "rovecomm:%(lineno)d [%(levelname)s] %(asctime)s - %(message)s", "%H:%M:%S"
)

manifest = rovecomm.get_manifest()
rovecomm_node = rovecomm.RoveComm(tcp_addr=("0.0.0.0", rovecomm.ROVECOMM_TCP_PORT))

streamers = []
config = {}


def get_devices():
    """
    Return the first device file under each usb device returned by v4l2-ctl --list-devices
    """
    output = subprocess.run(
        ["v4l2-ctl", "--list-devices"], capture_output=True, timeout=5, encoding="utf_8"
    ).stdout
    return re.findall("\\(usb.+\\n[ \\t]*(.+)", output)


def start_stream(index):
    logger.info(f"Starting stream {index}.")
    devices = get_devices()
    if index >= len(devices):
        logger.warning(f"Cannot start stream {index} with {len(devices)} devices.")
        return
    if index >= len(config["ports"]):
        logger.warning(
            f"Cannot start stream {index} with {len(config['ports'])} ports."
        )
        return
    if index >= len(streamers):
        streamers.extend([None] * (index - len(streamers) + 1))

    if streamers[index] != None:
        stop_stream(index)

    substitutions = [
        ("$index", str(index)),
        ("$input", devices[index]),
        ("$ip", config["ip"]),
        ("$port", str(config["ports"][index])),
    ]
    arguments = ["taskset", "--cpu-list", str(index % 4), config["ffmpeg_path"]]
    for argument in config["ffmpeg_arguments"]:
        for sub in substitutions:
            argument = argument.replace(sub[0], sub[1])
        arguments.append(argument)
    logger.debug(f"ffmpeg arguments: {' '.join(arguments)}.")
    streamers[index] = subprocess.Popen(
        arguments, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )
    logger.info(f"Started stream {index}.")


def stop_stream(index):
    logger.info(f"Stopping stream {index}.")
    if index >= len(streamers) or streamers[index] == None:
        logger.warning(f"Stream {index} does not exist.")
        return
    try:
        streamers[index].terminate()
        streamers[index].communicate(timeout=3)
    except:
        logger.warning(f"Failed to terminate stream {index}. Killing stream {index}.")
        streamers[index].kill()
    streamers[index] = None
    logger.info(f"Stopped stream {index}.")


def stop_restart_stream(packet):
    index = packet.data[0]
    restart = packet.data[1]
    if restart == 0:
        threading.Thread(target=stop_stream, args=(index,)).start()
    else:
        threading.Thread(target=start_stream, args=(index,)).start()


def take_picture_callback(packet):
    index = packet.data[0]
    restart = packet.data[1]
    threading.Thread(
        target=take_picture,
        args=(
            index,
            restart,
            config["picture_dir"],
            manifest[config["manifest"]["device"]]["Telemetry"][
                config["manifest"]["telemetry"]["picture"]
            ]["dataId"],
            config["picture_path"],
            config["picture_arguments"],
        ),
    ).start()


def take_picture(index, restart, picture_dir, data_id, picture_path, picture_arguments):
    logger.info(f"Taking picture from {index}.")
    devices = get_devices()
    if index >= len(devices):
        logger.warning(f"Cannot take picture {index} with {len(devices)} devices.")
        return

    stop_stream(index)

    arguments = [picture_path]
    substitutions = [
        ("$index", str(index)),
        ("$input", devices[index]),
        ("$output", picture_dir + "/" + time.strftime("%Y%m%d_%H%M%S")),
    ]
    for argument in picture_arguments:
        for sub in substitutions:
            argument = argument.replace(sub[0], sub[1])
        arguments.append(argument)
    before_count = 0
    after_count = 0
    try:
        before_count = len(os.listdir(picture_dir))
        logger.debug(f"picture arguments: {' '.join(arguments)}.")
        subprocess.run(arguments, timeout=10)
        after_count = len(os.listdir(picture_dir))
    except:
        logger.exception(f"Failed to take picture from {index}.")

    if after_count == before_count + 1:
        logger.info(f"New picture found.")
        packet = rovecomm.RoveCommPacket(
            data_id,
            "B",
            (1,),
        )
        rovecomm_node.write(packet, False)
    else:
        logger.warning(f"No picture found.")

    if restart:
        start_stream(index)


def set_ffmpeg_arguments(packet):
    try:
        # Decode 0x04 terminated 0x1f delimited character array into an array of utf-8 strings.
        arguments = [
            argument.decode("utf-8")
            for argument in b"".join(packet.data).partition(b"\x04")[0].split(b"\x1f")
        ]
    except:
        logger.exception("Failed to decode ffmpeg_arguments.")
        return
    logger.info(f"Set ffmpeg_arguments to {arguments}.")
    config["ffmpeg_arguments"] = arguments


def set_picture_arguments(packet):
    try:
        # Decode 0x04 terminated 0x1f delimited character array into an array of utf-8 strings.
        arguments = [
            argument.decode("utf-8")
            for argument in b"".join(packet.data).partition(b"\x04")[0].split(b"\x1f")
        ]
    except:
        logger.exception("Failed to decode picture_arguments.")
        return
    logger.info(f"Set picture_arguments to {arguments}.")
    config["picture_arguments"] = arguments


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
logger.info(f"Reading config file from {config_path}.")
try:
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
        assert type(config["ports"]) == list
        for port in config["ports"]:
            assert type(port) == int and port > 0
        assert type(config["ip"]) == str
        assert type(config["nproc"]) == int
        assert type(config["ffmpeg_path"]) == str
        for argument in config["ffmpeg_arguments"]:
            assert type(argument) == str
        assert type(config["picture_path"]) == str
        for argument in config["picture_arguments"]:
            assert type(argument) == str
        assert type(config["picture_dir"]) == str
        assert type(config["manifest"]["device"]) == str
        assert type(config["manifest"]["command"]["stop_restart"]) == str
        assert type(config["manifest"]["command"]["picture"]) == str
        assert type(config["manifest"]["command"]["ffmpeg_arguments"]) == str
        assert type(config["manifest"]["command"]["picture_arguments"]) == str
        assert type(config["manifest"]["telemetry"]["picture"]) == str
        assert type(config["manifest"]["telemetry"]["connected_cameras"]) == str
        assert type(config["manifest"]["telemetry"]["streams"]) == str
        assert type(config["manifest"]["telemetry"]["utilization"]) == str
except:
    logger.exception(f"Failed to read config file {config_path}.")
    exit(1)

logger.info("Registering rovecomm callbacks.")
try:
    rovecomm_node.set_callback(
        manifest[config["manifest"]["device"]]["Commands"][
            config["manifest"]["command"]["picture"]
        ]["dataId"],
        take_picture_callback,
    )
    rovecomm_node.set_callback(
        manifest[config["manifest"]["device"]]["Commands"][
            config["manifest"]["command"]["stop_restart"]
        ]["dataId"],
        stop_restart_stream,
    )
    rovecomm_node.set_callback(
        manifest[config["manifest"]["device"]]["Commands"][
            config["manifest"]["command"]["ffmpeg_arguments"]
        ]["dataId"],
        set_ffmpeg_arguments,
    )
    rovecomm_node.set_callback(
        manifest[config["manifest"]["device"]]["Commands"][
            config["manifest"]["command"]["picture_arguments"]
        ]["dataId"],
        set_picture_arguments,
    )
except:
    logger.exception(f"Failed to register rovecomm callbacks.")
    exit(1)

last_total_cpu_time = [1, 1, 1, 1]
last_idle_cpu_time = [1, 1, 1, 1]

while True:
    connected = len(get_devices())
    streaming = sum(
        0 if streamer == None or streamer.poll() != None else 1
        for streamer in streamers
    )
    logger.debug(f"Cameras {connected} connected {streaming} streaming.")

    utilization = []
    try:
        with open("/proc/stat", "r") as f:
            devices = {
                line.split(" ")[0]: [float(element) for element in line.split(" ")[1:]]
                for line in f.readlines()
            }
        total_cpu_time = [sum(devices[f"cpu{cpu}"]) for cpu in range(4)]
        idle_cpu_time = [devices[f"cpu{cpu}"][3] for cpu in range(4)]
        utilization.extend(
            [
                int(100 - (i - t) / (li - lt) * 100)
                for i, t, li, lt in zip(
                    idle_cpu_time,
                    total_cpu_time,
                    last_idle_cpu_time,
                    last_total_cpu_time,
                )
            ]
        )
    except:
        logger.exception("Failure decoding /proc/stat.")
        utilization.extend([0, 0, 0, 0])
    try:
        with open("/proc/meminfo", "r") as f:
            mem_total = float(f.readline().strip().split(" ").split(" ")[-2])
            f.readline()
            mem_available = float(f.readline().strip().split(" ").split(" ")[-2])
            utilization.append(int(mem_available / mem_total * 100))
    except:
        logger.exception("Failure decoding /proc/meminfo.")
        utilization.append(0)
    try:
        statvfs = os.statvfs("/")
        utilization.append(int(statvfs.f_bavail / statvfs.f_blocks * 100))
    except:
        logger.exception('Failure decoding os.statvfs("/").')
        utilization.append(0)

    rovecomm_node.write(
        rovecomm.packet(
            config["manifest"]["device"],
            "Telemetry",
            config["manifest"]["telemetry"]["connected_cameras"],
            (connected,),
        ),
        False,
    )
    rovecomm_node.write(
        rovecomm.packet(
            config["manifest"]["device"],
            "Telemetry",
            config["manifest"]["telemetry"]["streams"],
            (streaming,),
        ),
        False,
    )
    rovecomm_node.write(
        rovecomm.packet(
            config["manifest"]["device"],
            "Telemetry",
            config["manifest"]["telemetry"]["utilization"],
            utilization,
        )
    )
    time.sleep(5)
