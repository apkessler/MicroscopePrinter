#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 BINARY_FILE MNT_LOCATION SIZE_MB"
    exit 1
fi

BINARY_FILE=$1
MOUNT_DIR=$2
SIZE_MB=$3

if test -f "$BINARY_FILE"; then
    echo "$BINARY_FILE exists, skipping."
    exit 0
fi

## https://magpi.raspberrypi.com/articles/pi-zero-w-smart-usb-flash-drive
#Enable USB driver. This will keep appending if rerun..
echo "dtoverlay=dwc2" >>/boot/config.txt
echo "dwc2" >>/etc/modules

#Create a 2GB file to act as storage medium that will emulate "drive"
dd bs=1M if=/dev/zero of=$BINARY_FILE count=$SIZE_MB

#Format it as FAT32
mkdosfs $BINARY_FILE -F 32 -I

# create a folder on which we can mount the file system (-p to allow existing)
mkdir -p $MOUNT_DIR

# Add this mount point to fstab
echo "$BINARY_FILE $MOUNT_DIR vfat users,umask=000 0 2" >>/etc/fstab
