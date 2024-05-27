#!/bin/bash

declare -a argumentList
argumentList=()
declare -a portList
portList=("1185" "1186" "1187" "1188")

declare -a PIDS
export PIDS
PIDS=()

# Log file to store port and device information
log_file="stream_log.txt"

# Ensure log file exists and is writable
touch "$log_file"

> "$log_file"

python listenForScreenshots.py &
python listenForStreamToggle.py &


# We only want to stream the usb devices. This flag is set if the previous
# non-tabbed line started with "USB"
isUSB=true

# The printf is to ensure at least two trailing newlines.
# This is important to the loop.
counter=0
printf "$(v4l2-ctl --list-devices)\n\n" | while IFS="" ; read -r line ; do
  if [[ "$line" = $'\t'* ]]; then
    if [ $isUSB = true ]; then
      # xargs trims the tab off the front of the line
      argumentList+=($(echo "$line" | xargs))
    fi
  else
    if [ -n "$argumentList" ]; then
      if [ $isUSB = true ]; then
        # Start stream and log port and device
        port="${portList[$counter]}"
        device="${argumentList[0]}"
        bash startOne.sh "$port" "${argumentList[@]}" &
        PIDS[$counter]="$!"
        echo "$port $device" >> "$log_file"  # Append to the log file
        ((counter+=1))
      fi
      argumentList=()
    fi

    # I know, there should be a way of setting a variable to the output of a
    # boolean expression, but I don't think there is...
    if [[ "$line" =~ "(usb" ]]; then
      isUSB=true
    else
      isUSB=false
    fi
  fi
done

# Call the monitoring script
./restartStream.sh
