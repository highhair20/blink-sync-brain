#!/bin/bash
set -euo pipefail

echo "Installing system dependencies for Blink Processor..."
apt-get update -q
apt-get install -y python3 python3-pip python3-venv screen

# Video processing
apt-get install -y ffmpeg libgomp1

# Build dependencies for dlib (required by face-recognition)
apt-get install -y cmake build-essential gfortran
apt-get install -y libblas-dev liblapack-dev libopenblas-dev
echo "Done."
