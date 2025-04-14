#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <camera_index>"
    exit 1
fi

camera_index="$1"

# Read the specified line (camera_index) from stopped_stream.txt
line=$(sed -n "$((camera_index + 1))p" stopped_stream.txt)

# Check if the line is empty or does not exist
if [ -z "$line" ] || [ "$line" = " " ]; then
    echo "No entry found for camera index $camera_index in stopped_stream.txt"
    exit 1
fi

port=$(echo "$line" | cut -d ' ' -f 1)
device=$(echo "$line" | cut -d ' ' -f 2)

# Start the stream using startOne.sh
bash startOne.sh "$port" "$device" &

# Replace the line in stopped_stream.txt with a blank line
sed -i "$((camera_index + 1))s/.*/ /" stopped_stream.txt

# Append the port and device details to the correct line in stream_log.txt
sed -i "$((camera_index + 1))s#.*#$port $device#" stream_log.txt

echo "Started streaming for device: $device on port: $port"

exit 0

