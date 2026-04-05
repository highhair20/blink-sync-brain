"""
Unit tests for blink_lens.models.
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from blink_lens.models.face_data import FaceData, KnownFace
from blink_lens.models.processing_result import ProcessingResult
from blink_lens.models.video_metadata import VideoMetadata


class TestVideoMetadata:
    def _make(self, **kwargs):
        defaults = dict(
            width=1920,
            height=1080,
            fps=30.0,
            duration=10.0,
            codec="h264",
            created=datetime(2024, 1, 1, 12, 0, 0),
            file_size=5_000_000,
        )
        defaults.update(kwargs)
        return VideoMetadata(**defaults)

    def test_resolution_computed(self):
        m = self._make()
        assert m.resolution == "1920x1080"

    def test_bitrate_computed(self):
        m = self._make(duration=10.0, file_size=1_000_000)
        assert m.bitrate == pytest.approx((1_000_000 * 8) / 10.0)

    def test_bitrate_not_computed_when_duration_zero(self):
        m = self._make(duration=0.0)
        assert m.bitrate is None

    def test_to_dict_keys(self):
        m = self._make()
        d = m.to_dict()
        for key in ("width", "height", "fps", "duration", "codec", "created", "file_size"):
            assert key in d

    def test_round_trip(self):
        m = self._make()
        m2 = VideoMetadata.from_dict(m.to_dict())
        assert m2.width == m.width
        assert m2.fps == m.fps
        assert m2.resolution == m.resolution


class TestFaceData:
    def test_to_dict_round_trip(self):
        enc = np.zeros(128)
        fd = FaceData(
            encoding=enc,
            location=(10, 50, 60, 20),
            confidence=0.9,
            timestamp=datetime(2024, 3, 15, 8, 0, 0),
        )
        d = fd.to_dict()
        fd2 = FaceData.from_dict(d)
        assert fd2.confidence == fd.confidence
        assert fd2.location == fd.location
        assert np.allclose(fd2.encoding, fd.encoding)


class TestKnownFace:
    def test_post_init_sets_added_date(self):
        kf = KnownFace(name="Alice", encoding=np.zeros(128))
        assert kf.added_date is not None

    def test_update_detection(self):
        kf = KnownFace(name="Bob", encoding=np.zeros(128))
        assert kf.detection_count == 0
        kf.update_detection()
        assert kf.detection_count == 1
        assert kf.last_seen is not None

    def test_get_age_days(self):
        kf = KnownFace(name="Carol", encoding=np.zeros(128))
        age = kf.get_age_days()
        assert age >= 0

    def test_get_days_since_last_seen_none_when_never_seen(self):
        kf = KnownFace(name="Dave", encoding=np.zeros(128))
        assert kf.get_days_since_last_seen() is None

    def test_to_dict_round_trip(self):
        kf = KnownFace(name="Eve", encoding=np.ones(128) * 0.5, confidence_threshold=0.7)
        d = kf.to_dict()
        kf2 = KnownFace.from_dict(d)
        assert kf2.name == kf.name
        assert kf2.confidence_threshold == kf.confidence_threshold
        assert np.allclose(kf2.encoding, kf.encoding)


class TestProcessingResult:
    def _make_metadata(self):
        return VideoMetadata(
            width=640,
            height=480,
            fps=25.0,
            duration=5.0,
            codec="h264",
            created=datetime(2024, 6, 1),
            file_size=1_000,
        )

    def test_has_unknown_faces(self):
        result = ProcessingResult(
            video_path=Path("clip.mp4"),
            metadata=self._make_metadata(),
            face_detections=[{"name": "Unknown"}, {"name": "Alice"}],
            recognized_faces=[{"name": "Alice"}],
            processing_time=1.0,
            timestamp=datetime.now(),
        )
        assert result.has_unknown_faces() is True
        assert result.get_unknown_face_count() == 1

    def test_no_unknown_faces(self):
        result = ProcessingResult(
            video_path=Path("clip.mp4"),
            metadata=self._make_metadata(),
            face_detections=[{"name": "Alice"}],
            recognized_faces=[{"name": "Alice"}],
            processing_time=1.0,
            timestamp=datetime.now(),
        )
        assert result.has_unknown_faces() is False

    def test_get_recognized_names_deduplicates(self):
        result = ProcessingResult(
            video_path=Path("clip.mp4"),
            metadata=self._make_metadata(),
            face_detections=[],
            recognized_faces=[{"name": "Alice"}, {"name": "Alice"}, {"name": "Bob"}],
            processing_time=0.5,
            timestamp=datetime.now(),
        )
        names = result.get_recognized_names()
        assert sorted(names) == ["Alice", "Bob"]

    def test_to_dict_round_trip(self):
        result = ProcessingResult(
            video_path=Path("clip.mp4"),
            metadata=self._make_metadata(),
            face_detections=[],
            recognized_faces=[],
            processing_time=2.3,
            timestamp=datetime(2024, 7, 4, 12, 0, 0),
        )
        d = result.to_dict()
        r2 = ProcessingResult.from_dict(d)
        assert r2.processing_time == result.processing_time
        assert r2.status == result.status
