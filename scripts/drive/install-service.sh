#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-lens"

echo "Installing Blink Drive systemd services..."

cp "${REPO_DIR}/scripts/drive/systemd/blink-drive.service" /etc/systemd/system/
cp "${REPO_DIR}/scripts/drive/systemd/blink-watcher.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now blink-drive
systemctl enable blink-watcher

echo "Done."
