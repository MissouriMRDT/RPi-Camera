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

# [Lat, Lon, Alt, HorizontalAccuracy, VerticalAccuracy, HeadingAccuracy, FixType, IsDifferential]
# (deg, deg, m, m, m, deg, ublox_navpvt fix type http://docs.ros.org/en/noetic/api/ublox_msgs/html/msg/NavPVT.html, bool)
position = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
# [Heading] (0 - 360)
heading = 0.0


def lerp(x, x1, x2, y1, y2):
    return ((y2 - y1) * x + x2 * y1 - x1 * y2) / (x2 - x1)


def clamp(x, x1, x2):
    return x1 if x < x1 else (x2 if x > x2 else x)


def lerp_clamp(x, x1, x2, y1, y2):
    return clamp(lerp(x, x1, x2, y1, y2), y1, y2)


def update_position(packet):
    global position
    position = packet.data


def update_compass(packet):
    global heading
    heading = packet.data[0]


def get_devices():
    """
    For each device in config["device"], return the first device file under that device found in v4l2-ctl --list-devices
    """
    try:
        output = subprocess.run(
            ["v4l2-ctl", "--list-devices"],
            capture_output=True,
            timeout=10,
            encoding="utf_8",
        ).stdout
        devices = [None for _ in range(len(config["device"]))]
        for found_id, found_file in re.findall(r"\(([^)]*)\):\n[\t ]*(.+)*", output):
            for index, search_id in enumerate((d["id"] for d in config["device"])):
                if search_id == found_id:
                    devices[index] = found_file
    except Exception:
        logger.warning("Failed to get devices.")
        devices = [None for _ in range(len(config["device"]))]
    return devices


def start_stream(index):
    logger.info(f"Starting stream {index}.")
    if index >= len(config["device"]):
        logger.warning(
            f"Cannot start stream {index} with {config['device']} configured devices."
        )
        return
    device_config = config["device"][index]
    device = get_devices()[index]

    if device is None:
        logger.warning(
            f"Cannot start stream {index}: Device {device_config['id']} not found."
        )
        return

    if streamers[index] is not None:
        stop_stream(index)

    substitutions = [
        ("$index", str(index)),
        ("$input", device),
        ("$ip", config["ip"]),
        ("$port", str(device_config["port"])),
        ("$now", time.strftime("%Y%m%d_%H%M%S")),
    ]
    arguments = ["taskset", "--cpu-list", str(index % 4), config["ffmpeg_path"]]
    for argument in device_config["ffmpeg_arguments"]:
        for sub in substitutions:
            argument = argument.replace(sub[0], sub[1])
        arguments.append(argument)
    logger.debug(f"ffmpeg arguments: {' '.join(arguments)}.")
    streamers[index] = subprocess.Popen(arguments)
    logger.info(f"Started stream {index}.")


def stop_stream(index):
    logger.info(f"Stopping stream {index}.")
    if index >= len(streamers) or streamers[index] is None:
        logger.warning(f"Stream {index} does not exist.")
        return
    try:
        streamers[index].terminate()
        streamers[index].communicate(timeout=3)
    except Exception:
        logger.warning(f"Failed to terminate stream {index}. Killing stream {index}.")
        streamers[index].kill()
    streamers[index] = None
    logger.info(f"Stopped stream {index}.")


def toggle_stream_callback(packet):
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
            manifest[config["name"]]["Telemetry"]["PictureTaken"]["dataId"],
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
        (
            "$position",
            f"{position[0]}\xb0N {position[1]}\xb0E\xb1{position[3]:.2f}m {position[2]}m\xb1{position[4]:.2f}m {heading:.2f}\xb0\xb1{position[4]:.2f}\xb0",
        ),
        ("$now", time.strftime("%Y%m%d_%H%M%S")),
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
        subprocess.run(arguments)
        after_count = len(os.listdir(picture_dir))
    except Exception:
        logger.exception(f"Failed to take picture from {index}.")

    if after_count == before_count + 1:
        logger.info("New picture found.")
        packet = rovecomm.RoveCommPacket(
            data_id,
            "B",
            (1,),
        )
        rovecomm_node.write(packet, False)
    else:
        logger.warning("No picture found.")

    if restart:
        start_stream(index)


def set_ffmpeg_arguments(packet):
    try:
        # Decode 0x04 terminated 0x1f delimited character array into an array of utf-8 strings.
        # Byte afte 0x04 is the device index.
        list_, _, i = b"".join(packet.data).partition(b"\x04")
        arguments = [argument.decode("utf-8") for argument in list_.split(b"\x1f")]
        if len(i) > 0 and i[0] < len(config["device"]):
            config["device"][i[0]]["ffmpeg_arguments"] = arguments
            logger.info(f"Set device.{i[0]}.ffmpeg_arguments to {arguments}.")
        else:
            # Device index out of range, set all arguments
            for device in config["device"]:
                device["ffmpeg_arguments"] = list(arguments)
        logger.info(f"Set device.*.ffmpeg_arguments to {arguments}.")
    except UnicodeDecodeError:
        logger.exception("Failed to decode ffmpeg_arguments.")
        return


def set_picture_arguments(packet):
    try:
        # Decode 0x04 terminated 0x1f delimited character array into an array of utf-8 strings.
        # Byte afte 0x04 is the device index.
        list_, _, i = b"".join(packet.data).partition(b"\x04")
        arguments = [argument.decode("utf-8") for argument in list_.split(b"\x1f")]
        if len(i) > 0 and i[0] < len(config["device"]):
            config["device"][i[0]]["picture_arguments"] = arguments
            logger.info(f"Set device.{i[0]}.picture_arguments to {arguments}.")
        else:
            # Device index out of range, set all arguments
            for device in config["device"]:
                device["picture_arguments"] = list(arguments)
        logger.info(f"Set device.*.picture_arguments to {arguments}.")
    except Exception:
        logger.exception("Failed to decode picture_arguments.")
        return


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
logger.info(f"Reading config file from {config_path}.")
try:
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
except Exception:
    logger.exception(f"Failed to read config file {config_path}.")
    exit(1)
try:
    assert type(config["name"]) is str
    assert type(config["ip"]) is str
    assert type(config["ffmpeg_path"]) is str
    assert type(config["picture_path"]) is str
    assert type(config["picture_dir"]) is str
    for argument in config["ffmpeg_arguments"]:
        assert type(argument) is str
    for argument in config["picture_arguments"]:
        assert type(argument) is str
    assert type(config["device"]) is list
    for device in config["device"]:
        assert type(device["port"]) is int and device["port"] > 0
        assert type(device["id"]) is str
        if "ffmpeg_arguments" in device:
            for argument in config["ffmpeg_arguments"]:
                assert type(argument) is str
        else:
            # Copy default ffmpeg_arguments
            device["ffmpeg_arguments"] = list(config["ffmpeg_arguments"])
        if "picture_arguments" in device:
            for argument in config["picture_arguments"]:
                assert type(argument) is str
        else:
            # Copy default picture_arguments
            device["picture_arguments"] = list(config["picture_arguments"])
        streamers.append(None)
except Exception:
    logger.exception("Invalid config file.")
    exit(1)

logger.info("Subscribing to rovecomm Nav.")
try:
    rovecomm_node.udp_node.subscribe(manifest["Nav"]["Ip"])
except Exception:
    logger.exception("Failed to subscribe to rovecomm Nav.")

brightness = tuple([config["brightness"] for _ in range(len(config["ports"]))])
contrast = tuple([config["contrast"] for _ in range(len(config["ports"]))])

logger.info("Subscribing to rovecomm Nav.")
try:
    rovecomm_node.udp_node.subscribe(manifest["Nav"]["Ip"])
except:
    logger.exception("Failed to subscribe to rovecomm Nav.")

logger.info("Registering rovecomm callbacks.")
try:
    camera_commands = manifest[config["name"]]["Commands"]
    rovecomm_node.set_callback(
        camera_commands["TakePicture"]["dataId"],
        take_picture_callback,
    )
    rovecomm_node.set_callback(
        camera_commands["ToggleStream"]["dataId"],
        toggle_stream_callback,
    )
    rovecomm_node.set_callback(
        camera_commands["SetFFMPEGArguments"]["dataId"],
        set_ffmpeg_arguments,
    )
    rovecomm_node.set_callback(
        camera_commands["SetPictureArguments"]["dataId"],
        set_picture_arguments,
    )
    nav_telemetry = manifest["Nav"]["Telemetry"]
    rovecomm_node.set_callback(nav_telemetry["GPSLatLonAlt"]["dataId"], update_position)
    rovecomm_node.set_callback(nav_telemetry["CompassData"]["dataId"], update_compass)

except Exception:
    logger.exception("Failed to register rovecomm callbacks.")
    exit(1)

last_total_cpu_time = [1, 1, 1, 1]
last_idle_cpu_time = [1, 1, 1, 1]

while True:
    connected = sum(
        (0 if device is None else 1 << i for i, device in enumerate(get_devices()))
    )
    streaming = sum(
        (
            0 if streamer is None or streamer.poll() is not None else 1 << i
            for i, streamer in enumerate(streamers)
        )
    )

    utilization = []
    try:
        with open("/proc/stat", "r") as f:
            devices = {
                line.split(" ")[0]: [
                    float(element.strip()) if len(element) > 0 else 0.0
                    for element in line.split(" ")[1:]
                ]
                for line in f.readlines()
            }
        total_cpu_time = [sum(devices[f"cpu{cpu}"]) for cpu in range(4)]
        idle_cpu_time = [devices[f"cpu{cpu}"][3] for cpu in range(4)]
        utilization.extend(
            [
                int(100 - (i - li) / (t - lt) * 100)
                for i, li, t, lt in zip(
                    idle_cpu_time,
                    last_idle_cpu_time,
                    total_cpu_time,
                    last_total_cpu_time,
                )
            ]
        )
        last_total_cpu_time = total_cpu_time
        last_idle_cpu_time = idle_cpu_time
    except Exception:
        logger.exception("Failure decoding /proc/stat.")
        utilization.extend([0, 0, 0, 0])
    try:
        with open("/proc/meminfo", "r") as f:
            mem_total = float(f.readline().strip().split(" ")[-2])
            f.readline()
            mem_available = float(f.readline().strip().split(" ")[-2])
            utilization.append(int(100 - mem_available / mem_total * 100))
    except Exception:
        logger.exception("Failure decoding /proc/meminfo.")
        utilization.append(0)
    try:
        statvfs = os.statvfs("/")
        utilization.append(int(100 - statvfs.f_bavail / statvfs.f_blocks * 100))
    except Exception:
        logger.exception('Failure decoding os.statvfs("/").')
        utilization.append(0)

    logger.debug(
        f"connected: {connected:04b}, streaming: {streaming:04b}, utilization: {utilization}"
    )

    rovecomm_node.write(
        rovecomm.packet(
            config["name"],
            "Telemetry",
            "AvailableCameras",
            (connected, streaming),
        ),
        False,
    )
    rovecomm_node.write(
        rovecomm.packet(
            config["name"],
            "Telemetry",
            "Utilization",
            utilization,
        )
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
