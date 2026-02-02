#!/bin/bash
set -euo pipefail

STORAGE_DIR="/var/blink_storage"

echo "Setting up Blink Processor storage directories..."

mkdir -p "${STORAGE_DIR}/videos"
mkdir -p "${STORAGE_DIR}/results"
chown pi:pi "${STORAGE_DIR}"

echo "Done."
