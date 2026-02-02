#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-sync-brain"

echo "Installing Blink Drive application..."

cd "${REPO_DIR}"
python -m venv env
source env/bin/activate
pip install .[drive]

echo "Done."
