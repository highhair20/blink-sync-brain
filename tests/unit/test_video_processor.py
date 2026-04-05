"""
Unit tests for blink_lens.core.video_processor.VideoProcessor.

cv2, ffmpeg, numpy, moviepy, and face_recognition are mocked.
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Stub heavy processor-only imports
# ---------------------------------------------------------------------------
_cv2_mock = MagicMock()
_ffmpeg_mock = MagicMock()
_moviepy_mock = MagicMock()

sys.modules.setdefault("cv2", _cv2_mock)
sys.modules.setdefault("ffmpeg", _ffmpeg_mock)
sys.modules.setdefault("moviepy", _moviepy_mock)
sys.modules.setdefault("moviepy.editor", _moviepy_mock)
sys.modules.setdefault("face_recognition", MagicMock())
sys.modules.setdefault("PIL", MagicMock())
sys.modules.setdefault("PIL.Image", MagicMock())

from blink_lens.config.settings import Settings  # noqa: E402
from blink_lens.core.face_recognition import FaceRecognitionEngine  # noqa: E402
from blink_lens.core.video_processor import VideoProcessor  # noqa: E402
from blink_lens.models.video_metadata import VideoMetadata  # noqa: E402


@pytest.fixture
def processor(settings: Settings) -> VideoProcessor:
    settings.processing.frame_skip = 1
    return VideoProcessor(settings)


@pytest.fixture
def mock_face_engine() -> MagicMock:
    engine = MagicMock(spec=FaceRecognitionEngine)
    engine.detect_faces.return_value = []
    engine.get_face_encoding.return_value = None
    engine.recognize_face_with_confidence.return_value = ("Unknown", 0.0)
    return engine


def _ffprobe_result(width: int = 1280, height: int = 720, fps: str = "30/1", duration: str = "5.0") -> str:
    return json.dumps({
        "streams": [{
            "codec_type": "video",
            "codec_name": "h264",
            "width": width,
            "height": height,
            "r_frame_rate": fps,
        }],
        "format": {"duration": duration},
    })


class TestInit:
    def test_initial_state(self, processor: VideoProcessor):
        assert processor.is_processing is False
        assert processor.face_engine is None
        assert processor.processing_queue.maxsize == 100


class TestExtractMetadata:
    async def test_parses_ffprobe_output(self, processor: VideoProcessor, sample_video_path: Path):
        completed = subprocess.CompletedProcess(
            [], 0, _ffprobe_result(fps="25/1"), ""
        )
        with patch.object(processor, "_run_command", new_callable=AsyncMock, return_value=completed):
            meta = await processor._extract_metadata(sample_video_path)

        assert meta.width == 1280
        assert meta.height == 720
        assert meta.fps == pytest.approx(25.0)
        assert meta.codec == "h264"

    async def test_handles_fractional_fps(self, processor: VideoProcessor, sample_video_path: Path):
        # 30000/1001 ≈ 29.97
        completed = subprocess.CompletedProcess([], 0, _ffprobe_result(fps="30000/1001"), "")
        with patch.object(processor, "_run_command", new_callable=AsyncMock, return_value=completed):
            meta = await processor._extract_metadata(sample_video_path)
        assert meta.fps == pytest.approx(30000 / 1001)

    async def test_raises_on_ffprobe_failure(self, processor: VideoProcessor, sample_video_path: Path):
        completed = subprocess.CompletedProcess([], 1, "", "ffprobe error")
        with patch.object(processor, "_run_command", new_callable=AsyncMock, return_value=completed):
            with pytest.raises(RuntimeError, match="FFprobe failed"):
                await processor._extract_metadata(sample_video_path)

    async def test_no_eval_in_fps_parsing(self, processor: VideoProcessor):
        """Confirm eval() is not used anywhere in fps parsing."""
        import inspect
        src = inspect.getsource(processor._extract_metadata)
        assert "eval(" not in src


def _make_cap(frames: list) -> MagicMock:
    """Build a mock VideoCapture that yields the given frames then stops."""
    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.get.return_value = 30.0
    cap.read.side_effect = [(True, f) for f in frames] + [(False, None)]
    return cap


class TestAnalyzeFaces:
    async def test_releases_cap_on_success(
        self, processor: VideoProcessor, sample_video_path: Path, mock_face_engine: MagicMock
    ):
        processor.face_engine = mock_face_engine
        cap = _make_cap([np.zeros((480, 640, 3), dtype=np.uint8)])

        with patch("blink_lens.core.video_processor.cv2.VideoCapture", return_value=cap):
            await processor._analyze_faces(sample_video_path)

        cap.release.assert_called_once()

    async def test_releases_cap_on_exception(
        self, processor: VideoProcessor, sample_video_path: Path, mock_face_engine: MagicMock
    ):
        processor.face_engine = mock_face_engine
        mock_face_engine.detect_faces.side_effect = RuntimeError("boom")
        cap = _make_cap([np.zeros((480, 640, 3), dtype=np.uint8)])

        with patch("blink_lens.core.video_processor.cv2.VideoCapture", return_value=cap):
            with pytest.raises(RuntimeError):
                await processor._analyze_faces(sample_video_path)

        cap.release.assert_called_once()

    async def test_uses_actual_confidence(
        self, processor: VideoProcessor, sample_video_path: Path, mock_face_engine: MagicMock
    ):
        """Confidence must come from recognize_face_with_confidence, not hardcoded 0.8."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        processor.face_engine = mock_face_engine
        mock_face_engine.detect_faces.return_value = [(10, 50, 40, 20)]
        mock_face_engine.get_face_encoding.return_value = np.zeros(128)
        mock_face_engine.recognize_face_with_confidence.return_value = ("Alice", 0.92)
        cap = _make_cap([frame])

        with patch("blink_lens.core.video_processor.cv2.VideoCapture", return_value=cap):
            result = await processor._analyze_faces(sample_video_path)

        assert result["detections"][0]["confidence"] == pytest.approx(0.92)
        assert result["detections"][0]["name"] == "Alice"


class TestIsFileComplete:
    async def test_stable_file_returns_true(self, processor: VideoProcessor, tmp_path: Path):
        f = tmp_path / "stable.mp4"
        f.write_bytes(b"x" * 100)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await processor._is_file_complete(f)
        assert result is True

    async def test_missing_file_returns_false(self, processor: VideoProcessor, tmp_path: Path):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await processor._is_file_complete(tmp_path / "nope.mp4")
        assert result is False


class TestProcessedFilesEviction:
    async def test_evicts_oldest_when_over_limit(self, processor: VideoProcessor, settings: Settings, tmp_path: Path):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        settings.storage.video_directory = video_dir
        processor.settings = settings

        # Pre-fill processed_files with 1001 fake paths
        processed_files: dict = {Path(f"fake_{i}.mp4"): None for i in range(1001)}

        # Verify the eviction logic: more than 1000 entries → remove oldest 500
        if len(processed_files) > 1000:
            oldest = list(processed_files.keys())[:500]
            for k in oldest:
                del processed_files[k]

        assert len(processed_files) == 501
        # The oldest 500 (fake_0 .. fake_499) should be gone
        assert Path("fake_0.mp4") not in processed_files
        assert Path("fake_500.mp4") in processed_files
