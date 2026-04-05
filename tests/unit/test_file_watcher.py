"""
Unit tests for blink_lens.core.file_watcher.FileWatcher.

All subprocess calls are mocked so this runs without root or loop devices.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from blink_lens.config.settings import Settings
from blink_lens.core.file_watcher import FileWatcher


@pytest.fixture
def watcher(settings: Settings) -> FileWatcher:
    return FileWatcher(settings)


def _make_completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class TestInit:
    def test_initial_state(self, watcher: FileWatcher):
        assert watcher._running is False
        assert watcher._pushed_files == set()
        assert watcher._pending_scan is False


class TestStateFile:
    def test_load_state_populates_pushed_files(self, watcher: FileWatcher, settings: Settings):
        state = {"pushed_files": ["DCIM/clip1.mp4", "DCIM/clip2.mp4"]}
        settings.watcher.state_file.parent.mkdir(parents=True, exist_ok=True)
        settings.watcher.state_file.write_text(json.dumps(state))
        watcher._load_state()
        assert "DCIM/clip1.mp4" in watcher._pushed_files

    def test_load_state_tolerates_missing_file(self, watcher: FileWatcher):
        # Should not raise even if state file doesn't exist
        watcher._load_state()
        assert watcher._pushed_files == set()

    def test_save_state_persists(self, watcher: FileWatcher, settings: Settings):
        watcher._pushed_files = {"clip1.mp4", "clip2.mp4"}
        settings.watcher.state_file.parent.mkdir(parents=True, exist_ok=True)
        watcher._save_state()
        data = json.loads(settings.watcher.state_file.read_text())
        assert set(data["pushed_files"]) == watcher._pushed_files

    def test_save_state_tolerates_permission_error(self, watcher: FileWatcher, tmp_path: Path):
        watcher.settings.watcher.state_file = Path("/root/no_permission/state.json")
        # Should not raise
        watcher._save_state()


class TestFindNewFiles:
    def test_returns_only_video_files(self, watcher: FileWatcher, tmp_path: Path):
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip1.mp4").write_bytes(b"")
        (mount / "clip2.avi").write_bytes(b"")
        (mount / "notes.txt").write_bytes(b"")

        new_files = watcher._find_new_files(mount)
        names = {f.name for f in new_files}
        assert "clip1.mp4" in names
        assert "clip2.avi" in names
        assert "notes.txt" not in names

    def test_excludes_already_pushed_files(self, watcher: FileWatcher, tmp_path: Path):
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip1.mp4").write_bytes(b"")
        watcher._pushed_files.add("clip1.mp4")

        new_files = watcher._find_new_files(mount)
        assert new_files == []


class TestTick:
    async def test_no_drive_file_logs_warning(self, watcher: FileWatcher, settings: Settings):
        # Drive image doesn't exist — should not raise
        await watcher._tick(settings.storage.virtual_drive_path)

    async def test_detects_mtime_change(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")
        settings.storage.virtual_drive_path = drive
        watcher._last_mtime = 0.0
        watcher._pending_scan = False

        await watcher._tick(drive)
        assert watcher._pending_scan is True

    async def test_triggers_scan_when_settled(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")
        settings.storage.virtual_drive_path = drive
        settings.watcher.settle_seconds = 0

        # Prime: note the mtime but don't scan yet
        await watcher._tick(drive)
        watcher._last_changed_at = 0.0  # simulate elapsed settle time

        with patch.object(watcher, "_scan_and_push", new_callable=AsyncMock) as mock_scan:
            await watcher._tick(drive)
            mock_scan.assert_called_once()


class TestPushFile:
    async def test_success_on_first_attempt(self, watcher: FileWatcher, tmp_path: Path):
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        with patch.object(
            watcher, "_run_command", new_callable=AsyncMock,
            return_value=_make_completed(0)
        ) as mock_cmd:
            result = await watcher._push_file(clip)

        assert result is True
        assert mock_cmd.call_count == 1

    async def test_retries_on_failure(self, watcher: FileWatcher, tmp_path: Path):
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        responses = [_make_completed(1, stderr="err"), _make_completed(1, stderr="err"), _make_completed(0)]

        with patch.object(watcher, "_run_command", new_callable=AsyncMock, side_effect=responses) as mock_cmd:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await watcher._push_file(clip)

        assert result is True
        assert mock_cmd.call_count == 3

    async def test_gives_up_after_max_retries(self, watcher: FileWatcher, tmp_path: Path):
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        with patch.object(
            watcher, "_run_command", new_callable=AsyncMock,
            return_value=_make_completed(1, stderr="always fails")
        ) as mock_cmd:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await watcher._push_file(clip)

        assert result is False
        assert mock_cmd.call_count == 3

    async def test_no_processor_host_returns_false(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        settings.watcher.processor_host = ""
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")
        result = await watcher._push_file(clip)
        assert result is False

    def test_ssh_opts_use_accept_new(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        """Verify StrictHostKeyChecking=no was replaced with accept-new."""
        import inspect
        src = inspect.getsource(watcher._push_file)
        assert "StrictHostKeyChecking=no" not in src
        assert "accept-new" in src
