ip="192.168.100.10"
ports=("1181" "1182" "1183", "1184")
video_res="320x240"
extra_flags=" -loglevel warning"
encoding=""

ffmpeg $extra_flags -video_size $video_res -i /dev/video0 $encoding -f mpegts udp://$ip:${ports[0]} &
ffmpeg $extra_flags -video_size $video_res -i /dev/video2 $encoding -f mpegts udp://$ip:${ports[1]} &
ffmpeg $extra_flags -video_size $video_res -i /dev/video4 $encoding -f mpegts udp://$ip:${ports[2]} &
ffmpeg $extra_flags -video_size $video_res -i /dev/video6 $encoding -f mpegts udp://$ip:${ports[3]} &

echo "streams running as background process, enter 'sudo killall ffmpeg' to stop them"
