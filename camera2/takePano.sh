!/bin/bash

declare -a portList
portList=("1185" "1186" "1187" "1188")

# Function to capture image using selected camera
capture_image() {
    local device="$selected_device"
    local timestamp=$(date +%s)
    local output_dir="./Screenshots"
    local output_file="$output_dir/$timestamp.jpg"

    # Create the directory if it doesn't exist
    mkdir -p "$output_dir" || { echo "Error: Unable to create directory $output_dir"; exit 1; }

    # Capture image
    if ! fswebcam -r 2560x1440 --delay 1 --skip 50 --no-banner "$output_file" -d "$device"; then
        echo "Error: Failed to capture image using device $device"
        exit 1
    fi

    echo "Image captured and saved as $output_file"
}

# Function to get list of USB cameras
get_usb_cameras() {
    v4l2-ctl --list-devices | awk '/usb/{getline; print $NF}'
}

# Function to get PID of ffmpeg process
get_ffmpeg_pid() {
    local device="$1"
    pgrep -f "ffmpeg.*$device"
}

# Function to stop ffmpeg process
stop_ffmpeg_process() {
    local device="$1"
    local pid
    pid=$(get_ffmpeg_pid "$device")
    if [ -n "$pid" ]; then
        echo "Stopping ffmpeg process (PID: $pid)..."
        kill -TSTP "$pid" >/dev/null 2>&1
        sleep 1
        # Check if process is still running
        if ps -p "$pid" > /dev/null; then
            # If process is still running, send SIGKILL
            echo "Sending SIGKILL to ffmpeg process (PID: $pid)..."
            kill -KILL "$pid" >/dev/null 2>&1
        fi
    else
        echo "No ffmpeg process found for device $device"
    fi
}

# Function to resume ffmpeg process
resume_ffmpeg_process() {
    echo ${portList[$camera_index]}
    echo "$selected_device"
    bash startOne.sh ${portList[$camera_index]} "$selected_device" &
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

5A    # Check if the index is within the range of available USB camera devices
    local camera_index="$1"
    local usb_cameras
    usb_cameras=($(get_usb_cameras))
    local num_cameras="${#usb_cameras[@]}"

    if (( camera_index < 0 || camera_index >= num_cameras )); then
        echo "Error: Invalid index. Please provide a valid index between 0 and $((num_cameras - 1))."
        exit 1
    fi

    # Select the device
    selected_device="${usb_cameras[$camera_index]}"
    echo "Selected device: $selected_device"

    # Stop ffmpeg process
    stop_ffmpeg_process "$selected_device"

    # Capture image
    echo "Capturing image..."
    capture_image
    echo "Image captured."
}

# Call main function
main "$@"
