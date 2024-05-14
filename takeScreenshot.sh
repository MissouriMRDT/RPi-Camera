#!/bin/bash

# Function to list available USB camera devices
list_usb_devices() {
    printf "Available USB cameras:\n"
    ls /dev/video* | while read -r device; do
        if v4l2-ctl --list-devices "$device" | grep -q "(usb"; then
            echo "$device"
        fi
    done
}

# Function to capture image using selected camera
capture_image() {
    local device="$1"
    local timestamp=$(date +%s)
    local output_dir="./Screenshots"
    local output_file="$output_dir/$timestamp.jpg"
    
    # Create the directory if it doesn't exist
    mkdir -p "$output_dir"
    
    fswebcam -r 3840x2160 --delay 5 --skip 200 --no-banner "$output_file" -d "$device"
    
    echo "Image captured and saved as $output_file"
}

# List available USB camera devices
list_usb_devices

# Check if the index is provided as a command-line argument
if [ -z "$1" ]; then
    echo "Error: Please provide the index of the USB camera as a command-line argument."
    exit 1
fi

# Get the USB camera device corresponding to the provided index
camera_index="$1"
camera_devices=($(ls /dev/video* | while read -r device; do
    if v4l2-ctl --list-devices "$device" | grep -q "(usb"; then
        echo "$device"
    fi
done))

# Check if the index is within the range of available USB camera devices
if (( camera_index >= 0 && camera_index < ${#camera_devices[@]} )); then
    selected_device="${camera_devices[$camera_index]}"
    capture_image "$selected_device"
else
    echo "Error: Invalid index. Please provide a valid index."
    exit 1
fi

