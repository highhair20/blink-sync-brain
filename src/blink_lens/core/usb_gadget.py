"""
USB Gadget Manager for Raspberry Pi Zero 2 W.

This module manages the USB gadget mode functionality, allowing the Pi Zero 2 W
to act as a virtual USB storage device for the Blink Sync Module.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

import structlog

from blink_lens.config.settings import Settings
from blink_lens.core.utils import run_command as _run_command_impl


def _find_scripts_dir() -> Path:
    """Locate the drive scripts directory.

    Checks for a development install (scripts/ relative to the repo root)
    before falling back to the standard production deploy path.
    """
    candidate = Path(__file__).parents[3] / "scripts" / "drive"
    if candidate.is_dir():
        return candidate
    return Path("/opt/blink-lens/scripts/drive")


class USBGadgetManager:
    """
    Manages USB gadget mode for Raspberry Pi Zero 2 W.

    This class handles the configuration and management of the Pi Zero 2 W
    operating in USB gadget mode as a mass storage device.
    """

    def __init__(self, settings: Settings):
        """Initialize the USB Gadget Manager."""
        self.settings = settings
        self.logger = structlog.get_logger()
        self.virtual_drive_path: Path = settings.storage.virtual_drive_path
        self._scripts_dir = _find_scripts_dir()

    async def start_usb_gadget(self) -> bool:
        """
        Start Storage Mode: load g_mass_storage so Blink can write to the virtual drive.

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            self.logger.info("Starting USB gadget (Storage Mode)")

            if not self.virtual_drive_path.exists():
                self.logger.error(
                    "Virtual drive image not found — run the installer first",
                    path=str(self.virtual_drive_path),
                    hint="sudo /opt/blink-lens/scripts/drive/install.sh",
                )
                return False

            result = await self._run_command(
                [str(self._scripts_dir / "start_storage_mode.sh")]
            )
            if result.returncode != 0:
                self.logger.error("Failed to start Storage Mode", error=result.stderr)
                return False
            self.logger.info("Storage Mode active")
            return True

        except Exception as e:
            self.logger.error("Failed to start USB gadget", error=str(e))
            return False

    async def stop_usb_gadget(self) -> bool:
        """
        Stop Storage Mode: unload g_mass_storage.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            self.logger.info("Stopping USB gadget (unloading g_mass_storage)")
            result = await self._run_command(["modprobe", "-r", "g_mass_storage"])
            if result.returncode != 0:
                self.logger.error("Failed to unload g_mass_storage", error=result.stderr)
                return False
            self.logger.info("USB gadget stopped")
            return True

        except Exception as e:
            self.logger.error("Failed to stop USB gadget", error=str(e))
            return False

    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the USB gadget.

        Returns live system state — safe to call from a separate CLI invocation.
        """
        connected = await self._is_connected()
        drive_size = await self._get_drive_size()
        return {
            # Live: query lsmod rather than cached in-memory flags so that
            # `blink-drive status` reflects reality after a reboot.
            "active": connected,
            "configured": connected,
            "connected": connected,
            "virtual_drive_path": str(self.virtual_drive_path),
            "drive_size": drive_size,
        }

    async def _is_connected(self) -> bool:
        """Check if g_mass_storage is loaded (Storage Mode active)."""
        result = await self._run_command(["lsmod"])
        return "g_mass_storage" in result.stdout

    async def _get_drive_size(self) -> int:
        """Get the total size of the virtual drive in bytes."""
        try:
            return self.virtual_drive_path.stat().st_size
        except Exception as e:
            self.logger.error("Failed to get drive size", error=str(e))
            return 0

    async def _run_command(self, cmd: list) -> subprocess.CompletedProcess:
        """Run a command asynchronously and return a CompletedProcess."""
        return await _run_command_impl(cmd)
