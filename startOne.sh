#!/bin/bash

# You have to pass in a port number as the first argument.

ip="192.168.100.10"

video_res="-video_size 480x320"
#video_res=""

extra_flags="-loglevel warning"
#extra_flags=""

input_flags="-vf eq=brightness=-0.2:contrast=0.6"
output_flags="-b:v 512k -maxrate 524k -v 0"

# This loops through all but the first argument (the port).
for device in "${@:2}" ; do
  ffmpeg $extra_flags $video_res -i "$device" $input_flags -f mpegts $output_flags udp://$ip:$1
done
