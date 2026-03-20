#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-lens"

echo "Installing Blink Processor systemd service..."

cp "${REPO_DIR}/scripts/processor/systemd/blink-processor.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now blink-processor

echo "Done."
