# Blink Sync Brain

A Raspberry Pi-based system that extends Blink security cameras with face recognition, local video storage, and intelligent video processing. Two Raspberry Pi Zero 2 Ws work together in a dual-role architecture to intercept, analyze, and manage video clips from Blink cameras.

## Overview

Blink cameras don't provide local storage or advanced video analysis. This project solves that by intercepting the Blink Sync Module's USB connection using a virtual USB gadget, capturing clips locally, and running machine learning-based face recognition on a dedicated processor Pi.

### Architecture

| | Pi #1 — Drive (USB Gadget) | Pi #2 — Processor (Video & Face Recognition) |
|---|---|---|
| **Role** | Emulates a USB flash drive to the Blink Sync Module | Processes intercepted video clips and performs face recognition |
| **Key Components** | `USBGadgetManager` | `VideoProcessor`, `FaceRecognitionEngine` |
| **Capabilities** | Virtual 32GB FAT32 drive image, mode switching between Storage Mode (Blink access) and Server Mode (processor access), Samba file sharing, storage monitoring | Frame extraction, face detection and matching against a known-faces database, batch processing, result storage and metadata tracking |

### Data Flow

1. **Capture** — Blink camera records a clip and writes it to what it thinks is a USB drive (actually Pi #1's virtual drive image)
2. **Transfer** — Pi #1 switches to Server Mode so Pi #2 can access new clips
3. **Process** — Pi #2 extracts frames, runs face detection/recognition against the known-faces database
4. **Notify** — Known faces are logged; unknown faces trigger notifications (email, Pushbullet, or webhooks)
5. **Cleanup** — Old clips are automatically removed based on configurable retention policies (default: 30 days, 80% storage threshold)

### Key Technologies

- **Python 3.8+** with async architecture
- **face_recognition** + **OpenCV** for video/image processing
- **TensorFlow Lite** for edge ML inference
- **structlog** for structured JSON logging
- **YAML configuration** with environment variable overrides
- **systemd services** for automatic startup on each Pi

## 📖 Documentation

This project contains multiple README files with detailed documentation and visual guides:

### 🖼️ Visual Documentation

- ? **[Architecture Overview](./docs/architecture/README.md)** - System architecture diagrams and flow charts
- ? **[User Interface Guide](./docs/ui/README.md)** - Screenshots and UI walkthroughs
- **[Setup Instructions](./docs/setup/README.md)** - Step-by-step setup with annotated screenshots
- ? **[API Documentation](./docs/api/README.md)** - API endpoints with request/response examples
- ? **[Troubleshooting Guide](./docs/troubleshooting/README.md)** - Common issues with visual solutions

### 🍓 Raspberry Pi Setup Guides

- **[Complete Pi Zero Setup Guide](./docs/setup/pi-zero-setup.md)**
- **[Pi Quick Reference](./docs/setup/pi-quick-reference.md)**

### 📋 Quick Start

1. **Installation**: See [Setup Instructions](./docs/setup/README.md) for detailed installation steps
2. **Configuration**: Follow the [Architecture Overview](./docs/architecture/README.md) for system setup
3. **Usage**: Check the [User Interface Guide](./docs/ui/README.md) for interface walkthroughs

## 🚀 Features

- **Raspberry Pi Zero 2 W Integration**: Dual Pi setup for USB gadget mode and video processing
- **Local Video Storage**: Virtual USB drive for Blink Sync Module storage
- **Face Recognition**: Advanced face detection and recognition using machine learning
- **Video Processing**: Automated video analysis, stitching, and management
- **Intelligent Storage**: Smart cleanup and retention policies
- **Real-time Notifications**: Alert system for unknown faces and events
- **Comprehensive API**: RESTful API for system management and monitoring

## 📁 Project Structure

```
blink-sync-brain/
├── configs/
│   ├── drive.yaml                # Example config for Pi #1 (Drive)
│   └── processor.yaml            # Example config for Pi #2 (Processor)
├── scripts/
│   ├── drive/usb-gadget.sh       # USB gadget config script for Pi #1
│   └── systemd/
│       ├── blink-drive.service   # Systemd unit for Pi #1
│       └── blink-processor.service # Systemd unit for Pi #2
├── src/
│   └── blink_sync_brain/
│       ├── common/               # Shared code
│       ├── drive/                # Role-specific code for Pi #1 (Drive)
│       ├── processor/            # Role-specific code for Pi #2 (Processor)
│       ├── config/               # Settings
│       ├── models/               # Data models
│       └── utils/                # Utility functions
└── docs/
    └── setup/
        └── pi-zero-setup.md
```

## 🔗 Quick Links

- **Getting Started**: [Setup Guide](./docs/setup/README.md)
- **System Overview**: [Architecture Documentation](./docs/architecture/README.md)
- **User Guide**: [Interface Documentation](./docs/ui/README.md)
- **API Reference**: [API Documentation](./docs/api/README.md)
- **Need Help?**: [Troubleshooting Guide](./docs/troubleshooting/README.md)

## 🍓 Roles and CLIs

- Pi #1 Drive CLI: `blink-drive`
  - `blink-drive setup|start|stop|status`
- Pi #2 Processor CLI: `blink-processor`
  - `blink-processor start|status|process-video <file>`

## 🚀 Quick Start

```bash
# On Pi #1 (Drive)
pip install .[drive]
sudo cp scripts/systemd/blink-drive.service /etc/systemd/system/
sudo systemctl enable --now blink-drive

# On Pi #2 (Processor)
pip install .[processor]
sudo cp scripts/systemd/blink-processor.service /etc/systemd/system/
sudo systemctl enable --now blink-processor

# Ad-hoc processing on Pi #2
blink-processor process-video /path/to/video.mp4 --output-dir /var/blink_storage/results
```

## 📝 Contributing

Please read our contributing guidelines before submitting pull requests. Each documentation file contains relevant images and diagrams to help you understand the system better.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*For detailed visual documentation, please refer to the individual README files in the `docs/` directory.*