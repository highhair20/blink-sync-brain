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

# Update processor_host in drive.yaml (via Python to avoid sed injection risks
# and to preserve any trailing inline comments on the line)
python3 - <<PYEOF
import re, sys

path = "$CONFIG"
ip   = "$PROCESSOR_IP"

if not re.match(r'^[a-zA-Z0-9.\-]+\$', ip):
    print(f"ERROR: Refusing to write unsafe processor IP: {ip!r}", file=sys.stderr)
    sys.exit(1)

try:
    lines = open(path).readlines()
except FileNotFoundError:
    print(f"ERROR: Config file not found: {path}", file=sys.stderr)
    sys.exit(1)

updated = []
found = False
for line in lines:
    if re.match(r'\s*processor_host:', line):
        # Preserve any trailing inline comment (e.g.  # Pi #2 IP address)
        comment_match = re.search(r'([ \t]*#.*)$', line)
        trailing = comment_match.group(1) if comment_match else ""
        updated.append(f'processor_host: "{ip}"{trailing}\n')
        found = True
    else:
        updated.append(line)

if not found:
    print(f"ERROR: 'processor_host' key not found in {path}", file=sys.stderr)
    sys.exit(1)

open(path, 'w').writelines(updated)
PYEOF
echo "Set processor_host to ${PROCESSOR_IP} in ${CONFIG}"

# Generate SSH key if not already present
sudo mkdir -p /home/pi/.ssh && sudo chown pi:pi /home/pi/.ssh && sudo chmod 700 /home/pi/.ssh
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
