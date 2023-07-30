#!/bin/bash
# Top level install script
# Run from ./scripts

#Confirm actually being run as root
if [ "$(id -u)" -ne 0 ]; then
    echo 'This script must be run as root! Did you forget sudo?' >&2
    exit 1
fi

set -xeo

apt update
apt install -y cups hostapd dnsmasq python3-pip gcc libcups2-dev

#Make user pi part of the lpadmin group, so it can manage print jobs
usermod -a -G lpadmin pi

pip3 install -r requirements.txt

./setup_virtual_flash_drive.sh /piusb.bin /mnt/usb_share 2048

#Install the custom service
cp ../services/microscopeprinter.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable microscopeprinter.service
#Don't start it yet

#Remove WPA supplicant?
