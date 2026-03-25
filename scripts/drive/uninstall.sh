#!/bin/bash
set -euo pipefail

# Usage: sudo ./uninstall.sh [--purge]
#   --purge  Also delete the virtual drive image and all data in /var/blink_storage

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

# ── Remove Python virtualenv ──────────────────────────────────────────────────
VENV="/opt/blink-lens/env"
if [[ -d "${VENV}" ]]; then
    echo "Removing virtualenv at ${VENV}..."
    rm -rf "${VENV}"
fi

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
SHADOW="/mnt/blink_shadow"
if mountpoint -q "${SHADOW}" 2>/dev/null; then
    echo "Unmounting shadow mount at ${SHADOW}..."
    umount "${SHADOW}"
fi

# Detach any loop devices backed by the virtual drive image
DRIVE="/var/blink_storage/virtual_drive.img"
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
fi

echo "Done. Reboot to fully unload USB gadget kernel modules: sudo reboot"
