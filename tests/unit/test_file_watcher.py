"""
Unit tests for blink_lens.core.file_watcher.FileWatcher.

All subprocess calls are mocked so this runs without root or loop devices.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
        watcher._load_state()
        assert watcher._pushed_files == set()

    def test_save_state_persists(self, watcher: FileWatcher, settings: Settings):
        watcher._pushed_files = {"clip1.mp4", "clip2.mp4"}
        settings.watcher.state_file.parent.mkdir(parents=True, exist_ok=True)
        watcher._save_state()
        data = json.loads(settings.watcher.state_file.read_text())
        assert set(data["pushed_files"]) == watcher._pushed_files

    def test_save_state_tolerates_permission_error(self, watcher: FileWatcher):
        watcher.settings.watcher.state_file = Path("/root/no_permission/state.json")
        watcher._save_state()  # should not raise

    def test_save_state_sets_600_permissions(self, watcher: FileWatcher, settings: Settings):
        watcher._pushed_files = {"clip1.mp4"}
        settings.watcher.state_file.parent.mkdir(parents=True, exist_ok=True)
        watcher._save_state()
        mode = settings.watcher.state_file.stat().st_mode & 0o777
        assert mode == 0o600


class TestFindNewFiles:
    def test_returns_only_video_files(self, watcher: FileWatcher, tmp_path: Path):
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip1.mp4").write_bytes(b"")
        (mount / "clip2.avi").write_bytes(b"")
        (mount / "notes.txt").write_bytes(b"")

        names = {f.name for f in watcher._find_new_files(mount)}
        assert "clip1.mp4" in names
        assert "clip2.avi" in names
        assert "notes.txt" not in names

    def test_excludes_already_pushed_files(self, watcher: FileWatcher, tmp_path: Path):
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip1.mp4").write_bytes(b"")
        watcher._pushed_files.add("clip1.mp4")

        assert watcher._find_new_files(mount) == []

    def test_includes_previously_failed_files(self, watcher: FileWatcher, tmp_path: Path):
        """Files that failed to push must reappear so they are retried."""
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip.mp4").write_bytes(b"")
        # Not in _pushed_files → should appear as new
        assert len(watcher._find_new_files(mount)) == 1


class TestTick:
    async def test_no_drive_file_logs_warning(self, watcher: FileWatcher, settings: Settings):
        await watcher._tick(settings.storage.virtual_drive_path)  # should not raise

    async def test_detects_mtime_change(self, watcher: FileWatcher, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")
        watcher._last_mtime = 0.0

        await watcher._tick(drive)
        assert watcher._pending_scan is True

    async def test_triggers_scan_when_settled(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")
        settings.storage.virtual_drive_path = drive
        settings.watcher.settle_seconds = 0

        await watcher._tick(drive)
        watcher._last_changed_at = 0.0  # simulate elapsed settle time

        with patch.object(watcher, "_scan_and_push", new_callable=AsyncMock) as mock_scan:
            await watcher._tick(drive)
            mock_scan.assert_called_once()


class TestScanAndPush:
    async def test_logs_warning_when_mount_fails(self, watcher: FileWatcher, tmp_path: Path):
        watcher.settings.watcher.shadow_mount_point = tmp_path / "shadow"

        with patch.object(watcher, "_mount_shadow", new_callable=AsyncMock, return_value=False):
            with patch.object(watcher.logger, "warning") as mock_warn:
                await watcher._scan_and_push()

        assert mock_warn.called
        msg = mock_warn.call_args[0][0]
        assert "retried" in msg.lower() or "retry" in msg.lower()

    async def test_failed_push_not_added_to_pushed_files(self, watcher: FileWatcher, tmp_path: Path):
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip.mp4").write_bytes(b"")
        watcher.settings.watcher.shadow_mount_point = mount

        with patch.object(watcher, "_mount_shadow", new_callable=AsyncMock, return_value=True):
            with patch.object(watcher, "_unmount_shadow", new_callable=AsyncMock):
                with patch.object(watcher, "_push_file", new_callable=AsyncMock, return_value=False):
                    await watcher._scan_and_push()

        assert "clip.mp4" not in watcher._pushed_files

    async def test_successful_push_added_to_pushed_files(self, watcher: FileWatcher, tmp_path: Path):
        mount = tmp_path / "shadow"
        mount.mkdir()
        (mount / "clip.mp4").write_bytes(b"")
        watcher.settings.watcher.shadow_mount_point = mount

        with patch.object(watcher, "_mount_shadow", new_callable=AsyncMock, return_value=True):
            with patch.object(watcher, "_unmount_shadow", new_callable=AsyncMock):
                with patch.object(watcher, "_push_file", new_callable=AsyncMock, return_value=True):
                    await watcher._scan_and_push()

        assert "clip.mp4" in watcher._pushed_files


class TestPushFile:
    async def test_success_on_first_attempt(self, watcher: FileWatcher, tmp_path: Path):
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        with patch.object(watcher, "_run_command", new_callable=AsyncMock,
                          return_value=_make_completed(0)) as mock_cmd:
            result = await watcher._push_file(clip)

        assert result is True
        assert mock_cmd.call_count == 1

    async def test_retries_on_failure(self, watcher: FileWatcher, tmp_path: Path):
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        responses = [_make_completed(1, stderr="err"), _make_completed(1, stderr="err"), _make_completed(0)]

        with patch.object(watcher, "_run_command", new_callable=AsyncMock, side_effect=responses):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await watcher._push_file(clip)

        assert result is True

    async def test_gives_up_after_max_retries(self, watcher: FileWatcher, tmp_path: Path):
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        with patch.object(watcher, "_run_command", new_callable=AsyncMock,
                          return_value=_make_completed(1, stderr="always fails")):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await watcher._push_file(clip)

        assert result is False

    async def test_no_processor_host_returns_false(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        settings.watcher.processor_host = ""
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")
        assert await watcher._push_file(clip) is False

    async def test_rsync_error_message_is_user_friendly(self, watcher: FileWatcher, tmp_path: Path):
        """Exit code 5 should produce a human-readable SSH connection error."""
        clip = tmp_path / "clip.mp4"
        clip.write_bytes(b"")

        with patch.object(watcher, "_run_command", new_callable=AsyncMock,
                          return_value=_make_completed(5, stderr="Connection refused")):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with patch.object(watcher.logger, "warning") as mock_warn:
                    await watcher._push_file(clip)

        # At least one warning should mention Pi #2
        reasons = [str(call) for call in mock_warn.call_args_list]
        assert any("Pi #2" in r for r in reasons)

    def test_ssh_opts_use_accept_new(self, watcher: FileWatcher):
        import inspect
        src = inspect.getsource(watcher._push_file)
        assert "StrictHostKeyChecking=no" not in src
        assert "accept-new" in src


class TestStartValidation:
    async def test_raises_if_processor_host_not_set(self, watcher: FileWatcher, settings: Settings):
        settings.watcher.processor_host = ""
        with pytest.raises(ValueError, match="processor_host"):
            await watcher.start()

    async def test_raises_if_ssh_key_missing(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        settings.watcher.ssh_key_path = tmp_path / "nonexistent_key"
        with pytest.raises(FileNotFoundError, match="SSH key not found"):
            await watcher.start()

    async def test_no_error_if_ssh_key_not_configured(self, watcher: FileWatcher, settings: Settings):
        settings.watcher.ssh_key_path = None
        with patch.object(watcher, "_watch_loop", new_callable=AsyncMock):
            await watcher.start()

    async def test_no_error_if_ssh_key_exists_with_correct_perms(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        key = tmp_path / "id_rsa"
        key.write_bytes(b"")
        key.chmod(0o600)
        settings.watcher.ssh_key_path = key
        with patch.object(watcher, "_watch_loop", new_callable=AsyncMock):
            await watcher.start()

    async def test_raises_if_ssh_key_has_unsafe_permissions(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        key = tmp_path / "id_rsa"
        key.write_bytes(b"")
        key.chmod(0o644)
        settings.watcher.ssh_key_path = key
        with pytest.raises(PermissionError, match="unsafe permissions"):
            await watcher.start()


class TestHeartbeat:
    async def test_heartbeat_logged_after_interval(self, watcher: FileWatcher, settings: Settings, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")
        settings.storage.virtual_drive_path = drive
        settings.watcher.poll_interval = 0

        call_count = 0

        async def fake_sleep(_):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                watcher._running = False

        with patch("asyncio.sleep", side_effect=fake_sleep):
            with patch.object(watcher, "_tick", new_callable=AsyncMock):
                # Force heartbeat by setting last_heartbeat far in the past
                with patch("asyncio.get_event_loop") as mock_loop:
                    mock_loop.return_value.time.side_effect = [0.0, 999.0, 999.0]
                    with patch.object(watcher.logger, "info") as mock_info:
                        watcher._running = True
                        watcher._last_heartbeat_at = 0.0
                        await watcher._watch_loop()

        logged_events = [c[0][0] for c in mock_info.call_args_list if c[0]]
        assert any("healthy" in e.lower() for e in logged_events)


class TestLoopDeviceParsing:
    async def test_handles_valid_losetup_show_output(self, watcher: FileWatcher, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")

        responses = [
            _make_completed(0, stdout="/dev/loop0\n"),  # losetup --show -fP
            _make_completed(0),                         # mount
        ]

        with patch.object(watcher, "_run_command", new_callable=AsyncMock, side_effect=responses):
            with patch("pathlib.Path.exists", return_value=True):
                result = await watcher._mount_shadow(drive, tmp_path / "mnt")

        assert result is True

    async def test_handles_malformed_losetup_output(self, watcher: FileWatcher, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")

        with patch.object(watcher, "_run_command", new_callable=AsyncMock,
                          return_value=_make_completed(0, stdout="malformed\n")):
            result = await watcher._mount_shadow(drive, tmp_path / "mnt")

        assert result is False

    async def test_losetup_failure_returns_false(self, watcher: FileWatcher, tmp_path: Path):
        drive = tmp_path / "drive.img"
        drive.write_bytes(b"")

        with patch.object(watcher, "_run_command", new_callable=AsyncMock,
                          return_value=_make_completed(1, stderr="no free loop devices")):
            result = await watcher._mount_shadow(drive, tmp_path / "mnt")

        assert result is False
