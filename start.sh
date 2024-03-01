ip="192.168.100.10"
video_res="320x240"
extra_flags=" -loglevel warning"
encoding=""

ffmpeg $extra_flags -video_size $video_res -i /dev/video0 $encoding -f mpegts udp://$ip:1181 &
ffmpeg $extra_flags -video_size $video_res -i /dev/video2 $encoding -f mpegts udp://$ip:1182 &
ffmpeg $extra_flags -video_size $video_res -i /dev/video4 $encoding -f mpegts udp://$ip:1183 &
ffmpeg $extra_flags -video_size $video_res -i /dev/video6 $encoding -f mpegts udp://$ip:1184 &

date
echo "streams running as background process, enter 'sudo killall ffmpeg' to stop them"
