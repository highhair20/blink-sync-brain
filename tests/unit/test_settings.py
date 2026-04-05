"""
Unit tests for blink_lens.config.settings.
"""

import os
from pathlib import Path

import pytest
import yaml

from blink_lens.config.settings import (
    FaceRecognitionSettings,
    LoggingSettings,
    NetworkSettings,
    NotificationSettings,
    ProcessingSettings,
    Settings,
    StorageSettings,
    WatcherSettings,
)


class TestSettingsDefaults:
    def test_default_storage_paths(self):
        s = StorageSettings()
        assert s.virtual_drive_path == Path("/var/blink_storage/virtual_drive.img")
        assert s.video_directory == Path("/var/blink_storage/videos")
        assert s.retention_days == 30
        assert s.cleanup_threshold == 80.0

    def test_default_processing(self):
        s = ProcessingSettings()
        assert s.frame_skip == 5
        assert s.max_concurrent_videos == 2

    def test_default_face_recognition(self):
        s = FaceRecognitionSettings()
        assert 0.0 <= s.confidence_threshold <= 1.0
        assert 0.0 <= s.tolerance <= 1.0

    def test_default_notifications(self):
        s = NotificationSettings()
        assert s.enable_notifications is True
        assert s.email_enabled is False
        assert s.pushbullet_enabled is False
        assert s.webhook_enabled is False
        assert "unknown_face" in s.notification_types

    def test_default_watcher(self):
        s = WatcherSettings()
        assert s.poll_interval == 5
        assert s.settle_seconds == 10
        assert s.rsync_timeout == 30

    def test_default_network(self):
        s = NetworkSettings()
        assert 1 <= s.port <= 65535

    def test_default_logging(self):
        s = LoggingSettings()
        assert s.level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_settings_initialises(self):
        s = Settings()
        assert s.app_name == "Blink Lens"
        assert isinstance(s.storage, StorageSettings)
        assert isinstance(s.watcher, WatcherSettings)


class TestSettingsEnvOverrides:
    def test_video_directory_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("VIDEO_DIRECTORY", str(tmp_path / "vids"))
        s = Settings()
        assert s.storage.video_directory == tmp_path / "vids"

    def test_processor_host_from_env(self, monkeypatch):
        monkeypatch.setenv("PROCESSOR_HOST", "10.0.0.5")
        s = Settings()
        assert s.watcher.processor_host == "10.0.0.5"

    def test_face_confidence_from_env(self, monkeypatch):
        monkeypatch.setenv("FACE_CONFIDENCE_THRESHOLD", "0.75")
        s = Settings()
        assert s.face_recognition.confidence_threshold == pytest.approx(0.75)

    def test_log_level_from_env(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        s = Settings()
        assert s.logging.level == "DEBUG"

    def test_notification_smtp_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATION_SMTP_HOST", "mail.example.com")
        monkeypatch.setenv("NOTIFICATION_SMTP_PORT", "465")
        monkeypatch.setenv("NOTIFICATION_EMAIL_FROM", "from@example.com")
        monkeypatch.setenv("NOTIFICATION_EMAIL_TO", "to@example.com")
        s = Settings()
        assert s.notifications.smtp_host == "mail.example.com"
        assert s.notifications.smtp_port == 465
        assert s.notifications.email_from == "from@example.com"
        assert s.notifications.email_to == "to@example.com"

    def test_pushbullet_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATION_PUSHBULLET_API_KEY", "secret-key")
        s = Settings()
        assert s.notifications.pushbullet_api_key == "secret-key"

    def test_webhook_url_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTIFICATION_WEBHOOK_URL", "https://hooks.example.com/xyz")
        s = Settings()
        assert s.notifications.webhook_url == "https://hooks.example.com/xyz"


class TestSettingsFromFile:
    def test_load_from_yaml(self, tmp_path):
        config = {
            "storage": {"retention_days": 7, "cleanup_threshold": 90.0},
            "processing": {"frame_skip": 10},
            "watcher": {"processor_host": "192.168.1.99", "poll_interval": 15},
        }
        config_path = tmp_path / "test.yaml"
        config_path.write_text(yaml.dump(config))

        s = Settings.from_file(config_path)
        assert s.storage.retention_days == 7
        assert s.storage.cleanup_threshold == 90.0
        assert s.processing.frame_skip == 10
        assert s.watcher.processor_host == "192.168.1.99"
        assert s.watcher.poll_interval == 15

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            Settings.from_file(tmp_path / "nonexistent.yaml")


class TestSettingsValidation:
    def test_valid_settings_no_errors(self, tmp_path):
        s = Settings()
        s.storage.virtual_drive_path = tmp_path / "drive.img"
        # Parent dir (tmp_path) exists — no storage error
        errors = s.validate()
        # Filter out path errors since /var/blink_storage may not exist in test env
        non_path_errors = [e for e in errors if "does not exist" not in e]
        assert non_path_errors == []

    def test_invalid_frame_skip(self):
        s = Settings()
        s.processing.frame_skip = 0
        errors = s.validate()
        assert any("frame skip" in e.lower() for e in errors)

    def test_invalid_confidence_threshold(self):
        s = Settings()
        s.face_recognition.confidence_threshold = 1.5
        errors = s.validate()
        assert any("confidence" in e.lower() for e in errors)

    def test_invalid_port(self):
        s = Settings()
        s.network.port = 99999
        errors = s.validate()
        assert any("port" in e.lower() for e in errors)

    def test_invalid_log_level(self):
        s = Settings()
        s.logging.level = "VERBOSE"
        errors = s.validate()
        assert any("log level" in e.lower() for e in errors)


class TestSettingsToDict:
    def test_to_dict_round_trip(self, tmp_path):
        s = Settings()
        d = s.to_dict()
        assert "storage" in d
        assert "processing" in d
        assert "face_recognition" in d
        assert "notifications" in d
        assert "watcher" in d
        assert "network" in d
        assert "logging" in d

    def test_save_and_reload(self, tmp_path):
        s = Settings()
        s.storage.retention_days = 14
        config_path = tmp_path / "out.yaml"
        s.save_to_file(config_path)

        s2 = Settings.from_file(config_path)
        assert s2.storage.retention_days == 14
