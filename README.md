# Blink Lens

A Raspberry Pi-based system that extends Blink security cameras with local video storage and face recognition. Two Raspberry Pi Zero 2 Ws work together — one emulates a USB flash drive for the Blink Sync Module, the other processes the captured clips.

## How It Works

Blink cameras save clips to the Blink Sync Module via USB. Pi #1 intercepts this by presenting itself as a USB flash drive using Linux USB gadget mode. A file watcher detects new clips and pushes them to Pi #2 over SSH. Pi #2 extracts frames, runs face detection and recognition, and fires notifications for unknown faces.

### Data Flow

1. **Capture** — Blink writes a clip to what it thinks is a USB drive (Pi #1's virtual 32GB FAT32 image)
2. **Transfer** — Pi #1's file watcher shadow-mounts the image read-only, detects new files, and rsyncs them to Pi #2
3. **Process** — Pi #2 extracts frames and runs face detection/recognition against a known-faces database
4. **Notify** — Unknown faces trigger notifications (email, Pushbullet, or webhooks)
5. **Cleanup** — Old clips are automatically removed based on configurable retention policies (default: 30 days, 80% threshold)

### Architecture

| | Pi #1 — `blink-drive` | Pi #2 — `blink-processor` |
|---|---|---|
| **Role** | Emulates USB flash drive to Blink Sync Module | Processes video clips and runs face recognition |
| **CLI** | `blink-drive start\|stop\|status\|watch` | `blink-processor start\|status\|process-video` |
| **Key Tech** | USB gadget (`g_mass_storage`), rsync over SSH | OpenCV, face_recognition (dlib) |

### Key Technologies

- **Python 3.8+** with async architecture
- **face_recognition** + **OpenCV** for video and image processing
- **structlog** for structured JSON logging
- **YAML configuration** with environment variable overrides
- **systemd services** for automatic startup on each Pi

## 📖 Setup

- **[Hardware & OS Setup](./docs/setup/pi-zero-setup.md)** — Flash SD cards, configure hostnames, first boot
- **[Application Setup](./docs/setup/blink-app-setup.md)** — Full install guide for both Pis

## 📝 Contributing

Please read our contributing guidelines before submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*For detailed documentation, see the [Hardware & OS Setup](./docs/setup/pi-zero-setup.md) and [Application Setup](./docs/setup/blink-app-setup.md) guides.*
