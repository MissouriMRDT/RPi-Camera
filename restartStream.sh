#!/bin/bash

# File to store port and device information
log_file="stream_log.txt"

# Function to check if ffmpeg is running
check_ffmpeg() {
    local port="$1"
    local device="$2"
    # pgrep returns 0 if process is running, non-zero otherwise
    pgrep -f "ffmpeg.*-loglevel warning.*-video_size 320x240.*-i $device.*-f mpegts.*udp://192.168.100.10:$port"
    return $?
}

# Main function to restart ffmpeg streams
restart_streams() {
    local ip="192.168.100.10"
    local video_res="-video_size 320x240"
    local extra_flags="-loglevel warning"
    local input_flags="-vf eq=brightness=-0.2:contrast=0.6"
    local output_flags="-b:v 128k -maxrate 128k -v 0"

    # Read ports and devices from log file
    while IFS= read -r line; do
        local port=$(echo "$line" | cut -d" " -f1)
        local device=$(echo "$line" | cut -d" " -f2)
        if ! check_ffmpeg "$port" "$device"; then
            echo "FFmpeg stream on port $port stopped. Restarting..."
            # Restart ffmpeg stream
            ffmpeg $extra_flags $video_res -i "$device" $input_flags -f mpegts $output_flags "udp://$ip:$port" &
        fi
    done < "$log_file"  # Ensure to read from the log file
}

# Main function
main() {
    while true; do
        # Ensure log file exists
        touch "$log_file"
        # Restart ffmpeg streams
        restart_streams
        sleep 1
    done
}

# Run the main function
main

