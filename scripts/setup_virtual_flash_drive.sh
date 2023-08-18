#!/bin/bash
#
# This script will do the necessary configuration to setup Pi as a USB device
# (i.e. flash drive).
# https://magpi.raspberrypi.com/articles/pi-zero-w-smart-usb-flash-drive
#
if [ $# -lt 2 ]; then
    echo "Usage: $0 BINARY_FILE MNT_LOCATION SIZE_MB"
    exit 1
fi

BINARY_FILE=$1 #This is the binary blob that will be used as the virtual flash drive.
MOUNT_DIR=$2   #This is where the virtual flash drive will get mounted in Pi filesystem
SIZE_MB=$3     #This is the size of the virtual flash drive in MB. Powers of 2 suggested.

if test -f "$BINARY_FILE"; then
    echo "$BINARY_FILE exists, skipping."
    exit 0
fi

#Enable USB driver. This will keep appending if rerun..
echo "dtoverlay=dwc2" >>/boot/config.txt
echo "dwc2" >>/etc/modules

#Create a file to act as storage medium that will emulate "drive"
dd bs=1M if=/dev/zero of=$BINARY_FILE count=$SIZE_MB

#Format it as FAT32
mkdosfs $BINARY_FILE -F 32 -I

# create a folder on which we can mount the file system (-p to allow existing)
mkdir -p $MOUNT_DIR

# Add this mount point to fstab
echo "$BINARY_FILE $MOUNT_DIR vfat users,umask=000 0 2" >>/etc/fstab
