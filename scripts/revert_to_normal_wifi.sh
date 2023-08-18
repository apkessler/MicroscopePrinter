#!/bin/bash
# This script will put the Pi back into a mode where it can connect to a WiFi
# network as a normal client (after a reboot).

#Confirm actually being run as root
if [ "$(id -u)" -ne 0 ]; then
    echo 'This script must be run as root! Did you forget sudo?' >&2
    exit 1
fi

echo "Please enter name (SSID) of WiFi network you want to connect to: "
read ssid
echo "Ok, will look for SSID $ssid."

echo "Please enter password for WiFi network ($ssid): "
read password
echo "OK, the password will be $password."

systemctl disable hostapd dnsmasq
cp /etc/dhcpcd.conf.orig /etc/dhcpcd.conf

mv /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.orig
#Create a wpa_supplicant.conf...
cat <<EOF >>/etc/wpa_supplicant/wpa_supplicant.conf
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
 ssid="$ssid"
 scan_ssid=1
 psk="$password"
 key_mgmt=WPA-PSK
}
EOF

echo "Reboot for changes to take effect."
