"""
Unit tests for blink_lens.drive.main CLI entry point.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from blink_lens.drive.main import _run


def _patch_manager(start=True, stop=True, status=None):
    """Return a context manager that patches USBGadgetManager and Settings.validate."""
    if status is None:
        status = {"active": True, "connected": True}
    mock = MagicMock()
    mock.start_usb_gadget = AsyncMock(return_value=start)
    mock.stop_usb_gadget = AsyncMock(return_value=stop)
    mock.get_status = AsyncMock(return_value=status)
    # Patch both USBGadgetManager and Settings.validate so individual tests
    # don't fail due to non-existent paths in the default Settings() object.
    from contextlib import ExitStack
    from unittest.mock import patch as _patch

    class _MultiPatch:
        def __enter__(self):
            self._stack = ExitStack()
            self._stack.enter_context(_patch("blink_lens.drive.main.USBGadgetManager", return_value=mock))
            self._stack.enter_context(_patch("blink_lens.drive.main.Settings.validate", return_value=[]))
            return self

        def __exit__(self, *args):
            self._stack.__exit__(*args)

    return _MultiPatch(), mock


def _as_root():
    """Patch os.geteuid to simulate running as root."""
    return patch("blink_lens.drive.main.os.geteuid", return_value=0)


def _as_non_root():
    """Patch os.geteuid to simulate running as non-root."""
    return patch("blink_lens.drive.main.os.geteuid", return_value=1000)


class TestRootCheck:
    async def test_start_as_non_root_returns_1(self):
        with _as_non_root():
            with patch("sys.argv", ["blink-drive", "start"]):
                code = await _run()
        assert code == 1

    async def test_stop_as_non_root_returns_1(self):
        with _as_non_root():
            with patch("sys.argv", ["blink-drive", "stop"]):
                code = await _run()
        assert code == 1

    async def test_watch_as_non_root_returns_1(self):
        with _as_non_root():
            with patch("sys.argv", ["blink-drive", "watch"]):
                code = await _run()
        assert code == 1

    async def test_status_does_not_require_root(self):
        ctx, _ = _patch_manager()
        with _as_non_root():
            with ctx:
                with patch("sys.argv", ["blink-drive", "status"]):
                    code = await _run()
        assert code == 0


class TestConfigValidation:
    async def test_returns_1_on_validation_errors(self):
        ctx, _ = _patch_manager()
        with _as_root():
            with ctx:
                with patch("blink_lens.drive.main.Settings.validate", return_value=["Port out of range"]):
                    with patch("sys.argv", ["blink-drive", "start"]):
                        code = await _run()
        assert code == 1

    async def test_proceeds_when_valid(self):
        ctx, mock = _patch_manager(start=True)
        with _as_root():
            with ctx:
                with patch("blink_lens.drive.main.Settings.validate", return_value=[]):
                    with patch("sys.argv", ["blink-drive", "start"]):
                        code = await _run()
        assert code == 0


class TestStartCommand:
    async def test_returns_0_on_success(self):
        ctx, mock = _patch_manager(start=True)
        with _as_root():
            with ctx:
                with patch("sys.argv", ["blink-drive", "start"]):
                    code = await _run()
        assert code == 0
        mock.start_usb_gadget.assert_called_once()

    async def test_returns_1_on_failure(self):
        ctx, mock = _patch_manager(start=False)
        with _as_root():
            with ctx:
                with patch("sys.argv", ["blink-drive", "start"]):
                    code = await _run()
        assert code == 1


class TestStopCommand:
    async def test_returns_0_on_success(self):
        ctx, mock = _patch_manager(stop=True)
        with _as_root():
            with ctx:
                with patch("sys.argv", ["blink-drive", "stop"]):
                    code = await _run()
        assert code == 0
        mock.stop_usb_gadget.assert_called_once()

    async def test_returns_1_on_failure(self):
        ctx, mock = _patch_manager(stop=False)
        with _as_root():
            with ctx:
                with patch("sys.argv", ["blink-drive", "stop"]):
                    code = await _run()
        assert code == 1


class TestStatusCommand:
    async def test_returns_0_and_prints(self, capsys):
        ctx, mock = _patch_manager()
        with ctx:
            with patch("sys.argv", ["blink-drive", "status"]):
                code = await _run()
        assert code == 0
        mock.get_status.assert_called_once()
        assert capsys.readouterr().out.strip()


class TestWatchCommand:
    async def test_calls_watcher_start(self):
        ctx, _ = _patch_manager()
        mock_watcher = MagicMock()
        mock_watcher.start = AsyncMock()
        with _as_root():
            with ctx:
                with patch("blink_lens.core.file_watcher.FileWatcher", return_value=mock_watcher):
                    with patch("sys.argv", ["blink-drive", "watch"]):
                        code = await _run()
        assert code == 0
        mock_watcher.start.assert_called_once()

    async def test_returns_1_on_missing_processor_host(self):
        ctx, _ = _patch_manager()
        mock_watcher = MagicMock()
        mock_watcher.start = AsyncMock(side_effect=ValueError("processor_host not configured"))
        with _as_root():
            with ctx:
                with patch("blink_lens.core.file_watcher.FileWatcher", return_value=mock_watcher):
                    with patch("sys.argv", ["blink-drive", "watch"]):
                        code = await _run()
        assert code == 1

    async def test_returns_1_on_missing_ssh_key(self):
        ctx, _ = _patch_manager()
        mock_watcher = MagicMock()
        mock_watcher.start = AsyncMock(side_effect=FileNotFoundError("SSH key not found"))
        with _as_root():
            with ctx:
                with patch("blink_lens.core.file_watcher.FileWatcher", return_value=mock_watcher):
                    with patch("sys.argv", ["blink-drive", "watch"]):
                        code = await _run()
        assert code == 1

    async def test_returns_1_on_unsafe_ssh_key_permissions(self):
        ctx, _ = _patch_manager()
        mock_watcher = MagicMock()
        mock_watcher.start = AsyncMock(side_effect=PermissionError("unsafe permissions"))
        with _as_root():
            with ctx:
                with patch("blink_lens.core.file_watcher.FileWatcher", return_value=mock_watcher):
                    with patch("sys.argv", ["blink-drive", "watch"]):
                        code = await _run()
        assert code == 1


class TestNoCommand:
    async def test_returns_2(self):
        ctx, _ = _patch_manager()
        with ctx:
            with patch("sys.argv", ["blink-drive"]):
                code = await _run()
        assert code == 2
