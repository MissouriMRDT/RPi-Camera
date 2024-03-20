# RPi-Camera

Script to stream cameras from the Raspberry Pi's.

# Setup

1. Download and Install Raspberry Pi OS Lite (32 bit).

   - https://www.raspberrypi.com/software/operating-systems/

2. Do some config:

   - `$ sudo raspi-config`
   - Select "System Options > Boot / Auto Login > Console Autologin"
   - Select "System Options > Wireless LAN > (go throught the setup process)"

3. Install ffmpeg:

   - `$ sudo apt update`
   - `$ sudo apt upgrade`
   - `$ sudo apt install ffmpeg`

4. Disable wifi (I think if you do this it breaks? But it should be connecting over ethernet? Testing is needed...):

   - `$ sudo nano /boot/firmware/config.txt`
   - Add the line: `dtoverlay=disable-wifi`

5. Copy start.sh to `/home/pi/start.sh`.

   - Make sure it is executable!

6. start.sh needs to run on boot, after network has been established. For this, setup a systemd service:

   - `$ sudo systemctl edit --force --full cameras.service`
   - Copy the contents of cameras.service into the text editor.
   - Save and close.
   - `$ sudo systemctl enable cameras.service`

7. Set a static IP:

   - `$ sudo nano /etc/network/interfaces`
   - Copy the contents of interfaces to the end.
   - Save and close.

7. Check to make sure it works:

   - `$ sudo reboot now`
   - `$ htop`
   - You should see ffmpeg processes!
   - "q" to quit.
