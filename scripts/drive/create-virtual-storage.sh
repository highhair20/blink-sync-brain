#!/bin/bash
set -euo pipefail

STORAGE_DIR="/var/blink_storage"
DRIVE_IMG="${STORAGE_DIR}/virtual_drive.img"
SIZE_MB=32768

echo "Creating virtual storage at ${DRIVE_IMG} (${SIZE_MB} MB)..."

mkdir -p "${STORAGE_DIR}"
chown pi:pi "${STORAGE_DIR}"
chmod 755 "${STORAGE_DIR}"

# Create the disk image
dd if=/dev/zero of="${DRIVE_IMG}" bs=1M count="${SIZE_MB}" status=progress

# Create partition table and FAT32 partition (required for Blink Sync Module)
parted "${DRIVE_IMG}" --script mklabel msdos
parted "${DRIVE_IMG}" --script mkpart primary fat32 1MiB 100%

# Format the partition
losetup -fP "${DRIVE_IMG}"
LOOP=$(losetup -j "${DRIVE_IMG}" | cut -d: -f1)
mkfs.vfat -F 32 "${LOOP}p1"
losetup -d "${LOOP}"

echo "Done."
