"""
USB Gadget Manager for Raspberry Pi Zero 2 W.

This module manages the USB gadget mode functionality, allowing the Pi Zero 2 W
to act as a virtual USB storage device for the Blink Sync Module.
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

import structlog
import psutil

from blink_lens.config.settings import Settings


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

        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            self.logger.info("Starting USB gadget (Storage Mode)")
            result = await self._run_command(
                ["sudo", str(self._scripts_dir / "start_storage_mode.sh")]
            )
            if result.returncode != 0:
                self.logger.error("Failed to start Storage Mode", error=result.stderr)
                return False
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
            "free_space": await self._get_free_space(),
            "connected": await self._is_connected(),
        }

    async def monitor_storage(self) -> None:
        """
        Monitor storage usage and manage space.

        This method runs continuously to monitor the virtual drive
        and manage storage space by removing old files when needed.
        """
        self.logger.info("Starting storage monitoring")

        while self.is_active:
            try:
                free_space = await self._get_free_space()
                total_space = await self._get_drive_size()
                usage_percent = ((total_space - free_space) / total_space) * 100

                self.logger.debug(
                    "Storage status",
                    free_space_gb=free_space / (1024**3),
                    usage_percent=usage_percent,
                )

                if usage_percent > self.settings.storage.cleanup_threshold:
                    await self._cleanup_old_files()

                await asyncio.sleep(self.settings.storage.monitor_interval)

            except Exception as e:
                self.logger.error("Error in storage monitoring", error=str(e))
                await asyncio.sleep(60)

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

    async def _get_free_space(self) -> int:
        """Get free space inside the virtual drive's FAT32 filesystem via a read-only shadow mount."""
        mount_point = self.settings.watcher.shadow_mount_point
        mount_point.mkdir(parents=True, exist_ok=True)

        result = await self._run_command(["sudo", "losetup", "-fP", str(self.virtual_drive_path)])
        if result.returncode != 0:
            self.logger.error("Failed to create loop device for space check", error=result.stderr)
            return 0

        result = await self._run_command(["sudo", "losetup", "-j", str(self.virtual_drive_path)])
        if result.returncode != 0 or not result.stdout.strip():
            return 0

        loop_dev = result.stdout.strip().splitlines()[0].split(":")[0]
        partition = f"{loop_dev}p1"

        for _ in range(10):
            if Path(partition).exists():
                break
            await self._run_command(["sudo", "partprobe", loop_dev])
            await asyncio.sleep(0.5)

        result = await self._run_command(
            ["sudo", "mount", "-t", "vfat", "-o", "ro", partition, str(mount_point)]
        )
        if result.returncode != 0:
            self.logger.error("Failed to mount drive for space check", error=result.stderr)
            await self._run_command(["sudo", "losetup", "-d", loop_dev])
            return 0

        try:
            return psutil.disk_usage(str(mount_point)).free
        except Exception as e:
            self.logger.error("Failed to read free space", error=str(e))
            return 0
        finally:
            await self._run_command(["sudo", "umount", str(mount_point)])
            await self._run_command(["sudo", "losetup", "-d", loop_dev])

    async def _cleanup_old_files(self) -> None:
        """Stop Storage Mode, delete old files from the virtual drive, then restart."""
        self.logger.info("Cleaning up old files from virtual drive")
        mount_point = self.settings.watcher.shadow_mount_point
        mount_point.mkdir(parents=True, exist_ok=True)

        # Unload g_mass_storage so we can mount the image writably
        result = await self._run_command(["sudo", "modprobe", "-r", "g_mass_storage"])
        if result.returncode != 0:
            self.logger.error("Failed to unload g_mass_storage for cleanup", error=result.stderr)
            return

        try:
            result = await self._run_command(["sudo", "losetup", "-fP", str(self.virtual_drive_path)])
            if result.returncode != 0:
                self.logger.error("Failed to create loop device for cleanup", error=result.stderr)
                return

            result = await self._run_command(["sudo", "losetup", "-j", str(self.virtual_drive_path)])
            if result.returncode != 0 or not result.stdout.strip():
                self.logger.error("Could not find loop device for cleanup")
                return

            loop_dev = result.stdout.strip().splitlines()[0].split(":")[0]
            partition = f"{loop_dev}p1"

            for _ in range(10):
                if Path(partition).exists():
                    break
                await self._run_command(["sudo", "partprobe", loop_dev])
                await asyncio.sleep(0.5)

            result = await self._run_command(
                ["sudo", "mount", "-t", "vfat", partition, str(mount_point)]
            )
            if result.returncode != 0:
                self.logger.error("Failed to mount drive for cleanup", error=result.stderr)
                await self._run_command(["sudo", "losetup", "-d", loop_dev])
                return

            try:
                cutoff = time.time() - self.settings.storage.retention_days * 86400
                removed = 0
                for file_path in mount_point.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                        file_path.unlink()
                        removed += 1
                        self.logger.debug("Removed old file", file=str(file_path))
                self.logger.info("Cleanup completed", files_removed=removed)
            finally:
                await self._run_command(["sudo", "umount", str(mount_point)])
                await self._run_command(["sudo", "losetup", "-d", loop_dev])

        finally:
            # Always restart Storage Mode regardless of cleanup outcome
            reload = await self._run_command(
                ["sudo", str(self._scripts_dir / "start_storage_mode.sh")]
            )
            if reload.returncode != 0:
                self.logger.error("Failed to restart Storage Mode after cleanup", error=reload.stderr)
                self.is_active = False

    async def _run_command(self, cmd: list) -> subprocess.CompletedProcess:
        """Run a command asynchronously and return a CompletedProcess."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(
            cmd, process.returncode, stdout.decode(), stderr.decode()
        )
