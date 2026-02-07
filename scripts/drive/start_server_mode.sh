#!/bin/bash
set -euo pipefail

DRIVE_IMG="/var/blink_storage/virtual_drive.img"
MOUNT_POINT="/mnt/blink_drive"

echo "Switching to Server Mode for Blink Sync Brain..."

# Unload the kernel module to stop USB drive emulation
modprobe -r g_mass_storage

# Check if a loop device already exists for this image
LOOP=$(losetup -j "${DRIVE_IMG}" | cut -d: -f1 | head -n1)

if [[ -z "${LOOP}" ]]; then
    # Create new loop device with partition scanning
    losetup -fP "${DRIVE_IMG}"
    LOOP=$(losetup -j "${DRIVE_IMG}" | cut -d: -f1 | head -n1)
fi

# Wait for partition device to appear
PART="${LOOP}p1"
for i in {1..10}; do
    [[ -b "${PART}" ]] && break
    partprobe "${LOOP}" 2>/dev/null || true
    sleep 0.5
done

if [[ ! -b "${PART}" ]]; then
    echo "Error: Partition ${PART} not found"
    exit 1
fi

# Mount the partition
mkdir -p "${MOUNT_POINT}"
mount "${PART}" "${MOUNT_POINT}"

echo "Server Mode is LIVE. Drive mounted at ${MOUNT_POINT}."