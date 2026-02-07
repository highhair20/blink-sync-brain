#!/bin/bash
set -euo pipefail

DRIVE_IMG="/var/blink_storage/virtual_drive.img"
MOUNT_POINT="/mnt/blink_drive"

echo "Switching to Storage Mode for Blink..."

# Ensure the drive is unmounted before starting the gadget
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