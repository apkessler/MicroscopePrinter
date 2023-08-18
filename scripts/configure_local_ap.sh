#!/bin/bash

#This script should configure the local WiFi AP.
# Andrew Kessler 2023

#Confirm actually being run as root
if [ "$(id -u)" -ne 0 ]; then
    echo 'This script must be run as root! Did you forget sudo?' >&2
    exit 1
fi

echo "Starting AP provisioning script."

HOSTNAME=$(hostname)
DEFAULT_CHN=7

#Local DHCP settings
#Script will configure DHCP to assign IPs between
#192.168.$SUBNET.$MIN_ADDR thru 192.168.$SUBNET.$MAX_ADDR
SUBNET=4
MIN_ADDR=2
MAX_ADDR=20

DHCPCD_CONF_FILE=/etc/dhcpcd.conf
DNSMASQ_CONF_FILE=/etc/dnsmasq.conf
HOSTAPD_CONF_FILE=/etc/hostapd/hostapd.conf

#From https://www.raspberrypi.com/documentation/computers/configuration.html#software-install
#In order to work as an access point, the  Pi needs to have the hostapd
#access point software package installed and in order to provide network
#management services (DNS, DHCP) to wireless clients, the  Pi needs to have the
#dnsmasq software package installed:
apt install -y hostapd dnsmasq

# #Enable the wireless access point service and set it to start when your Raspberry Pi boots:
systemctl unmask hostapd
systemctl enable hostapd

systemctl unmask dnsmasq
systemctl enable dnsmasq

echo "Please enter name (SSID) you want for local WiFi (default will be $HOSTNAME): "
read ssid
ssid=${ssid:-$HOSTNAME}
echo "Ok, the SSID will be $ssid."

echo "Please enter password you want for local WiFi (default will be $HOSTNAME): "
read password
password=${password:-$HOSTNAME}
echo "OK, the password will be $password."

echo "Please enter the channel for local WiFi (default will be $DEFAULT_CHN). "
echo "If you're not sure, just leave blank to use the default."
read chn
chn=${chn:-$DEFAULT_CHN}
echo "OK, the SSID channel will be $chn."

## Setup the Network Router

# Define the Wireless Interface IP Configuration
DHCPCD_CONF_BACKUP_FILE=$DHCPCD_CONF_FILE.orig
if test -f "$DHCPCD_CONF_BACKUP_FILE"; then
    echo "$DHCPCD_CONF_BACKUP_FILE exists, skipping."
else
    echo "No backup file. Backing up."
    cp $DHCPCD_CONF_FILE $DHCPCD_CONF_BACKUP_FILE
fi

#Now, append new stuff to original (backup file)
cp $DHCPCD_CONF_BACKUP_FILE $DHCPCD_CONF_FILE #Restore original
#Add the blob below to end of dhcpcd.conf - this defines the static IP for Pi on
#its own network
cat <<EOF >>$DHCPCD_CONF_FILE
interface wlan0
    static ip_address=192.168.$SUBNET.1/24
    nohook wpa_supplicant
EOF

#Configure the DHCP and DNS services for the wireless network
DNSMASQ_CONF_BACKUP_FILE=$DNSMASQ_CONF_FILE.orig
if test -f "$DNSMASQ_CONF_BACKUP_FILE"; then
    echo "$DNSMASQ_CONF_BACKUP_FILE exists, skipping."
else
    echo "No backup file. Backing up."
    cp $DNSMASQ_CONF_FILE $DNSMASQ_CONF_BACKUP_FILE
fi

# Create a new dnsmasq.conf
#The  Pi will deliver IP addresses between 192.168.$SUBNET.$MIN_ADDR and
# 192.168.$SUBNET.$MAX_ADDR, with a lease time of 24 hours, to wireless DHCP
# clients. You should be able to reach the Raspberry Pi under the name gw.wlan
# from wireless clients.
cat <<EOF >$DNSMASQ_CONF_FILE
interface=wlan0 # Listening interface
dhcp-range=192.168.$SUBNET.$MIN_ADDR,192.168.$SUBNET.$MAX_ADDR,255.255.255.0,24h
                # Pool of IP addresses served via DHCP
domain=wlan     # Local wireless DNS domain
address=/gw.wlan/192.168.$SUBNET.1
                # Alias for this router
EOF

## Configure the AP Software
bash generate_hostapd.sh $ssid $password $chn >$HOSTAPD_CONF_FILE

#Need this?
#Finally, install netfilter-persistent and its plugin iptables-persistent. This utility helps by saving firewall rules and restoring them when the Raspberry Pi boots:
#sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent

echo "On next reboot, the Pi will be broadcastings its own WiFi with SSID=$ssid."
