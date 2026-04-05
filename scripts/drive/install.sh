#!/bin/bash
set -euo pipefail

# Full install for Blink Drive (Pi #1).
# Run after:
#   1. enable-usb-gadget.sh + reboot
#   2. Running configure.sh <pi2-ip>
#
# Usage: sudo ./install.sh
#
# Note: Virtual drive image creation takes several minutes.
# Running this inside screen is recommended: screen sudo ./install.sh

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script must be run with sudo."
    echo "  Run: sudo $0"
    exit 1
fi

REPO_DIR="/opt/blink-lens"

# Pre-flight check 1: verify enable-usb-gadget.sh has been run (config.txt updated).
if ! grep -q "^dtoverlay=dwc2,dr_mode=peripheral$" /boot/firmware/config.txt 2>/dev/null; then
    echo "ERROR: USB gadget mode is not enabled."
    echo "  Run: sudo ${REPO_DIR}/scripts/drive/enable-usb-gadget.sh"
    echo "  Then reboot: sudo reboot"
    echo "  Then run this installer again."
    exit 1
fi

# Pre-flight check 2: verify the Pi has been rebooted since enable-usb-gadget.sh ran.
# config.txt can be updated without a reboot — dwc2 must actually be loaded in the
# running kernel for g_mass_storage to work as a USB device controller.
if ! lsmod | grep -q "^dwc2"; then
    echo "ERROR: dwc2 module is not loaded — the Pi needs to be rebooted."
    echo "  Reboot now: sudo reboot"
    echo "  Then run this installer again."
    exit 1
fi

echo "Installing Blink Drive (Pi #1)..."

"${REPO_DIR}/scripts/drive/install-deps.sh"

# Read virtual_drive_size_gb from drive.yaml so the image matches the configured size.
# Falls back to 32 if the key is missing or python3/pyyaml is unavailable.
DRIVE_SIZE_GB=$(python3 -c "
import sys, yaml
try:
    d = yaml.safe_load(open('${REPO_DIR}/configs/drive.yaml'))
    print(d.get('storage', {}).get('virtual_drive_size_gb', 32))
except Exception:
    print(32)
" 2>/dev/null || echo 32)

"${REPO_DIR}/scripts/drive/create-virtual-storage.sh" "${DRIVE_SIZE_GB}"
"${REPO_DIR}/scripts/drive/install-app.sh"
"${REPO_DIR}/scripts/drive/install-service.sh"

echo ""

# Post-install: warn if configure.sh hasn't been run yet.
# blink-watcher will fail on reboot if processor_host is still empty.
if grep -q 'processor_host: ""' "${REPO_DIR}/configs/drive.yaml" 2>/dev/null; then
    echo "WARNING: Pi #2 is not configured yet."
    echo "  Run configure.sh before rebooting, otherwise blink-watcher will fail:"
    echo ""
    echo "  /opt/blink-lens/scripts/drive/configure.sh <pi2-ip>"
    echo ""
    echo "  Then reboot: sudo reboot"
else
    echo "Done. Reboot to start services: sudo reboot"
fi
