#!/bin/bash

# Top level install script
#run with sudo
BINARY_FILE=/piusb.bin
MOUNT_DIR=/mnt/usb_share

apt install -y cups hostapd dnsmasq python3-pip

#Make user pi part of the lpadmin group, so it can manage print jobs
usermod -a -G lpadmin pi

## TODO: Install printer drivers???

pip install -r requirements.txt

## https://magpi.raspberrypi.com/articles/pi-zero-w-smart-usb-flash-drive
#Enable USB driver. This will keep appending if rerun..
echo "dtoverlay=dwc2" >>/boot/config.txt
echo "dwc2" >>/etc/modules

#Create a 2GB file to act as storage medium that will emulate "drive"
dd bs=1M if=/dev/zero of=$BINARY_FILE count=2048

#Format it as FAT32
mkdosfs $BINARY_FILE -F 32 -I

# create a folder on which we can mount the file system (-p to allow existing)
mkdir -p $MOUNT_DIR

# Add this mount point to fstab
echo "$BINARY_FILE $MOUNT_DIR vfat users,umask=000 0 2" >>/etc/fstab

#Install the custom service
cp ../services/microscopeprinter.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable microscopeprinter.service
#Don't start it yet

#Remove WPA supplicant?
