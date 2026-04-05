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

# Detect the actual non-root user (the one who ran sudo, or current user)
PI_USER="${SUDO_USER:-$(id -un)}"

# Update processor_host in drive.yaml.
# IP is passed as a command-line argument to Python (never interpolated into source)
# so there is no shell-injection risk regardless of what the user types.
python3 - "$PROCESSOR_IP" "$CONFIG" <<'PYEOF'
import re, sys

ip   = sys.argv[1]
path = sys.argv[2]

if not re.match(r'^[a-zA-Z0-9.\-]+$', ip):
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
SSH_DIR="/home/${PI_USER}/.ssh"
sudo mkdir -p "${SSH_DIR}"
sudo chown "${PI_USER}:${PI_USER}" "${SSH_DIR}"
sudo chmod 700 "${SSH_DIR}"

SSH_KEY="${SSH_DIR}/id_rsa"
if [[ ! -f "${SSH_KEY}" ]]; then
    sudo -u "${PI_USER}" ssh-keygen -t ed25519 -f "${SSH_KEY}" -N ""
    echo "SSH key generated (${SSH_KEY})"
else
    echo "SSH key already exists, skipping"
fi

# Copy key to Pi #2 (will prompt for Pi #2's password once)
echo "Copying SSH key to pi@${PROCESSOR_IP} — enter Pi #2's password when prompted:"
if ! sudo -u "${PI_USER}" ssh-copy-id -i "${SSH_KEY}.pub" "pi@${PROCESSOR_IP}"; then
    echo "ERROR: ssh-copy-id failed. Check that:"
    echo "  - Pi #2 is online and SSH is enabled"
    echo "  - Password authentication is not disabled on Pi #2"
    echo "  - The IP address ${PROCESSOR_IP} is correct"
    exit 1
fi

# Verify the connection works
echo "Testing SSH connection to Pi #2..."
if ! sudo -u "${PI_USER}" ssh "pi@${PROCESSOR_IP}" "echo 'SSH OK'"; then
    echo "ERROR: SSH test failed. The key was copied but the connection did not work."
    exit 1
fi
echo "Done. Pi #1 is configured to push clips to ${PROCESSOR_IP}."
