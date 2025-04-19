# RPi-Camera

Script to stream USB cameras from Raspberry PI 5 to Basestation with RoveComm control.

## Setup

1. Download and install Raspberry Pi OS Lite (64 bit).

   - <https://www.raspberrypi.com/software/operating-systems/>

2. Configure the system:

   - `$ sudo raspi-config`
   - Select "System Options > Boot / Auto Login > Console Autologin".
   - Select "System Options > Wireless LAN" and connect to a network.

3. Install software:

   - `$ sudo apt update`
   - `$ sudo apt upgrade`
   - `$ sudo apt install ffmpeg v4l-utils vsftpd fswebcam`

4. Configure `server.py`:

   - Make `server.py` executable.
   - Edit `ports` and `manifest.device` in `config.toml`.

5. `server.py` should be started on boot, after network has been established. Setup a systemd service:

   - `$ sudo systemctl edit --force --full cameras.service`
   - Copy the contents of cameras.service into the text editor.
   - Save and close.
   - `$ sudo systemctl enable cameras.service`

6. Set a static IP:

   - In `sudo nmtui`, disable `wlan0` interface and configure and set a static IP for `eth0` that matches the RoveComm manifest.
   - OR
   - `$ sudo nano /etc/network/interfaces`
   - Copy the contents of interfaces to the end.
   - Change the IP accordingly (see "Port Info").
   - Save and close.

7. Check operation:

   - Start with `sudo systemctl start cameras`.
   - Monitor status with `sudo systemctl status cameras`.
   - Follow logs with `sudo journalctl -fu cameras`.
   - Monitor FFmpeg subprocess and resource utilization `htop`.

## Port Info

The Basestation IP (`config.toml` `ip`) should be `192.168.100.10`.

The Raspberry Pi IP/port combos should be:

```lang-none
192.168.4.100:8100
192.168.4.100:8200
192.168.4.100:8300
192.168.4.100:8400
192.168.4.101:8500
192.168.4.101:8600
192.168.4.101:8700
192.168.4.101:8800
```
