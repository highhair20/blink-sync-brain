#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-sync-brain"

echo "Installing Blink Drive systemd service..."

cp "${REPO_DIR}/scripts/drive/systemd/blink-drive.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now blink-drive

echo "Done."
