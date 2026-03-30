#!/bin/bash
set -euo pipefail

# Configure Pi #1 (blink-drive) after first reboot.
# - Sets processor_host in drive.yaml
# - Generates an SSH key and copies it to Pi #2
#
# Usage: ./configure.sh <processor-ip>
#
# Example: ./configure.sh 192.168.1.201

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <processor-ip>"
    echo "  e.g. $0 192.168.1.201"
    exit 1
fi

PROCESSOR_IP="$1"
CONFIG="/opt/blink-lens/configs/drive.yaml"

# Update processor_host in drive.yaml
sed -i "s|processor_host:.*|processor_host: \"${PROCESSOR_IP}\"|" "$CONFIG"
echo "Set processor_host to ${PROCESSOR_IP} in ${CONFIG}"

# Generate SSH key if not already present
mkdir -p /home/pi/.ssh && chmod 700 /home/pi/.ssh
if [[ ! -f /home/pi/.ssh/id_rsa ]]; then
    ssh-keygen -t rsa -f /home/pi/.ssh/id_rsa -N ""
    echo "SSH key generated"
else
    echo "SSH key already exists, skipping"
fi

# Copy key to Pi #2 (will prompt for Pi #2's password)
echo "Copying SSH key to pi@${PROCESSOR_IP} — enter Pi #2's password when prompted:"
ssh-copy-id -i /home/pi/.ssh/id_rsa.pub "pi@${PROCESSOR_IP}"

# Verify
echo "Testing SSH connection to Pi #2..."
ssh "pi@${PROCESSOR_IP}" "echo 'SSH OK'"
echo "Done."
