# RPi-Camera

Script to stream cameras from the Raspberry Pi's.

# Setup

1. Download and Install Raspberry Pi OS Lite (32 bit).

   - https://www.raspberrypi.com/software/operating-systems/

2. Do some config:

   - `$ sudo raspi-config`
   - Select "System Options > Boot / Auto Login > Console Autologin"
   - Select "System Options > Wireless LAN > (go throught the setup process)"

3. Install software:

   - `$ sudo apt update`
   - `$ sudo apt upgrade`
   - `$ sudo apt install ffmpeg`
   - `$ sudo apt install v4l-utils`

4. Copy start.sh to `/home/pi/start.sh`.

   - Make sure it is executable!
   - Change the ports accordingly (see "Port Info").
   - You may also have to change the destination IP (see "Port Info").

5. start.sh needs to run on boot, after network has been established. For this, setup a systemd service:

   - `$ sudo systemctl edit --force --full cameras.service`
   - Copy the contents of cameras.service into the text editor.
   - Save and close.
   - `$ sudo systemctl enable cameras.service`

6. Set a static IP:

   - `$ sudo nano /etc/network/interfaces`
   - Copy the contents of interfaces to the end
   - Change the IP accordingly (see "Port Info").
   - Save and close.

7. Check to make sure it works:

   - `$ sudo reboot now`
   - `$ htop`
   - You should see ffmpeg processes!
   - "q" to quit.

# Port Info

The basestation IP should be `192.168.100.10`.

The Raspberry Pi IP/port combos should be:
```
192.168.4.100:1181
192.168.4.100:1182
192.168.4.100:1183
192.168.4.100:1184
192.168.4.101:1185
192.168.4.101:1186
192.168.4.101:1187
192.168.4.101:1188
```
