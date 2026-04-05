#!/bin/bash
set -euo pipefail

# Configure Pi #1 (blink-drive) after first reboot.
# - Sets processor_host, processor_user, and ssh_key_path in drive.yaml
# - Generates an SSH key and copies it to Pi #2
#
# Usage: ./configure.sh <processor-ip> [processor-user]
#
# Example: ./configure.sh 192.168.1.201
#          ./configure.sh 192.168.1.201 jason   # if Pi #2's user is not 'pi'

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <processor-ip> [processor-user]"
    echo "  e.g. $0 192.168.1.201"
    echo "  e.g. $0 192.168.1.201 jason   # if Pi #2's username is not 'pi'"
    exit 1
fi

PROCESSOR_IP="$1"
PROCESSOR_USER="${2:-pi}"
CONFIG="/opt/blink-lens/configs/drive.yaml"

# Detect the actual non-root user (the one who ran sudo, or current user)
PI_USER="${SUDO_USER:-$(id -un)}"

# Update processor_host, processor_user, and ssh_key_path in drive.yaml.
# All values are passed as command-line arguments to Python (never interpolated
# into source) so there is no shell-injection risk regardless of input.
SSH_KEY="/home/${PI_USER}/.ssh/id_ed25519"

python3 - "$PROCESSOR_IP" "$PROCESSOR_USER" "$SSH_KEY" "$CONFIG" <<'PYEOF'
import re, sys

ip           = sys.argv[1]
proc_user    = sys.argv[2]
ssh_key_path = sys.argv[3]
path         = sys.argv[4]

if not re.match(r'^[a-zA-Z0-9.\-]+$', ip):
    print(f"ERROR: Refusing to write unsafe processor IP: {ip!r}", file=sys.stderr)
    sys.exit(1)

if not re.match(r'^[a-zA-Z0-9_\-]+$', proc_user):
    print(f"ERROR: Refusing to write unsafe processor username: {proc_user!r}", file=sys.stderr)
    sys.exit(1)

try:
    lines = open(path).readlines()
except FileNotFoundError:
    print(f"ERROR: Config file not found: {path}", file=sys.stderr)
    sys.exit(1)

def replace_value(lines, key, value):
    updated = []
    found = False
    for line in lines:
        if re.match(rf'\s*{re.escape(key)}:', line):
            comment_match = re.search(r'([ \t]*#.*)$', line)
            trailing = comment_match.group(1) if comment_match else ""
            updated.append(f'{key}: "{value}"{trailing}\n')
            found = True
        else:
            updated.append(line)
    return updated, found

lines, found = replace_value(lines, "processor_host", ip)
if not found:
    print(f"ERROR: 'processor_host' key not found in {path}", file=sys.stderr)
    sys.exit(1)

lines, _ = replace_value(lines, "processor_user", proc_user)
lines, _ = replace_value(lines, "ssh_key_path", ssh_key_path)

open(path, 'w').writelines(lines)
PYEOF

echo "Updated drive.yaml:"
echo "  processor_host: ${PROCESSOR_IP}"
echo "  processor_user: ${PROCESSOR_USER}"
echo "  ssh_key_path:   ${SSH_KEY}"

# Generate SSH key if not already present
SSH_DIR="/home/${PI_USER}/.ssh"
sudo mkdir -p "${SSH_DIR}"
sudo chown "${PI_USER}:${PI_USER}" "${SSH_DIR}"
sudo chmod 700 "${SSH_DIR}"

if [[ ! -f "${SSH_KEY}" ]]; then
    sudo -u "${PI_USER}" ssh-keygen -t ed25519 -f "${SSH_KEY}" -N ""
    echo "SSH key generated (${SSH_KEY})"
else
    echo "SSH key already exists (${SSH_KEY}), skipping generation"
fi

# Copy key to Pi #2 (will prompt for Pi #2's password once)
echo ""
echo "Copying SSH key to ${PROCESSOR_USER}@${PROCESSOR_IP}"
echo "Enter Pi #2's password when prompted:"
if ! sudo -u "${PI_USER}" ssh-copy-id -i "${SSH_KEY}.pub" "${PROCESSOR_USER}@${PROCESSOR_IP}"; then
    echo ""
    echo "ERROR: ssh-copy-id failed. Check that:"
    echo "  - Pi #2 is online and SSH is enabled (sudo systemctl status ssh)"
    echo "  - Password authentication is not disabled on Pi #2"
    echo "  - The IP address ${PROCESSOR_IP} is correct"
    echo "  - The username '${PROCESSOR_USER}' exists on Pi #2"
    exit 1
fi

# Verify the connection works with the key (no password)
echo "Testing SSH connection to Pi #2..."
if ! sudo -u "${PI_USER}" ssh "${PROCESSOR_USER}@${PROCESSOR_IP}" "echo 'SSH OK'"; then
    echo ""
    echo "ERROR: SSH test failed. The key was copied but the connection did not work."
    echo "Try running manually: ssh ${PROCESSOR_USER}@${PROCESSOR_IP}"
    exit 1
fi

echo ""
echo "Done. Pi #1 is configured to push clips to ${PROCESSOR_USER}@${PROCESSOR_IP}."
echo "Next step: sudo blink-drive start"
