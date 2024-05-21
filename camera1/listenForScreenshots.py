import subprocess
import os
from RoveComm_Python.rovecomm import RoveComm, RoveCommPacket, get_manifest
import time

manifest = get_manifest()
rovecomm_node = RoveComm()

def takeScreenshot(packet):
    index = packet.data[0]
    startStream = packet.data[1]
    screenshot_dir = "/home/pi/Screenshots"

    # Get the number of files in the directory before taking the screenshot
    before_count = len(os.listdir(screenshot_dir))

    # Start the screenshot process
    if startStream:
        subprocess.Popen(["./takeScreenshot.sh", str(index)])
    else:
        subprocess.Popen(["./takePano.sh", str(index)])


    # Check if the screenshot file exists
    while not len(os.listdir(screenshot_dir)) == before_count+1:
        time.sleep(1)  # Wait for 1 second before checking again

    # Get the number of files in the directory after taking the screenshot
    after_count = len(os.listdir(screenshot_dir))

    # Check if there is one more file after taking the screenshot
    if after_count == before_count + 1:
        packet = RoveCommPacket(manifest["Camera1"]["Telemetry"]["PictureTaken1"]["dataId"], "B", (1,))
        rovecomm_node.write(packet, False)


def main():
    rovecomm_node.set_callback(manifest["Camera1"]["Commands"]["TakePicture"]["dataId"], takeScreenshot)
    while True:
        pass

main()

