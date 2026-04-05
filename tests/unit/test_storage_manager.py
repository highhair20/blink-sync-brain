"""
Unit tests for blink_lens.core.storage_manager.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from blink_lens.config.settings import Settings
from blink_lens.core.storage_manager import StorageManager


@pytest.fixture
def manager(settings: Settings) -> StorageManager:
    settings.storage.video_directory.mkdir(parents=True, exist_ok=True)
    settings.storage.results_directory.mkdir(parents=True, exist_ok=True)
    return StorageManager(settings)


def _write_file(path: Path, age_days: int = 0) -> None:
    """Write a small file and backdate its mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * 1024)
    if age_days:
        mtime = (datetime.now() - timedelta(days=age_days)).timestamp()
        import os
        os.utime(path, (mtime, mtime))


class TestStorageManagerInit:
    def test_init(self, manager: StorageManager):
        assert manager.is_monitoring is False


class TestGetFileList:
    async def test_empty_directory_returns_empty(self, manager: StorageManager):
        result = await manager.get_file_list()
        assert result == []

    async def test_lists_files(self, manager: StorageManager, settings: Settings):
        video_dir = settings.storage.video_directory
        _write_file(video_dir / "clip1.mp4")
        _write_file(video_dir / "clip2.mp4")
        result = await manager.get_file_list()
        names = [f["name"] for f in result]
        assert "clip1.mp4" in names
        assert "clip2.mp4" in names

    async def test_sorted_newest_first(self, manager: StorageManager, settings: Settings):
        video_dir = settings.storage.video_directory
        _write_file(video_dir / "old.mp4", age_days=5)
        _write_file(video_dir / "new.mp4", age_days=0)
        result = await manager.get_file_list()
        assert result[0]["name"] == "new.mp4"


class TestCleanupOldFiles:
    async def test_dry_run_does_not_delete(self, manager: StorageManager, settings: Settings):
        video_dir = settings.storage.video_directory
        _write_file(video_dir / "old.mp4", age_days=60)
        settings.storage.retention_days = 30

        result = await manager.cleanup_old_files(dry_run=True)
        assert result["files_deleted"] >= 1
        assert (video_dir / "old.mp4").exists()

    async def test_deletes_old_files(self, manager: StorageManager, settings: Settings):
        video_dir = settings.storage.video_directory
        old_file = video_dir / "stale.mp4"
        _write_file(old_file, age_days=60)
        settings.storage.retention_days = 30

        result = await manager.cleanup_old_files(dry_run=False)
        assert result["files_deleted"] >= 1
        assert not old_file.exists()

    async def test_retains_recent_files(self, manager: StorageManager, settings: Settings):
        video_dir = settings.storage.video_directory
        recent = video_dir / "recent.mp4"
        _write_file(recent, age_days=1)
        settings.storage.retention_days = 30

        await manager.cleanup_old_files(dry_run=False)
        assert recent.exists()


class TestMoveAndCopyFile:
    async def test_move_file(self, manager: StorageManager, tmp_path: Path):
        src = tmp_path / "src.txt"
        src.write_bytes(b"hello")
        dst = tmp_path / "dst" / "moved.txt"
        ok = await manager.move_file(src, dst)
        assert ok is True
        assert dst.exists()
        assert not src.exists()

    async def test_copy_file(self, manager: StorageManager, tmp_path: Path):
        src = tmp_path / "src.txt"
        src.write_bytes(b"world")
        dst = tmp_path / "dst" / "copy.txt"
        ok = await manager.copy_file(src, dst)
        assert ok is True
        assert dst.exists()
        assert src.exists()


class TestDeleteFile:
    async def test_deletes_existing_file(self, manager: StorageManager, tmp_path: Path):
        f = tmp_path / "todelete.txt"
        f.write_bytes(b"bye")
        ok = await manager.delete_file(f)
        assert ok is True
        assert not f.exists()

    async def test_returns_false_for_missing_file(self, manager: StorageManager, tmp_path: Path):
        ok = await manager.delete_file(tmp_path / "nope.txt")
        assert ok is False
