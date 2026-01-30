# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blink Sync Brain is a dual-Raspberry Pi Zero 2 W system that extends Blink security cameras with local storage and face recognition. Pi #1 (Drive) emulates a USB flash drive to the Blink Sync Module via USB gadget mode. Pi #2 (Processor) pulls clips from the virtual drive, runs face detection/recognition, and manages storage with retention policies.

## Build & Install

```bash
# Install for Drive Pi (minimal deps)
pip install .[drive]

# Install for Processor Pi (ML/CV stack)
pip install .[processor]

# Install with dev tools
pip install .[dev]
```

## Testing

```bash
pytest                          # Run all tests with coverage
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m "not slow"            # Skip slow-marked tests
pytest tests/unit/test_foo.py   # Run a single test file
pytest -k "test_name"           # Run a specific test by name
```

Coverage reports are generated automatically (terminal + `htmlcov/`).

## Linting & Formatting

All tool configuration lives in `pyproject.toml`.

```bash
black src/          # Format (line-length=88, target py38)
flake8 src/         # Lint (extends-ignore E203, W503)
mypy src/           # Type check (strict mode: disallow_untyped_defs, etc.)
```

## Architecture

### Dual-Role Design

The codebase is split by Pi role. Each role has its own CLI entry point, optional dependencies, config file, and systemd service:

- **Drive** (`src/blink_sync_brain/drive/`) — CLI: `blink-drive setup|start|stop|status`
- **Processor** (`src/blink_sync_brain/processor/`) — CLI: `blink-processor start|process-video|status`

Entry points are registered in `pyproject.toml` under `[project.scripts]`.

### Core Modules (`src/blink_sync_brain/core/`)

Shared business logic used by both roles:

- `usb_gadget.py` — `USBGadgetManager`: virtual drive image creation, USB gadget lifecycle, mode switching (Storage Mode for Blink access vs Server Mode for processor access via Samba)
- `video_processor.py` — `VideoProcessor`: frame extraction, face recognition integration, directory monitoring, processing queue
- `face_recognition.py` — `FaceRecognitionEngine`: face detection/encoding via `face_recognition` lib, known-face database (pickled numpy arrays), confidence scoring
- `storage_manager.py` — `StorageManager`: disk usage monitoring, retention policy enforcement (default 30 days, 80% threshold)
- `notification_service.py` — `NotificationService`: email, Pushbullet, webhook alerts for unknown faces

The `drive/` and `processor/` role modules re-export from `core/` and add CLI argument parsing.

### Configuration (`src/blink_sync_brain/config/settings.py`)

Dataclass-based settings with nested sections: `StorageSettings`, `ProcessingSettings`, `FaceRecognitionSettings`, `NotificationSettings`, `NetworkSettings`, `LoggingSettings`.

Loading precedence: dataclass defaults → `.env` file → YAML config file. Config files live in `configs/drive.yaml` and `configs/processor.yaml`. Key environment variables: `VIRTUAL_DRIVE_PATH`, `VIDEO_DIRECTORY`, `FACE_DATABASE_PATH`, `FACE_CONFIDENCE_THRESHOLD`, `LOG_LEVEL`.

### Data Models (`src/blink_sync_brain/models/`)

- `VideoMetadata` — resolution, FPS, duration, codec
- `FaceData` / `KnownFace` — face encodings, locations, detection stats
- `ProcessingResult` — complete processing output with metadata and recognized faces

### Async Patterns

Both CLI entry points use `async def _run()` with `asyncio.run()`. Video processing uses queue-based concurrency. Structured logging via `structlog` in JSON format.

## Key Paths (on Pi hardware)

```
/var/blink_storage/virtual_drive.img    # 32GB FAT32 virtual drive
/var/blink_storage/videos/              # Extracted video clips
/var/blink_storage/results/             # Processing results
/var/blink_storage/face_database.pkl    # Known faces database
/var/log/blink_sync_brain/app.log       # Application logs
```
