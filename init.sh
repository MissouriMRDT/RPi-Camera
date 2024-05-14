#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <camera_pi_board_number>"
    exit 1
fi

camera_pi_board_number="$1"

# Check if camera_pi_board_number is either 1 or 2
if [ "$camera_pi_board_number" != "1" ] && [ "$camera_pi_board_number" != "2" ]; then
    echo "Invalid camera pi board number. Please specify either 1 or 2."
    exit 1
fi

# Copy files from the selected camera directory to the $HOME directory
if [ "$camera_pi_board_number" -eq 1 ]; then
    cp -r camera1/* $HOME
    echo "Files copied from camera1 to $HOME"
elif [ "$camera_pi_board_number" -eq 2 ]; then
    cp -r camera2/* $HOME
    echo "Files copied from camera2 to $HOME"
fi

# Copy the service to the system directory
sudo cp cameras.service /etc/systemd/system/cameras.service

# Copy the shared files to the $HOME directory
find . -maxdepth 1 -name '*.sh' ! -name "init.sh" -exec cp {} $HOME \;
cp -r RoveComm_Python $HOME

# Move Interface Files
sudo mv "$HOME/interfaces" /etc/network/interfaces

# Make Shell Scripts Executable
chmod +x ~/*.sh

# Make Screenshots Directory
if [ ! -d "$HOME/Screenshots" ]; then
    mkdir -p "$HOME/Screenshots"
fi

# Exit Script
exit 0

