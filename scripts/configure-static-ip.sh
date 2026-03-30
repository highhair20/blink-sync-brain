#!/bin/bash
set -euo pipefail

# Configure a static IP address using NetworkManager.
# Looks up the active Wi-Fi connection automatically.
#
# Usage: sudo ./configure-static-ip.sh <ip-address>
#
# Examples:
#   sudo ./configure-static-ip.sh 192.168.1.200   # Pi #1 (blink-drive)
#   sudo ./configure-static-ip.sh 192.168.1.201   # Pi #2 (blink-processor)
#
# Note: Your SSH session will drop when the connection restarts.
#       Reconnect using the static IP you set.

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ip-address>"
    echo "  e.g. $0 192.168.1.200"
    exit 1
fi

IP="$1"

# Validate IP format
if ! [[ "$IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: '$IP' is not a valid IP address"
    exit 1
fi

# Find the active connection name
CONN=$(nmcli -t -f NAME,TYPE,STATE connection show --active \
    | grep ':802-11-wireless:activated' \
    | cut -d: -f1 \
    | head -1)

if [[ -z "$CONN" ]]; then
    echo "Error: no active Wi-Fi connection found"
    nmcli connection show --active
    exit 1
fi

# Derive gateway and DNS from the IP (assume /24, gateway = .1)
GATEWAY=$(echo "$IP" | cut -d. -f1-3).1

echo "Connection : $CONN"
echo "IP address : ${IP}/24"
echo "Gateway    : $GATEWAY"
echo "DNS        : $GATEWAY, 8.8.8.8"
echo

nmcli connection modify "$CONN" ipv4.addresses "${IP}/24"
nmcli connection modify "$CONN" ipv4.gateway "$GATEWAY"
nmcli connection modify "$CONN" ipv4.dns "$GATEWAY,8.8.8.8"
nmcli connection modify "$CONN" ipv4.method "manual"

echo "Applying — SSH session will drop. Reconnect to $IP"
nmcli connection down "$CONN" && nmcli connection up "$CONN"
