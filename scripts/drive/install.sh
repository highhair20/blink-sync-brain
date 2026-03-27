#!/bin/bash
set -euo pipefail

# Full install for Blink Drive (Pi #1).
# Run after:
#   1. enable-usb-gadget.sh + reboot
#   2. Setting processor_host in configs/drive.yaml
#   3. SSH key setup to Pi #2
#
# Usage: sudo ./install.sh
#
# Note: Virtual drive image creation (32 GB dd) takes several minutes.
# Running this inside screen is recommended: screen sudo ./install.sh

REPO_DIR="/opt/blink-lens"

echo "Installing Blink Drive (Pi #1)..."

"${REPO_DIR}/scripts/drive/install-deps.sh"
"${REPO_DIR}/scripts/drive/create-virtual-storage.sh"
"${REPO_DIR}/scripts/drive/install-app.sh"
"${REPO_DIR}/scripts/drive/install-service.sh"

echo ""
echo "Done. Reboot to start services: sudo reboot"
