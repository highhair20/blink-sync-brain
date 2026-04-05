"""
Unit tests for blink_lens.core.usb_gadget.USBGadgetManager.

All subprocess calls are mocked so these run without root or Pi hardware.
"""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from blink_lens.config.settings import Settings
from blink_lens.core.usb_gadget import USBGadgetManager


@pytest.fixture
def manager(settings: Settings) -> USBGadgetManager:
    return USBGadgetManager(settings)


def _ok(stdout: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout, "")


def _fail(stderr: str = "error") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 1, "", stderr)


class TestInit:
    def test_initial_state(self, manager: USBGadgetManager, settings: Settings):
        assert manager.virtual_drive_path == settings.storage.virtual_drive_path

    def test_scripts_dir_falls_back_to_production_path(self, settings: Settings):
        with patch("blink_lens.core.usb_gadget._find_scripts_dir", return_value=Path("/opt/blink-lens/scripts/drive")):
            m = USBGadgetManager(settings)
            assert m._scripts_dir == Path("/opt/blink-lens/scripts/drive")


class TestStartUsbGadget:
    async def test_returns_true_when_drive_exists(self, manager: USBGadgetManager, tmp_path: Path, settings: Settings):
        img = tmp_path / "virtual_drive.img"
        img.write_bytes(b"")
        settings.storage.virtual_drive_path = img
        manager.virtual_drive_path = img

        with patch.object(manager, "_run_command", new_callable=AsyncMock, return_value=_ok()):
            result = await manager.start_usb_gadget()

        assert result is True

    async def test_returns_false_when_drive_missing(self, manager: USBGadgetManager):
        # virtual_drive_path does not exist — should fail with actionable message, not try to create
        result = await manager.start_usb_gadget()
        assert result is False

    async def test_returns_false_on_script_failure(self, manager: USBGadgetManager, tmp_path: Path, settings: Settings):
        img = tmp_path / "virtual_drive.img"
        img.write_bytes(b"")
        settings.storage.virtual_drive_path = img
        manager.virtual_drive_path = img

        with patch.object(manager, "_run_command", new_callable=AsyncMock, return_value=_fail()):
            result = await manager.start_usb_gadget()
        assert result is False

    async def test_returns_false_on_exception(self, manager: USBGadgetManager, tmp_path: Path, settings: Settings):
        img = tmp_path / "virtual_drive.img"
        img.write_bytes(b"")
        settings.storage.virtual_drive_path = img
        manager.virtual_drive_path = img

        with patch.object(manager, "_run_command", new_callable=AsyncMock, side_effect=OSError("no such file")):
            result = await manager.start_usb_gadget()
        assert result is False


class TestStopUsbGadget:
    async def test_returns_true_on_success(self, manager: USBGadgetManager):
        with patch.object(manager, "_run_command", new_callable=AsyncMock, return_value=_ok()):
            result = await manager.stop_usb_gadget()
        assert result is True

    async def test_returns_false_on_failure(self, manager: USBGadgetManager):
        with patch.object(manager, "_run_command", new_callable=AsyncMock, return_value=_fail()):
            result = await manager.stop_usb_gadget()
        assert result is False

    async def test_returns_false_on_exception(self, manager: USBGadgetManager):
        with patch.object(manager, "_run_command", new_callable=AsyncMock, side_effect=RuntimeError("boom")):
            result = await manager.stop_usb_gadget()
        assert result is False


class TestGetStatus:
    async def test_returns_expected_keys(self, manager: USBGadgetManager):
        with patch.object(manager, "_get_drive_size", new_callable=AsyncMock, return_value=1024):
            with patch.object(manager, "_is_connected", new_callable=AsyncMock, return_value=True):
                status = await manager.get_status()

        assert "active" in status
        assert "virtual_drive_path" in status
        assert "drive_size" in status
        assert "configured" not in status
        assert "connected" not in status

    async def test_active_reflects_lsmod(self, manager: USBGadgetManager):
        with patch.object(manager, "_get_drive_size", new_callable=AsyncMock, return_value=0):
            with patch.object(manager, "_run_command", new_callable=AsyncMock,
                              return_value=_ok("g_mass_storage  12345  0\n")):
                status = await manager.get_status()
        assert status["active"] is True


class TestIsConnected:
    async def test_true_when_module_loaded(self, manager: USBGadgetManager):
        with patch.object(manager, "_run_command", new_callable=AsyncMock,
                          return_value=_ok("g_mass_storage  12345  0\n")):
            assert await manager._is_connected() is True

    async def test_false_when_module_absent(self, manager: USBGadgetManager):
        with patch.object(manager, "_run_command", new_callable=AsyncMock,
                          return_value=_ok("dwc2  99999  0\n")):
            assert await manager._is_connected() is False


class TestGetDriveSize:
    async def test_returns_file_size(self, manager: USBGadgetManager, tmp_path: Path, settings: Settings):
        img = tmp_path / "drive.img"
        img.write_bytes(b"x" * 512)
        settings.storage.virtual_drive_path = img
        manager.virtual_drive_path = img
        assert await manager._get_drive_size() == 512

    async def test_returns_zero_when_missing(self, manager: USBGadgetManager):
        assert await manager._get_drive_size() == 0


