#!/bin/bash
set -euo pipefail

echo "Installing system dependencies for Blink Drive..."
apt install -y python3 python3-pip python3-venv screen parted rsync
echo "Done."
