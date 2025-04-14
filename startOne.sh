#!/bin/bash

# You have to pass in a port number as the first argument.

ip="192.168.100.10"

video_res="-video_size 480x320"

extra_flags="-f video4linux2"
#extra_flags="-loglevel warning -f video4linux2 -framerate 30"

#input_flags="-vf eq=brightness=-0.2:contrast=0.6,drawtext=text=%{gmtime\\\\:%X.%3N}:fontsize=20:fontcolor=red -vcodec libvpx -cpu-used 5 -deadline 1 -g 10 -error-resilient 1 -auto-alt-ref 1"
#input_flags="-vf eq=brightness=-0.2:contrast=0.6 -vcodec libvpx -cpu-used 5 -deadline 1 -g 10 -error-resilient 1 -auto-alt-ref 1"
#input_flags="-vf eq=brightness=-0.2:contrast=0.6"
input_flags="-vf eq=brightness=-0.2:contrast=0.6 -c:v libx264 -preset ultrafast -tune zerolatency"
#input_flags='-filter:v eq=brightness=-0.2:contrast=0.6,drawtext=text=%{gmtime\\:%X}:fontsize=32:fontcolor=red -c:v libvpx -cpu-used 5 -deadline 1 -g 5 -error-resilient 1 -auto-alt-ref 1'
#output_flags="-b:v 512k -maxrate 512k"
output_flags="-b:v 256k -maxrate 256k"
# -v 0"

# This loops through all but the first argument (the port).
for device in "${@:2}" ; do
  ffmpeg $extra_flags $video_res -i "$device" $input_flags -f mpegts $output_flags udp://$ip:$1
  # ffmpeg $extra_flags $video_res -i "$device" $input_flags -f rtp $output_flags rtp://$ip:$1?pkt_size=1200
done
