"""
Shared pytest fixtures for Blink Lens tests.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from blink_lens.config.settings import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Return a Settings instance pointing all paths at a temp directory."""
    s = Settings()
    s.storage.virtual_drive_path = tmp_path / "virtual_drive.img"
    s.storage.video_directory = tmp_path / "videos"
    s.storage.results_directory = tmp_path / "results"
    s.watcher.shadow_mount_point = tmp_path / "shadow"
    s.watcher.state_file = tmp_path / "watcher_state.json"
    s.watcher.processor_host = "192.168.1.2"
    s.face_recognition.database_path = tmp_path / "face_database.pkl"
    return s


@pytest.fixture
def face_encoding() -> np.ndarray:
    """Return a deterministic dummy face encoding (128-dim unit vector)."""
    rng = np.random.default_rng(seed=42)
    enc = rng.random(128).astype(np.float64)
    return enc / np.linalg.norm(enc)


@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Create a zero-byte placeholder video file."""
    p = tmp_path / "videos" / "clip_001.mp4"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"")
    return p
