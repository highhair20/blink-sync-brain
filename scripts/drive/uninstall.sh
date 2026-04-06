#!/bin/bash
set -euo pipefail

# Usage: sudo ./uninstall.sh [--purge]
#   --purge  Also delete the virtual drive image and all data in /var/blink_storage

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run with sudo."
    echo "  Run: sudo $0 $*"
    exit 1
fi

PURGE=false
for arg in "$@"; do
    [[ "$arg" == "--purge" ]] && PURGE=true
done

echo "Uninstalling Blink Drive (Pi #1)..."

# ── Stop and disable services ─────────────────────────────────────────────────
for svc in blink-watcher blink-drive; do
    if systemctl is-active --quiet "${svc}" 2>/dev/null; then
        echo "Stopping ${svc}..."
        systemctl stop "${svc}"
    fi
    if systemctl is-enabled --quiet "${svc}" 2>/dev/null; then
        echo "Disabling ${svc}..."
        systemctl disable "${svc}"
    fi
done

# ── Remove service files ──────────────────────────────────────────────────────
for svc_file in /etc/systemd/system/blink-drive.service \
                /etc/systemd/system/blink-watcher.service; do
    if [[ -f "${svc_file}" ]]; then
        echo "Removing ${svc_file}..."
        rm "${svc_file}"
    fi
done

systemctl daemon-reload

# ── Remove symlink and Python virtualenv ─────────────────────────────────────
if [[ -L /usr/local/bin/blink-drive ]]; then
    echo "Removing /usr/local/bin/blink-drive symlink..."
    rm /usr/local/bin/blink-drive
fi

VENV="/opt/blink-lens/env"
if [[ -d "${VENV}" ]]; then
    echo "Removing virtualenv at ${VENV}..."
    rm -rf "${VENV}"
fi

# ── Remove configuration env file ────────────────────────────────────────────
if [[ -f /etc/blink-lens/env ]]; then
    echo "Removing /etc/blink-lens/env..."
    rm /etc/blink-lens/env
fi
rmdir --ignore-fail-on-non-empty /etc/blink-lens 2>/dev/null || true

# ── Reverse USB gadget boot config ───────────────────────────────────────────
CONFIG="/boot/firmware/config.txt"
if [[ -f "${CONFIG}" ]]; then
    if grep -q "^dtoverlay=dwc2,dr_mode=peripheral$" "${CONFIG}"; then
        echo "Removing dtoverlay=dwc2,dr_mode=peripheral from ${CONFIG}..."
        sed -i '/^dtoverlay=dwc2,dr_mode=peripheral$/d' "${CONFIG}"
    fi
fi

if grep -q "^dwc2" /etc/modules; then
    echo "Removing dwc2 from /etc/modules..."
    sed -i '/^dwc2$/d' /etc/modules
fi

# ── Unmount shadow mount if active ───────────────────────────────────────────
# Read paths from drive.yaml if possible; fall back to defaults.
# Note: the venv is already removed at this point, so system python3 is used.
CONFIG="/opt/blink-lens/configs/drive.yaml"
SHADOW=$(python3 -c "
import yaml
try:
    d = yaml.safe_load(open('${CONFIG}'))
    print(d.get('watcher', {}).get('shadow_mount_point', '/mnt/blink_shadow'))
except Exception:
    print('/mnt/blink_shadow')
" 2>/dev/null || echo "/mnt/blink_shadow")

DRIVE=$(python3 -c "
import yaml
try:
    d = yaml.safe_load(open('${CONFIG}'))
    print(d.get('storage', {}).get('virtual_drive_path', '/var/blink_storage/virtual_drive.img'))
except Exception:
    print('/var/blink_storage/virtual_drive.img')
" 2>/dev/null || echo "/var/blink_storage/virtual_drive.img")

if mountpoint -q "${SHADOW}" 2>/dev/null; then
    echo "Unmounting shadow mount at ${SHADOW}..."
    umount "${SHADOW}"
fi

# Detach any loop devices backed by the virtual drive image
if [[ -f "${DRIVE}" ]]; then
    losetup -j "${DRIVE}" 2>/dev/null | awk -F: '{print $1}' | while read -r loop; do
        echo "Detaching loop device ${loop}..."
        losetup -d "${loop}"
    done
fi

# ── Purge data (opt-in) ───────────────────────────────────────────────────────
if [[ "${PURGE}" == true ]]; then
    echo "Purging virtual drive image and storage data..."
    rm -f "${DRIVE}"
    rm -f /var/blink_storage/watcher_state.json
    rmdir --ignore-fail-on-non-empty "${SHADOW}" 2>/dev/null || true
    echo "Warning: /var/blink_storage retained. Remove manually if no longer needed."
else
    echo "Data preserved. Run with --purge to also delete the virtual drive image."
    rmdir --ignore-fail-on-non-empty "${SHADOW}" 2>/dev/null || true
fi

echo "Done. Reboot to fully unload USB gadget kernel modules: sudo reboot"
