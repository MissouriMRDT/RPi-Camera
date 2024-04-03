#!/bin/bash

# You have to pass in a port number as the first argument.

ip="192.168.100.10"
video_res="320x240"
extra_flags=" -loglevel warning"
encoding=""

# This loops through all but the first argument (the port).
for device in "${@:2}" ; do
#   sleep 1 && echo "starting" $device $1 && sleep 8
  ffmpeg $extra_flags -video_size $video_res -i "$device" $encoding -f mpegts udp://$ip:$1
done
