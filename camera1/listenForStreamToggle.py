import subprocess
import os
from RoveComm_Python.rovecomm import RoveComm, RoveCommPacket, get_manifest
import time

manifest = get_manifest()
rovecomm_node = RoveComm()


def toggleStream(packet):
    index = packet.data[0]
    startStream = packet.data[1]

    if startStream == 0:
        subprocess.Popen(["home/pi/stopStream.sh", str(index)])
    elif startStream == 1:
        subprocess.Popen(["home/pi/startStream.sh", str(index)])
    else:
        print("Invalid startStream value")


def main():
    rovecomm_node.set_callback(
        manifest["Camera1"]["Commands"]["ToggleStream1"]["dataId"], toggleStream
    )
    while True:
        pass


main()
