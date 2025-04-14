#!/bin/bash

declare -a portList
portList=("1181" "1182" "1183" "1184")

# Function to capture image using selected camera
capture_image() {
    local device="$selected_device"
    local timestamp=$(date +%s)
    local output_dir="./Screenshots"
    local output_file="$output_dir/$timestamp.jpg"

    # Create the directory if it doesn't exist
    mkdir -p "$output_dir" || { echo "Error: Unable to create directory $output_dir"; exit 1; }

    # Check if any process is using the device and terminate them
    fuser -k "$device"

    # Timeout in seconds for checking device availability
    local timeout_seconds=5
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout_seconds))

    # Check if device becomes available within the timeout period
    while true; do
        if ! fuser -s "$device"; then
            break
        fi

        if [ "$(date +%s)" -ge "$end_time" ]; then
            echo "Error: Device $device is busy. Timeout reached."
            exit 1
        fi

        sleep 1
    done

    # Capture image with additional options for troubleshooting
    if ! fswebcam -d "$device" -r 2560x1440  --no-banner --jpeg 85 --skip 100 "$output_file"; then
    # if ! ffmpeg -i "$device" -frames:v 1 "$output_file"; then
        echo "Error: Failed to capture image using device $device"
        exit 1
    fi

    echo "Image captured and saved as $output_file"
}

# Function to get list of USB cameras
get_usb_cameras() {
    v4l2-ctl --list-devices | awk '/usb/{getline; print $NF}'
}

# Main function
main() {
    # Print list of camera devices
    echo "Available USB Cameras:"
    local usb_cameras
    usb_cameras=($(get_usb_cameras))
    for ((i = 0; i < ${#usb_cameras[@]}; i++)); do
        echo "[$i] ${usb_cameras[$i]}"
    done

    # Check if at least one argument is provided
    if [ $# -ne 1 ]; then
        echo "Usage: $0 <camera_index>"
        exit 1
    fi

    # Check if the index is within the range of available USB camera devices
    local camera_index="$1"
    local num_cameras="${#usb_cameras[@]}"

    if (( camera_index < 0 || camera_index >= num_cameras )); then
        echo "Error: Invalid index. Please provide a valid index between 0 and $((num_cameras - 1))."
        exit 1
    fi

    # Select the device
    selected_device="${usb_cameras[$camera_index]}"
    echo "Selected device: $selected_device"

    # Capture image
    echo "Capturing image..."
    capture_image
    echo "Image captured."
}

# Call main function
main "$@"

