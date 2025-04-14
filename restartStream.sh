#!/bin/bash

# File to store port and device information
log_file="stream_log.txt"

# Function to check if ffmpeg is running
check_ffmpeg() {
    local port="$1"
    local device="$2"
    # pgrep returns 0 if process is running, non-zero otherwise
    pgrep -f "ffmpeg.*-loglevel warning.*-video_size 480x320.*-i $device.*-f mpegts.*udp://192.168.100.10:$port"
    return $?
}

# Function to restart ffmpeg streams
restart_streams() {
    # Read ports and devices from log file
    while IFS= read -r line; do
        local port=$(echo "$line" | cut -d" " -f1)
        local device=$(echo "$line" | cut -d" " -f2)
        if ! check_ffmpeg "$port" "$device"; then
            echo "FFmpeg stream on port $port stopped. Restarting..."
            # Restart ffmpeg stream using startOne.sh
            ./startOne.sh "$port" "$device" &
        fi
    done < "$log_file"
}

# Main function
main() {
    while true; do
        # Ensure log file exists
        touch "$log_file"
        # Restart ffmpeg streams
        restart_streams
        sleep 3
    done
}

# Run the main function
main

