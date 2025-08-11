# Blink Sync Brain

Two Raspberry Pi Zero 2 Ws working together:
- Pi #1 Drive: USB Gadget that presents a virtual USB drive to the Blink Sync Module
- Pi #2 Processor: Pulls clips, runs face recognition and video processing, and stores results

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