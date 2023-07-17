#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 SSID PASSWORD"
    exit 1
fi

SSID_NAME=$1
SSID_PASSWORD=$2

cat <<EOF
country_code=US
interface=wlan0
ssid=$1
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$2
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
