"""
Unit tests for blink_lens.drive.main CLI entry point.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from blink_lens.drive.main import _run


def _patch_manager(start=True, stop=True, status=None):
    """Return a context manager that patches USBGadgetManager."""
    if status is None:
        status = {"active": True, "connected": True}
    mock = MagicMock()
    mock.start_usb_gadget = AsyncMock(return_value=start)
    mock.stop_usb_gadget = AsyncMock(return_value=stop)
    mock.get_status = AsyncMock(return_value=status)
    return patch("blink_lens.drive.main.USBGadgetManager", return_value=mock), mock


class TestStartCommand:
    async def test_returns_0_on_success(self):
        ctx, mock = _patch_manager(start=True)
        with ctx:
            with patch("sys.argv", ["blink-drive", "start"]):
                code = await _run()
        assert code == 0
        mock.start_usb_gadget.assert_called_once()

    async def test_returns_1_on_failure(self):
        ctx, mock = _patch_manager(start=False)
        with ctx:
            with patch("sys.argv", ["blink-drive", "start"]):
                code = await _run()
        assert code == 1


class TestStopCommand:
    async def test_returns_0_on_success(self):
        ctx, mock = _patch_manager(stop=True)
        with ctx:
            with patch("sys.argv", ["blink-drive", "stop"]):
                code = await _run()
        assert code == 0
        mock.stop_usb_gadget.assert_called_once()

    async def test_returns_1_on_failure(self):
        ctx, mock = _patch_manager(stop=False)
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
        out = capsys.readouterr().out
        assert out.strip()  # something was printed


class TestWatchCommand:
    async def test_calls_watcher_start(self):
        ctx, _ = _patch_manager()
        mock_watcher = MagicMock()
        mock_watcher.start = AsyncMock()
        with ctx:
            with patch("blink_lens.core.file_watcher.FileWatcher", return_value=mock_watcher):
                with patch("sys.argv", ["blink-drive", "watch"]):
                    code = await _run()
        assert code == 0
        mock_watcher.start.assert_called_once()


class TestNoCommand:
    async def test_returns_2(self):
        ctx, _ = _patch_manager()
        with ctx:
            with patch("sys.argv", ["blink-drive"]):
                code = await _run()
        assert code == 2
