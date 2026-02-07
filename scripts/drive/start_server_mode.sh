#!/bin/bash
set -euo pipefail

DRIVE_IMG="/var/blink_storage/virtual_drive.img"
MOUNT_POINT="/mnt/blink_drive"

echo "Switching to Server Mode for Blink Sync Brain..."

# Unload the kernel module to stop USB drive emulation
modprobe -r g_mass_storage

# Mount the partition (not the raw image) so Pi #2 can pull clips via rsync/SSH
mkdir -p "${MOUNT_POINT}"
losetup -fP "${DRIVE_IMG}"
LOOP=$(losetup -j "${DRIVE_IMG}" | cut -d: -f1)
mount "${LOOP}p1" "${MOUNT_POINT}"

echo "Server Mode is LIVE. Drive mounted at ${MOUNT_POINT}."