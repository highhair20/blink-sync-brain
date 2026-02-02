#!/bin/bash
set -euo pipefail

echo "Installing system dependencies for Blink Processor..."
apt install -y python3 python3-pip

# Video processing
apt install -y ffmpeg libgomp1

# Build dependencies for dlib (required by face-recognition)
apt install -y cmake build-essential gfortran
apt install -y libblas-dev liblapack-dev libopenblas-dev
echo "Done."
