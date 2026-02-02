#!/bin/bash
set -euo pipefail

STORAGE_DIR="/var/blink_storage"
DRIVE_IMG="${STORAGE_DIR}/virtual_drive.img"
SIZE_MB=32768

echo "Creating virtual storage at ${DRIVE_IMG} (${SIZE_MB} MB)..."

mkdir -p "${STORAGE_DIR}"
chown pi:pi "${STORAGE_DIR}"
chmod 755 "${STORAGE_DIR}"

dd if=/dev/zero of="${DRIVE_IMG}" bs=1M count="${SIZE_MB}" status=progress
mkfs.vfat -F 32 "${DRIVE_IMG}"

echo "Done."
