#!/bin/bash
set -euo pipefail

# Configure Pi #1 (blink-drive) after first reboot.
# - Writes PROCESSOR_HOST, PROCESSOR_USER, and SSH_KEY_PATH to /etc/blink-lens/env
# - Generates an SSH key and copies it to Pi #2
#
# Usage: sudo ./configure.sh <processor-ip> [processor-user]
#
# Example: sudo ./configure.sh 192.168.1.201
#          sudo ./configure.sh 192.168.1.201 jason   # if Pi #2's user is not 'pi'

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run with sudo."
    echo "  Run: sudo $0 $*"
    exit 1
fi

if [[ $# -lt 1 ]]; then
    echo "Usage: sudo $0 <processor-ip> [processor-user]"
    echo "  e.g. sudo $0 192.168.1.201"
    echo "  e.g. sudo $0 192.168.1.201 jason   # if Pi #2's username is not 'pi'"
    exit 1
fi

PROCESSOR_IP="$1"
PROCESSOR_USER="${2:-pi}"

# Detect the actual non-root user (the one who ran sudo, or current user)
PI_USER="${SUDO_USER:-$(id -un)}"
SSH_KEY="/home/${PI_USER}/.ssh/id_ed25519"
ENV_FILE="/etc/blink-lens/env"

# Validate inputs before writing anywhere
python3 - "$PROCESSOR_IP" "$PROCESSOR_USER" <<'PYEOF'
import re, sys

ip        = sys.argv[1]
proc_user = sys.argv[2]

if not re.match(r'^[a-zA-Z0-9.\-]+$', ip):
    print(f"ERROR: Refusing to use unsafe processor IP: {ip!r}", file=sys.stderr)
    sys.exit(1)

if not re.match(r'^[a-zA-Z0-9_\-]+$', proc_user):
    print(f"ERROR: Refusing to use unsafe processor username: {proc_user!r}", file=sys.stderr)
    sys.exit(1)
PYEOF

# Write configuration to /etc/blink-lens/env (not tracked by git)
mkdir -p /etc/blink-lens
cat > "${ENV_FILE}" <<EOF
PROCESSOR_HOST=${PROCESSOR_IP}
PROCESSOR_USER=${PROCESSOR_USER}
SSH_KEY_PATH=${SSH_KEY}
EOF
chmod 600 "${ENV_FILE}"

echo "Configuration written to ${ENV_FILE}:"
echo "  PROCESSOR_HOST=${PROCESSOR_IP}"
echo "  PROCESSOR_USER=${PROCESSOR_USER}"
echo "  SSH_KEY_PATH=${SSH_KEY}"

# Generate SSH key if not already present
SSH_DIR="/home/${PI_USER}/.ssh"
mkdir -p "${SSH_DIR}"
chown "${PI_USER}:${PI_USER}" "${SSH_DIR}"
chmod 700 "${SSH_DIR}"

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
if ! sudo -u "${PI_USER}" ssh -i "${SSH_KEY}" -o IdentitiesOnly=yes "${PROCESSOR_USER}@${PROCESSOR_IP}" "echo 'SSH OK'"; then
    echo ""
    echo "ERROR: SSH test failed. The key was copied but the connection did not work."
    echo "Try running manually: ssh ${PROCESSOR_USER}@${PROCESSOR_IP}"
    exit 1
fi

echo ""
echo "Done. Pi #1 is configured to push clips to ${PROCESSOR_USER}@${PROCESSOR_IP}."
echo "Next step:"
echo "  If install.sh has not been run yet: sudo /opt/blink-lens/scripts/drive/install.sh"
echo "  If install.sh is already done:      sudo systemctl restart blink-watcher"
