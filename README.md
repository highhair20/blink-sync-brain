# Blink Sync Brain

A comprehensive Blink camera system enhancement using Raspberry Pi Zero 2 W for local video processing, face recognition, and intelligent storage management.

## 📖 Documentation

This project contains multiple README files with detailed documentation and visual guides:

### 🖼️ Visual Documentation

- **[Architecture Overview](./docs/architecture/README.md)** - System architecture diagrams and flow charts
- **[User Interface Guide](./docs/ui/README.md)** - Screenshots and UI walkthroughs
- **[Setup Instructions](./docs/setup/README.md)** - Step-by-step setup with annotated screenshots
- **[API Documentation](./docs/api/README.md)** - API endpoints with request/response examples
- **[Troubleshooting Guide](./docs/troubleshooting/README.md)** - Common issues with visual solutions

### 🍓 Raspberry Pi Setup Guides

- **[Complete Pi Zero Setup Guide](./docs/setup/pi-zero-setup.md)** - Comprehensive instructions for both Pi boards
- **[Pi Quick Reference](./docs/setup/pi-quick-reference.md)** - Quick commands and troubleshooting for Pi management

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
├── src/
│   └── blink_sync_brain/
│       ├── core/                 # Core system components
│       │   ├── usb_gadget.py     # USB gadget mode manager
│       │   ├── video_processor.py # Video processing engine
│       │   ├── face_recognition.py # Face recognition engine
│       │   ├── storage_manager.py # Storage management
│       │   └── notification_service.py # Notification system
│       ├── config/               # Configuration management
│       ├── models/               # Data models
│       ├── services/             # Service layer
│       └── utils/                # Utility functions
├── docs/
│   ├── architecture/README.md    # System architecture with diagrams
│   ├── ui/README.md              # UI screenshots and guides
│   ├── setup/README.md           # Setup instructions with images
│   ├── api/README.md             # API documentation with examples
│   └── troubleshooting/README.md # Troubleshooting with visual aids
├── tests/                        # Test files
├── scripts/                      # Utility scripts
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## 🔗 Quick Links

- **Getting Started**: [Setup Guide](./docs/setup/README.md)
- **System Overview**: [Architecture Documentation](./docs/architecture/README.md)
- **User Guide**: [Interface Documentation](./docs/ui/README.md)
- **API Reference**: [API Documentation](./docs/api/README.md)
- **Need Help?**: [Troubleshooting Guide](./docs/troubleshooting/README.md)

## 🍓 Raspberry Pi Setup

### Pi Zero 2 W #1: USB Gadget Mode
- **Function**: Acts as virtual USB storage for Blink Sync Module
- **Setup**: USB gadget mode configuration and virtual drive creation
- **Storage**: Local video storage with ExFAT formatting

### Pi Zero 2 W #2: Video Processing Hub
- **Function**: Video analysis, face recognition, and management
- **Processing**: Face detection, video stitching, and storage management
- **Network**: WiFi connectivity for accessing shared storage

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Setup USB gadget mode (Pi #1)
blink-sync-brain setup usb-gadget

# Setup face recognition database (Pi #2)
blink-sync-brain setup face-database

# Start the complete system
blink-sync-brain start

# Process a single video
blink-sync-brain process-video /path/to/video.mp4

# Check system status
blink-sync-brain status
```

## 📝 Contributing

Please read our contributing guidelines before submitting pull requests. Each documentation file contains relevant images and diagrams to help you understand the system better.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*For detailed visual documentation, please refer to the individual README files in the `docs/` directory.*