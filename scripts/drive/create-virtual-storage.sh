#!/bin/bash
set -euo pipefail

STORAGE_DIR="/var/blink_storage"
DRIVE_IMG="${STORAGE_DIR}/virtual_drive.img"
SIZE_MB=32768

echo "Creating virtual storage at ${DRIVE_IMG} (${SIZE_MB} MB)..."

mkdir -p "${STORAGE_DIR}"

# Determine the non-root owner for the storage directory.
# SUDO_USER is set when the script is run via sudo; fall back to 'pi' only
# if that user actually exists, otherwise fail fast with a clear message.
if [[ -n "${SUDO_USER:-}" ]]; then
    OWNER="${SUDO_USER}"
elif id pi &>/dev/null; then
    OWNER="pi"
else
    echo "ERROR: Cannot determine storage directory owner."
    echo "  Run this script via sudo: sudo $0"
    echo "  Or run as the non-root user who owns the Pi."
    exit 1
fi

chown "${OWNER}:${OWNER}" "${STORAGE_DIR}"
chmod 755 "${STORAGE_DIR}"

mkdir -p /mnt/blink_shadow

# Create the disk image
dd if=/dev/zero of="${DRIVE_IMG}" bs=1M count="${SIZE_MB}" status=progress

# Create partition table and FAT32 partition (required for Blink Sync Module)
parted "${DRIVE_IMG}" --script mklabel msdos
parted "${DRIVE_IMG}" --script mkpart primary fat32 1MiB 100%

# Format the partition
losetup -fP "${DRIVE_IMG}"
LOOP=$(losetup -j "${DRIVE_IMG}" | cut -d: -f1)

# Always detach the loop device on exit (success, failure, or Ctrl-C)
trap 'losetup -d "${LOOP}" 2>/dev/null || true' EXIT

mkfs.vfat -F 32 "${LOOP}p1"

echo "Done."
