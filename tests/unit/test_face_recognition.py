"""
Unit tests for blink_lens.core.face_recognition.FaceRecognitionEngine.

cv2, face_recognition, and PIL are mocked so this runs without the heavy
processor dependencies installed.
"""

import pickle
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Stub the processor-only imports before anything imports the real modules
# ---------------------------------------------------------------------------
_cv2_mock = MagicMock()
_face_rec_mock = MagicMock()
_pil_mock = MagicMock()

sys.modules.setdefault("cv2", _cv2_mock)
sys.modules.setdefault("face_recognition", _face_rec_mock)
sys.modules.setdefault("PIL", _pil_mock)
sys.modules.setdefault("PIL.Image", _pil_mock)

from blink_lens.config.settings import Settings  # noqa: E402
from blink_lens.core.face_recognition import FaceRecognitionEngine  # noqa: E402
from blink_lens.models.face_data import KnownFace  # noqa: E402


@pytest.fixture
def engine(settings: Settings) -> FaceRecognitionEngine:
    return FaceRecognitionEngine(settings)


@pytest.fixture
def loaded_engine(engine: FaceRecognitionEngine, face_encoding: np.ndarray) -> FaceRecognitionEngine:
    """Engine with one known face pre-loaded."""
    kf = KnownFace(name="Alice", encoding=face_encoding, confidence_threshold=0.4)
    engine.known_faces = [kf]
    engine.face_encodings = [face_encoding]
    engine.face_names = ["Alice"]
    engine.is_loaded = True
    engine.model_path = engine.settings.face_recognition.database_path
    return engine


class TestInit:
    def test_initial_state(self, engine: FaceRecognitionEngine):
        assert engine.is_loaded is False
        assert engine.known_faces == []
        assert engine.face_encodings == []
        assert engine.face_names == []


class TestLoadFaceDatabase:
    async def test_creates_new_db_when_missing(self, engine: FaceRecognitionEngine, settings: Settings):
        db_path = settings.face_recognition.database_path
        assert not db_path.exists()

        with patch.object(engine, "save_face_database", return_value=True) as mock_save:
            result = await engine.load_face_database(db_path)

        assert result is True
        assert engine.is_loaded is True
        mock_save.assert_called_once()

    async def test_loads_existing_db(self, engine: FaceRecognitionEngine, settings: Settings, face_encoding: np.ndarray):
        db_path = settings.face_recognition.database_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "known_faces": [KnownFace(name="Bob", encoding=face_encoding)],
            "encodings": [face_encoding],
            "names": ["Bob"],
            "last_updated": None,
        }
        with open(db_path, "wb") as f:
            pickle.dump(data, f)

        result = await engine.load_face_database(db_path)
        assert result is True
        assert engine.is_loaded is True
        assert engine.face_names == ["Bob"]

    async def test_returns_false_on_corrupt_db(self, engine: FaceRecognitionEngine, settings: Settings):
        db_path = settings.face_recognition.database_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_bytes(b"not a pickle")

        result = await engine.load_face_database(db_path)
        assert result is False


class TestSaveFaceDatabase:
    async def test_atomic_write_uses_tmp_file(self, loaded_engine: FaceRecognitionEngine, tmp_path: Path):
        import os

        replaced_pairs: list = []
        original_replace = os.replace

        def capturing_replace(src: str, dst: str) -> None:
            replaced_pairs.append((src, dst))
            original_replace(src, dst)

        with patch("blink_lens.core.face_recognition.os.replace", side_effect=capturing_replace):
            result = await loaded_engine.save_face_database()

        assert result is True
        assert len(replaced_pairs) == 1
        src, dst = replaced_pairs[0]
        assert str(src).endswith(".tmp")
        assert str(dst).endswith(".pkl")

    async def test_save_without_path_returns_false(self, engine: FaceRecognitionEngine):
        engine.model_path = None
        result = await engine.save_face_database()
        assert result is False


class TestDetectFaces:
    def test_delegates_to_face_recognition_lib(self, engine: FaceRecognitionEngine):
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _face_rec_mock.face_locations.return_value = [(10, 50, 60, 20)]
        locs = engine.detect_faces(img)
        assert locs == [(10, 50, 60, 20)]

    def test_returns_empty_on_exception(self, engine: FaceRecognitionEngine):
        _face_rec_mock.face_locations.side_effect = RuntimeError("boom")
        locs = engine.detect_faces(np.zeros((10, 10, 3), dtype=np.uint8))
        assert locs == []
        _face_rec_mock.face_locations.side_effect = None


class TestRecognizeFace:
    def test_unknown_when_not_loaded(self, engine: FaceRecognitionEngine, face_encoding: np.ndarray):
        name = engine.recognize_face(face_encoding)
        assert name == "Unknown"

    def test_recognizes_known_face(self, loaded_engine: FaceRecognitionEngine, face_encoding: np.ndarray):
        _face_rec_mock.compare_faces.return_value = [True]
        _face_rec_mock.face_distance.return_value = np.array([0.3])
        name = loaded_engine.recognize_face(face_encoding, tolerance=0.6)
        assert name == "Alice"

    def test_unknown_below_confidence_threshold(self, loaded_engine: FaceRecognitionEngine, face_encoding: np.ndarray):
        loaded_engine.known_faces[0].confidence_threshold = 0.99
        _face_rec_mock.compare_faces.return_value = [True]
        _face_rec_mock.face_distance.return_value = np.array([0.5])  # confidence = 0.5
        name = loaded_engine.recognize_face(face_encoding)
        assert name == "Unknown"


class TestRecognizeFaceWithConfidence:
    def test_returns_name_and_confidence(self, loaded_engine: FaceRecognitionEngine, face_encoding: np.ndarray):
        _face_rec_mock.compare_faces.return_value = [True]
        _face_rec_mock.face_distance.return_value = np.array([0.2])
        name, confidence = loaded_engine.recognize_face_with_confidence(face_encoding)
        assert name == "Alice"
        assert confidence == pytest.approx(0.8)

    def test_returns_zero_confidence_for_unknown(self, loaded_engine: FaceRecognitionEngine, face_encoding: np.ndarray):
        _face_rec_mock.compare_faces.return_value = [False]
        _face_rec_mock.face_distance.return_value = np.array([0.9])
        name, confidence = loaded_engine.recognize_face_with_confidence(face_encoding)
        assert name == "Unknown"
        assert confidence == 0.0

    def test_returns_unknown_when_not_loaded(self, engine: FaceRecognitionEngine, face_encoding: np.ndarray):
        name, confidence = engine.recognize_face_with_confidence(face_encoding)
        assert name == "Unknown"
        assert confidence == 0.0


class TestRemoveKnownFace:
    async def test_removes_existing_face(self, loaded_engine: FaceRecognitionEngine):
        with patch.object(loaded_engine, "save_face_database", return_value=True):
            result = await loaded_engine.remove_known_face("Alice")
        assert result is True
        assert "Alice" not in loaded_engine.face_names

    async def test_remove_nonexistent_still_succeeds(self, loaded_engine: FaceRecognitionEngine):
        with patch.object(loaded_engine, "save_face_database", return_value=True):
            result = await loaded_engine.remove_known_face("Nobody")
        assert result is True


class TestValidateDatabase:
    async def test_valid_database(self, loaded_engine: FaceRecognitionEngine):
        result = await loaded_engine.validate_database()
        assert result["is_valid"] is True
        assert result["errors"] == []

    async def test_detects_count_mismatch(self, loaded_engine: FaceRecognitionEngine):
        loaded_engine.face_names.append("Extra")
        result = await loaded_engine.validate_database()
        assert result["is_valid"] is False
