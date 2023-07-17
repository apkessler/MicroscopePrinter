#!/bin/bash

#This script should install everything on the Pi.

#set -xeo

echo "Starting provisioning script."

HOSTNAME=$(hostname)

echo "Please enter name (SSID) you want for local WiFi (default will be $HOSTNAME): "
read ssid
ssid=${ssid:-$HOSTNAME}
echo "Ok, the SSID will be $ssid."

echo "Please enter password you want for local WiFi (default will be $HOSTNAME): "
read password
password=${password:-$HOSTNAME}
echo "OK, the password will be $password."

#Now, generate the hostapd config file
./generate_hostapd.sh $ssid $password >hostapd.conf

#TODO: Move it where it needs to go

#From https://www.raspberrypi.com/documentation/computers/configuration.html#software-install
#In order to work as an access point, the  Pi needs to have the hostapd
#access point software package installed and in order to provide network
#management services (DNS, DHCP) to wireless clients, the  Pi needs to have the
#dnsmasq software package installed:
sudo apt install -y hostapd dnsmasq

#Enable the wireless access point service and set it to start when your Raspberry Pi boots:
sudo systemctl unmask hostapd
sudo systemctl enable hostapd

#Need this?
#Finally, install netfilter-persistent and its plugin iptables-persistent. This utility helps by saving firewall rules and restoring them when the Raspberry Pi boots:
#sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
