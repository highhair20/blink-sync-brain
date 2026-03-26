#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-lens"

echo "Installing Blink Processor application..."

cd "${REPO_DIR}"
python -m venv env
source env/bin/activate
pip install .[processor]

ln -sf "${REPO_DIR}/env/bin/blink-processor" /usr/local/bin/blink-processor
echo "Symlinked blink-processor to /usr/local/bin/blink-processor"

echo "Done."
