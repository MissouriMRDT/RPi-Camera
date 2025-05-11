#!/bin/bash
if [ $# != 2 ]; then
    echo "Usage: rpicameradeploy.sh cameraip confignumber"
    exit
fi

sftp pi@$1 << EOF
lcd ~/RPi-Camera
cd ~/
put server.py server.py
chmod 744 server.py
put config$2.toml config.toml
mkdir RoveComm_Python
put RoveComm_Python/rovecomm.py RoveComm_Python/rovecomm.py
mkdir RoveComm_Python/manifest
put RoveComm_Python/manifest/manifest.json RoveComm_Python/manifest/manifest.json
mkdir pictures
EOF
