#!/bin/bash

# Ensure stopped_stream.txt exists and is writable
stopped_log="stopped_stream.txt"
touch "$stopped_log"

# Ensure stopped_stream.txt has the same number of lines as stream_log.txt
while IFS= read -r line; do
    echo "" >> "$stopped_log"
done < stream_log.txt

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <camera_index>"
    exit 1
fi

camera_index="$1"

# Read the specified line (camera_index) from stream_log.txt
line=$(sed -n "$((camera_index + 1))p" stream_log.txt)

# Check if the line is empty or does not exist
if [ -z "$line" ] || [ "$line" = " " ]; then
    echo "No entry found for camera index $camera_index"
    exit 1
fi

port=$(echo "$line" | cut -d ' ' -f 1)
device=$(echo "$line" | cut -d ' ' -f 2)

# Replace the line in stream_log.txt with a blank line
sed -i "$((camera_index + 1))s/.*/ /" stream_log.txt

# Replace the corresponding line in stopped_stream.txt with the original line
sed -i "$((camera_index + 1))s/.*/$line/" "$stopped_log"

# Kill the process using fuser
fuser -k "${port}/udp"

echo "Stopped streaming for device: $device on port: $port"

exit 0
