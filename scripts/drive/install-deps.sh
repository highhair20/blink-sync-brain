#!/bin/bash
set -euo pipefail

echo "Installing system dependencies for Blink Drive..."
apt install -y python3 python3-pip screen cmake libboost-all-dev
echo "Done."
