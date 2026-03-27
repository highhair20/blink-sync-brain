#!/bin/bash
set -euo pipefail

# Full install for Blink Processor (Pi #2).
#
# Usage: sudo ./install.sh
#
# Note: pip install with dlib/face-recognition compilation takes a long time.
# Running this inside screen is recommended: screen sudo ./install.sh

REPO_DIR="/opt/blink-lens"

echo "Installing Blink Processor (Pi #2)..."

"${REPO_DIR}/scripts/processor/install-deps.sh"
"${REPO_DIR}/scripts/processor/setup-storage.sh"
"${REPO_DIR}/scripts/processor/install-app.sh"
"${REPO_DIR}/scripts/processor/install-service.sh"

echo ""
echo "Done. blink-processor is running."
