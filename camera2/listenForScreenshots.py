import subprocess
from rovecomm.rovecomm import RoveComm, RoveCommPacket, get_manifest

def takeScreenshot(packet):
    index = packet.data[0]-5
    s = subprocess.call(f"takeScreenshot.sh {index}")

rovecomm_node = RoveComm()
rovecomm_node.set_callback(manifest["Camera2"]["Commands"]["ExportScreenshots"]["dataId"], takeScreenshot )
