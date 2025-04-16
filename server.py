#!/bin/python3
import subprocess
import os
import RoveComm_Python.rovecomm as rovecomm
import time
import tomllib
import logging
import re
import threading

logging.basicConfig(
    format="%(funcName)s:%(lineno)d [%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%H:%M:%S",
)

rovecomm_logger = logging.getLogger(rovecomm.__file__)
rovecomm_logger.basicConfig(
    format="rovecomm:%(lineno)d [%(levelname)s] %(asctime)s - %(message)s",
    datefmt="%H:%M:%S",
)

manifest = get_manifest()
rovecomm_node = RoveComm()

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
    logging.info(f"Starting stream {index}.")
    devices = get_devices()
    if index >= len(devices):
        logging.warn(f"Cannot start stream {index} with {len(devices)} devices.")
        return
    if index >= len(config["ports"]):
        logging.warn(f"Cannot start stream {index} with {len(config['ports'])} ports.")
        return
    if index >= len(streamers):
        streamers.extend([None] * (index - len(streamers) + 1))

    if streamers[index] != None:
        stop_stream(index)

    substitutions = [
        ("$index", index),
        ("$input", devices[index]),
        ("$ip", config["ip"]),
        ("$port", config["ports"][index]),
    ]
    arguments = [config["ffmpeg_path"]]
    for argument in config["ffmpeg_arguments"]:
        for sub in substitutions:
            argument.replace(sub[0], sub[1])
        arguments.append(argument)
    streamers[index] = subprocess.Popen(arguments)
    logging.info(f"Started stream {index}.")


def stop_stream(index):
    logging.info(f"Stopping stream {index}.")
    if index >= len(streamers) or streamers[index] == None:
        logging.warn(f"Stream {index} does not exist.")
        return
    try:
        streamers[index].terminate()
        streamers[index].communicate(timeout=3)
    except:
        logging.warn(f"Failed to terminate stream {index}. Killing stream {index}.")
        streamers[index].kill()
    streamers[index] = None
    logging.info(f"Stopped stream {index}.")


def stop_restart_stream(packet):
    index = packet.data[0]
    restart = packet.data[1]
    if restart == 0:
        threading.Thread(target=stop_stream, args=(index,))
    else:
        threading.Thread(target=start_stream, args=(index,))


def take_screenshot_callback(packet):
    index = packet.data[0]
    restart = packet.data[1]
    threading.Thread(
        target=take_screenshot,
        args=(
            index,
            restart,
            config["screenshot_dir"],
            manifest[config["manifest"]["device"]]["Telemetry"][
                config["manifest"]["screenshot_telemetry"]
            ]["dataId"],
            config["fswebcam_path"],
            config["fswebcam_arguments"],
        ),
    )


def take_screenshot(
    index, restart, screenshot_dir, data_id, fswebcam_path, fswebcam_arguments
):
    logging.info(f"Taking screenshot from {index}.")
    devices = get_devices()
    if index >= len(devices):
        logging.warn(f"Cannot take screenshot {index} with {len(devices)} devices.")
        return

    stop_stream(index)

    arguments = [fswebcam_path]
    substitutions = [
        ("$input", devices[index]),
        ("$output", time.strftime("%Y%m%d_%H%M%S")),
    ]
    for argument in fswebcam_arguments:
        for sub in substitutions:
            argument.replace(sub[0], sub[1])
        arguments.append(argument)
    before_count = 0
    after_count = 0
    try:
        before_count = len(os.listdir(screenshot_dir))
        subprocess.run(arguments, timeout=10)
        after_count = len(os.listdir(screenshot_dir))
    except:
        logging.exception(f"Failed to take screenshot from {index}.")

    if after_count == before_count + 1:
        logging.info(f"New screenshot found.")
        packet = rovecomm.RoveCommPacket(
            data_id,
            "B",
            (1,),
        )
        rovecomm_node.write(packet, False)
    else:
        logging.info(f"No screenshot found.")

    if restart:
        start_stream(index)


config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")
logging.info(f"Reading config file from {config_path}.")
try:
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
        assert type(config["ports"]) == list
        for port in config["ports"]:
            assert type(port) == int and port > 0
        assert type(config["ip"]) == str
        assert type(config["ffmpeg_path"]) == str
        for argument in config["ffmpeg_arguments"]:
            assert type(argument) == str
        assert type(config["screenshot_dir"]) == str
        assert type(config["manifest"]["device"]) == str
        assert type(config["manifest"]["stop_restart_command"]) == str
        assert type(config["manifest"]["screenshot_command"]) == str
        assert type(config["manifest"]["screenshot_telemetry"]) == str
        assert type(config["manifest"]["connected_cameras_telemetry"]) == str
        assert type(config["manifest"]["streams_telemetry"]) == str
except:
    logging.exception(f"Failed to read config file {config_path}.")
    exit(1)

logging.info("Registering rovecomm callbacks.")
try:
    rovecomm_node.set_callback(
        manifest[config["manifest"]["device"]]["Commands"][
            config["manifest"]["screenshot_command"]
        ]["dataId"],
        take_screenshot_callback,
    )
    rovecomm_node.set_callback(
        manifest[config["manifest"]["device"]]["Commands"][
            config["manifest"]["stop_restart_command"]
        ]["dataId"],
        stop_restart_stream,
    )
except:
    logging.exception(f"Failed to register rovecomm callbacks.")
    exit(1)

while True:
    rovecomm_node.write(
        rovecomm.packet(
            config["manifest"]["device"],
            "Telemetry",
            config["manifest"]["connected_cameras_telemetry"],
            (len(get_devices()),),
        ),
        False,
    )
    rovecomm_node.write(
        rovecomm.packet(
            config["manifest"]["device"],
            "Telemetry",
            config["manifest"]["streams_telemetry"],
            tuple([streamer == None for streamer in streamers]),
        ),
        False,
    )
    time.sleep(5)
