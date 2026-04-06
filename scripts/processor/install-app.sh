#!/bin/bash
set -euo pipefail

REPO_DIR="/opt/blink-lens"
SWAP_FILE="/var/tmp/blink-build-swap"

# dlib compiles from source and requires ~1.5 GB of memory.
# The Pi Zero 2 W has 512 MB RAM, so we create a temporary swap file
# for the duration of the build and remove it when done.
echo "Setting up temporary swap for dlib compilation..."
if [[ ! -f "${SWAP_FILE}" ]]; then
    fallocate -l 2G "${SWAP_FILE}" 2>/dev/null || \
        dd if=/dev/zero of="${SWAP_FILE}" bs=1M count=2048 status=progress
fi
chmod 600 "${SWAP_FILE}"
mkswap "${SWAP_FILE}"
swapon "${SWAP_FILE}"
trap 'swapoff "${SWAP_FILE}" 2>/dev/null || true; rm -f "${SWAP_FILE}"' EXIT

echo "Installing Blink Processor application..."

cd "${REPO_DIR}"
python3 -m venv env
source env/bin/activate

# MAKEFLAGS="-j1" limits cmake to one parallel job — reduces peak memory
# at the cost of longer build time (~45 min on Pi Zero 2 W).
# TMPDIR redirects large build temp files away from tmpfs.
TMPDIR=/var/tmp MAKEFLAGS="-j1" pip install --upgrade -q .[processor]

ln -sf "${REPO_DIR}/env/bin/blink-processor" /usr/local/bin/blink-processor
echo "Symlinked blink-processor to /usr/local/bin/blink-processor"

echo "Done."
