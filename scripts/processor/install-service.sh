#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-sync-brain"

echo "Installing Blink Processor systemd service..."

cp "${REPO_DIR}/scripts/systemd/blink-processor.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now blink-processor

echo "Done."
