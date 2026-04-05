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
        self.is_configured = False
        self.is_active = False
        self._scripts_dir = _find_scripts_dir()

    async def start_usb_gadget(self) -> bool:
        """
        Start Storage Mode: load g_mass_storage so Blink can write to the virtual drive.

        Creates the virtual drive image if it does not already exist.

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            self.logger.info("Starting USB gadget (Storage Mode)")

            if not self.virtual_drive_path.exists():
                self.logger.info("Virtual drive image not found, creating it")
                if not await self._create_virtual_drive():
                    return False

            result = await self._run_command(
                ["sudo", str(self._scripts_dir / "start_storage_mode.sh")]
            )
            if result.returncode != 0:
                self.logger.error("Failed to start Storage Mode", error=result.stderr)
                return False
            self.is_configured = True
            self.is_active = True
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
            result = await self._run_command(["sudo", "modprobe", "-r", "g_mass_storage"])
            if result.returncode != 0:
                self.logger.error("Failed to unload g_mass_storage", error=result.stderr)
                return False
            self.is_active = False
            self.logger.info("USB gadget stopped")
            return True

        except Exception as e:
            self.logger.error("Failed to stop USB gadget", error=str(e))
            return False

    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the USB gadget.

        Returns:
            Dict containing status information
        """
        return {
            "configured": self.is_configured,
            "active": self.is_active,
            "virtual_drive_path": str(self.virtual_drive_path),
            "drive_size": await self._get_drive_size(),
            "connected": await self._is_connected(),
        }

    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                return "Raspberry Pi" in f.read()
        except Exception:
            return False

    async def _create_virtual_drive(self) -> bool:
        """Create the virtual drive image using create-virtual-storage.sh."""
        self.logger.info("Creating virtual drive", path=str(self.virtual_drive_path))
        result = await self._run_command(
            ["sudo", str(self._scripts_dir / "create-virtual-storage.sh")]
        )
        if result.returncode != 0:
            self.logger.error("Failed to create virtual drive", error=result.stderr)
            return False
        self.logger.info("Virtual drive created successfully")
        return True

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
