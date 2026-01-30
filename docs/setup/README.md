# Setup Instructions

This guide covers installing and operating the two-role layout: Pi #1 Drive (USB Gadget) and Pi #2 Processor (video/face).


## 📋 Overview

The Blink Sync Brain system uses two Raspberry Pi Zero 2 W boards:

- **Pi Zero 2 W Drive**: USB Gadget Mode - Acts as virtual USB storage for Blink Sync Module
- **Pi Zero 2 W Processor**: Video Processing Hub - Handles video analysis and face recognition


See: **[Pi Zero Setup Guide](pi-zero-setup.md)** and **[Pi Quick Reference](pi-quick-reference.md)**.

### Quick Pi Setup Overview

**Pi #1 Drive:**
- Virtual USB storage for Blink Sync Module
- Configure USB gadget, Samba optional

**Pi #2 Processor:**
- Video analysis, face recognition
- Installs OpenCV/face-recognition and runs watcher

## 📋 Prerequisites

- Raspberry Pi OS Lite 64-bit on both Pis
- SSH enabled and network configured
- Python 3.8+ on both

## 🚀 Install by Role

### Pi #1 Drive
```bash
pip install .[drive]
sudo mkdir -p /etc/blink-sync-brain && sudo cp configs/drive.yaml /etc/blink-sync-brain/config.yaml
sudo cp scripts/drive/start_storage_mode.sh /opt/blink-sync-brain/start_storage_mode.sh && sudo chmod +x /opt/blink-sync-brain/start_storage_mode.sh
sudo cp scripts/systemd/blink-drive.service /etc/systemd/system/
sudo systemctl enable --now blink-drive
```

### Pi #2 Processor
```bash
sudo apt update && sudo apt install -y ffmpeg
pip install .[processor]
sudo mkdir -p /etc/blink-sync-brain && sudo cp configs/processor.yaml /etc/blink-sync-brain/config.yaml
sudo cp scripts/systemd/blink-processor.service /etc/systemd/system/
sudo systemctl enable --now blink-processor
```

## 🔧 Configuration

- Pi #1: edit `/etc/blink-sync-brain/config.yaml` based on `configs/drive.yaml`
- Pi #2: edit `/etc/blink-sync-brain/config.yaml` based on `configs/processor.yaml`

## 🔌 Blink Integration

1. Connect Pi #1's USB data port to the Blink Sync Module
2. In the Blink app, choose Local Storage and select the presented drive

## 🧪 Quick checks

```bash
# Pi #1
blink-drive status

# Pi #2
blink-processor status
blink-processor process-video /path/to/test.mp4 --output-dir /var/blink_storage/results
```

## 🚨 Troubleshooting

See the role-specific sections in [pi-brain-drive-setup.md](pi-brain-drive-setup.md) for USB gadget and processing troubleshooting.
