#!/bin/bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run with sudo."
    echo "  Run: sudo $0 ${1:-}"
    exit 1
fi

STORAGE_DIR="/var/blink_storage"
DRIVE_IMG="${STORAGE_DIR}/virtual_drive.img"
SIZE_GB="${1:-32}"
SIZE_MB=$(( SIZE_GB * 1024 ))

echo "Creating virtual storage at ${DRIVE_IMG} (${SIZE_GB} GB)..."

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

# Skip image creation if it already exists at the expected size.
# This prevents wiping footage when re-running the installer after initial setup.
EXPECTED_BYTES=$(( SIZE_MB * 1024 * 1024 ))
if [[ -f "${DRIVE_IMG}" ]]; then
    ACTUAL_BYTES=$(stat -c%s "${DRIVE_IMG}" 2>/dev/null || echo 0)
    if [[ "${ACTUAL_BYTES}" -ge "${EXPECTED_BYTES}" ]]; then
        echo "Virtual drive already exists at full size — skipping creation."
        exit 0
    fi
    echo "WARNING: Existing image is smaller than expected (${ACTUAL_BYTES} bytes). Recreating."
fi

# Check available disk space before running dd.
# If a partial image already exists, credit its current size toward the requirement —
# dd will overwrite it in-place, so only the delta needs to come from free space.
# df -m outputs available space in MB; awk extracts the 4th column (Avail) of the data row.
PARTIAL_MB=0
if [[ -f "${DRIVE_IMG}" ]]; then
    PARTIAL_BYTES=$(stat -c%s "${DRIVE_IMG}" 2>/dev/null || echo 0)
    PARTIAL_MB=$(( PARTIAL_BYTES / 1024 / 1024 ))
fi
NEEDED_MB=$(( SIZE_MB - PARTIAL_MB ))
AVAILABLE_MB=$(df -m "${STORAGE_DIR}" | awk 'NR==2 {print $4}')
if [[ "${NEEDED_MB}" -gt 0 && "${AVAILABLE_MB}" -lt "${NEEDED_MB}" ]]; then
    AVAILABLE_GB=$(( ( AVAILABLE_MB + PARTIAL_MB ) / 1024 ))
    echo "ERROR: Not enough disk space to create the virtual drive."
    echo "  Required:  ${SIZE_GB} GB"
    echo "  Available: ${AVAILABLE_GB} GB"
    echo "  Use a larger SD card, or reduce virtual_drive_size_gb in configs/drive.yaml."
    exit 1
fi

# Create the disk image
dd if=/dev/zero of="${DRIVE_IMG}" bs=1M count="${SIZE_MB}" status=progress

# Create partition table and FAT32 partition (required for Blink Sync Module)
parted "${DRIVE_IMG}" --script mklabel msdos
parted "${DRIVE_IMG}" --script mkpart primary fat32 1MiB 100%

# Format the partition
losetup -fP "${DRIVE_IMG}"
LOOP=$(losetup -j "${DRIVE_IMG}" | cut -d: -f1)

# Always detach the loop device on exit (success, failure, or Ctrl-C)
trap '[[ -n "${LOOP}" ]] && losetup -d "${LOOP}" 2>/dev/null || true' EXIT

mkfs.vfat -F 32 "${LOOP}p1"

echo "Done."
