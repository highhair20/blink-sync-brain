#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-lens"

echo "Installing Blink Drive application..."

cd "${REPO_DIR}"
python3 -m venv env
source env/bin/activate
pip install --upgrade -q .[drive]

ln -sf "${REPO_DIR}/env/bin/blink-drive" /usr/local/bin/blink-drive
echo "Symlinked blink-drive to /usr/local/bin/blink-drive"

echo "Done."
