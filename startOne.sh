#!/bin/bash

# You have to pass in a port number as the first argument.

ip="192.168.100.10"

video_res="-video_size 320x240"
#video_res=""

extra_flags="-loglevel warning"
#extra_flags=""

encoding=""

# This loops through all but the first argument (the port).
for device in "${@:2}" ; do
  ffmpeg $extra_flags $video_res -i "$device" $encoding -f mpegts udp://$ip:$1
done
