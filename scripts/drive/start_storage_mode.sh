#!/bin/bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run with sudo."
    echo "  Run: sudo $0"
    exit 1
fi

DRIVE_IMG="/var/blink_storage/virtual_drive.img"
CONFIG="/opt/blink-lens/configs/drive.yaml"

# Read shadow_mount_point from drive.yaml so cleanup targets the configured path.
MOUNT_POINT=$(python3 -c "
import yaml, sys
try:
    d = yaml.safe_load(open('${CONFIG}'))
    print(d.get('watcher', {}).get('shadow_mount_point', '/mnt/blink_shadow'))
except Exception:
    print('/mnt/blink_shadow')
" 2>/dev/null || echo "/mnt/blink_shadow")

echo "Switching to Storage Mode for Blink..."

# Pre-flight: verify the drive image exists and is at least 1 MB
# (guards against a partially-created or zero-byte image that would silently
# confuse the Blink Sync Module without producing a clear error)
if [[ ! -f "${DRIVE_IMG}" ]]; then
    echo "ERROR: Virtual drive image not found: ${DRIVE_IMG}"
    echo "  Run: sudo /opt/blink-lens/scripts/drive/install.sh"
    exit 1
fi
IMAGE_SIZE=$(stat -c%s "${DRIVE_IMG}" 2>/dev/null || echo 0)
if [[ "${IMAGE_SIZE}" -lt 1048576 ]]; then
    echo "ERROR: Virtual drive image is too small (${IMAGE_SIZE} bytes) — it may be corrupted."
    echo "  Delete it and run: sudo /opt/blink-lens/scripts/drive/install.sh"
    exit 1
fi

# Ensure the shadow mount is detached before starting the gadget
umount "${MOUNT_POINT}" &>/dev/null || true

# Detach any loop devices associated with the image
for loop in $(losetup -j "${DRIVE_IMG}" | cut -d: -f1); do
    losetup -d "${loop}" &>/dev/null || true
done

# Unload the module first in case it was loaded without parameters
modprobe -r g_mass_storage &>/dev/null || true

# Load the kernel module to start USB drive emulation
modprobe g_mass_storage file="${DRIVE_IMG}" removable=1 stall=0

echo "Storage Mode is LIVE."
