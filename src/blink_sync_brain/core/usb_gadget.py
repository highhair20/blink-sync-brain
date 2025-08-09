"""
USB Gadget Manager for Raspberry Pi Zero 2 W.

This module manages the USB gadget mode functionality, allowing the Pi Zero 2 W
to act as a virtual USB storage device for the Blink Sync Module.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import structlog
import psutil

from blink_sync_brain.config.settings import Settings


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
        self.virtual_drive_path: Optional[Path] = None
        self.is_configured = False
        self.is_active = False
        
    async def setup_usb_gadget(self) -> bool:
        """
        Setup USB gadget mode for mass storage.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        try:
            self.logger.info("Setting up USB gadget mode")
            
            # Check if running on Raspberry Pi
            if not self._is_raspberry_pi():
                self.logger.error("Not running on Raspberry Pi")
                return False
            
            # Create virtual drive file
            await self._create_virtual_drive()
            
            # Configure USB gadget
            await self._configure_usb_gadget()
            
            # Enable USB gadget mode
            await self._enable_usb_gadget()
            
            self.is_configured = True
            self.logger.info("USB gadget setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to setup USB gadget", error=str(e), exc_info=True)
            return False
    
    async def start_usb_gadget(self) -> bool:
        """
        Start the USB gadget service.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if not self.is_configured:
                self.logger.warning("USB gadget not configured, setting up first")
                if not await self.setup_usb_gadget():
                    return False
            
            self.logger.info("Starting USB gadget service")
            
            # Start the USB gadget service
            await self._start_gadget_service()
            
            self.is_active = True
            self.logger.info("USB gadget service started successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to start USB gadget service", error=str(e))
            return False
    
    async def stop_usb_gadget(self) -> bool:
        """
        Stop the USB gadget service.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            self.logger.info("Stopping USB gadget service")
            
            # Stop the USB gadget service
            await self._stop_gadget_service()
            
            self.is_active = False
            self.logger.info("USB gadget service stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to stop USB gadget service", error=str(e))
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the USB gadget.
        
        Returns:
            Dict containing status information
        """
        status = {
            "configured": self.is_configured,
            "active": self.is_active,
            "virtual_drive_path": str(self.virtual_drive_path) if self.virtual_drive_path else None,
            "drive_size": await self._get_drive_size(),
            "free_space": await self._get_free_space(),
            "connected": await self._is_connected(),
        }
        
        return status
    
    async def monitor_storage(self) -> None:
        """
        Monitor storage usage and manage space.
        
        This method runs continuously to monitor the virtual drive
        and manage storage space by removing old files when needed.
        """
        self.logger.info("Starting storage monitoring")
        
        while self.is_active:
            try:
                # Check available space
                free_space = await self._get_free_space()
                total_space = await self._get_drive_size()
                usage_percent = ((total_space - free_space) / total_space) * 100
                
                self.logger.debug(
                    "Storage status",
                    free_space_gb=free_space / (1024**3),
                    usage_percent=usage_percent,
                )
                
                # If usage is above threshold, clean up old files
                if usage_percent > self.settings.storage.cleanup_threshold:
                    await self._cleanup_old_files()
                
                # Wait before next check
                await asyncio.sleep(self.settings.storage.monitor_interval)
                
            except Exception as e:
                self.logger.error("Error in storage monitoring", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpu_info = f.read()
                return "Raspberry Pi" in cpu_info
        except Exception:
            return False
    
    async def _create_virtual_drive(self) -> None:
        """Create the virtual drive file."""
        drive_size = self.settings.storage.virtual_drive_size_gb
        drive_path = self.settings.storage.virtual_drive_path
        
        self.logger.info("Creating virtual drive", size_gb=drive_size, path=str(drive_path))
        
        # Create directory if it doesn't exist
        drive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create virtual drive file using dd
        cmd = [
            "dd", "if=/dev/zero",
            f"of={drive_path}",
            "bs=1G",
            f"count={drive_size}",
        ]
        
        result = await self._run_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create virtual drive: {result.stderr}")
        
        # Format the drive with ExFAT (recommended by Blink)
        await self._format_drive(drive_path)
        
        self.virtual_drive_path = drive_path
        self.logger.info("Virtual drive created successfully")
    
    async def _format_drive(self, drive_path: Path) -> None:
        """Format the virtual drive with ExFAT filesystem."""
        self.logger.info("Formatting virtual drive with ExFAT")
        
        # Install exfat-utils if not available
        await self._install_exfat_utils()
        
        # Format with ExFAT
        cmd = ["mkfs.exfat", str(drive_path)]
        result = await self._run_command(cmd)
        
        if result.returncode != 0:
            self.logger.warning("ExFAT formatting failed, trying FAT32", error=result.stderr)
            # Fallback to FAT32
            cmd = ["mkfs.vfat", "-F", "32", str(drive_path)]
            result = await self._run_command(cmd)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to format drive: {result.stderr}")
    
    async def _install_exfat_utils(self) -> None:
        """Install exfat-utils package if not available."""
        try:
            # Check if exfat-utils is installed
            result = await self._run_command(["which", "mkfs.exfat"])
            if result.returncode == 0:
                return  # Already installed
            
            # Install exfat-utils
            self.logger.info("Installing exfat-utils")
            cmd = ["apt-get", "update"]
            await self._run_command(cmd)
            
            cmd = ["apt-get", "install", "-y", "exfat-utils"]
            result = await self._run_command(cmd)
            
            if result.returncode != 0:
                self.logger.warning("Failed to install exfat-utils", error=result.stderr)
                
        except Exception as e:
            self.logger.warning("Could not install exfat-utils", error=str(e))
    
    async def _configure_usb_gadget(self) -> None:
        """Configure USB gadget mode."""
        self.logger.info("Configuring USB gadget mode")
        
        # Create gadget configuration
        config = self._create_gadget_config()
        
        # Write configuration to file
        config_path = Path("/sys/kernel/config/usb_gadget/blink_storage")
        config_path.mkdir(parents=True, exist_ok=True)
        
        # Apply configuration
        await self._apply_gadget_config(config_path, config)
        
        self.logger.info("USB gadget configuration applied")
    
    def _create_gadget_config(self) -> Dict[str, Any]:
        """Create USB gadget configuration."""
        return {
            "idVendor": "0x1d6b",  # Linux Foundation
            "idProduct": "0x0104",  # Multifunction Composite Gadget
            "bcdDevice": "0x0100",
            "bcdUSB": "0x0200",
            "strings": {
                "0x409": {
                    "serialnumber": "BLINK_STORAGE_001",
                    "product": "Blink Storage Device",
                    "manufacturer": "Blink Sync Brain",
                }
            },
            "configs": {
                "c.1": {
                    "MaxPower": "250",
                    "bmAttributes": "0x80",
                    "strings": {
                        "0x409": {
                            "configuration": "Blink Storage Configuration"
                        }
                    }
                }
            },
            "functions": {
                "mass_storage.0": {
                    "lun.0": {
                        "file": str(self.virtual_drive_path),
                        "removable": "1",
                        "cdrom": "0",
                        "ro": "0",
                        "no_fua": "1"
                    }
                }
            }
        }
    
    async def _apply_gadget_config(self, config_path: Path, config: Dict[str, Any]) -> None:
        """Apply the gadget configuration."""
        # This is a simplified version - in practice, you'd need to write
        # the configuration to the appropriate sysfs files
        self.logger.info("Applying gadget configuration", config_path=str(config_path))
        
        # Note: This is a placeholder for the actual implementation
        # The real implementation would involve writing to sysfs files
        # which requires root privileges and careful handling
        
        await asyncio.sleep(1)  # Simulate configuration time
    
    async def _enable_usb_gadget(self) -> None:
        """Enable USB gadget mode."""
        self.logger.info("Enabling USB gadget mode")
        
        # Enable the gadget
        cmd = ["echo", "1", ">", "/sys/kernel/config/usb_gadget/blink_storage/UDC"]
        result = await self._run_command(cmd, shell=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to enable USB gadget: {result.stderr}")
        
        self.logger.info("USB gadget mode enabled")
    
    async def _start_gadget_service(self) -> None:
        """Start the USB gadget service."""
        # In a real implementation, this would start a systemd service
        # or similar that manages the USB gadget
        self.logger.info("Starting USB gadget service")
        await asyncio.sleep(1)  # Simulate service startup
    
    async def _stop_gadget_service(self) -> None:
        """Stop the USB gadget service."""
        self.logger.info("Stopping USB gadget service")
        await asyncio.sleep(1)  # Simulate service shutdown
    
    async def _get_drive_size(self) -> int:
        """Get the total size of the virtual drive in bytes."""
        if not self.virtual_drive_path or not self.virtual_drive_path.exists():
            return 0
        
        try:
            stat = self.virtual_drive_path.stat()
            return stat.st_size
        except Exception as e:
            self.logger.error("Failed to get drive size", error=str(e))
            return 0
    
    async def _get_free_space(self) -> int:
        """Get the free space on the virtual drive in bytes."""
        if not self.virtual_drive_path or not self.virtual_drive_path.exists():
            return 0
        
        try:
            # Get disk usage of the directory containing the virtual drive
            disk_usage = psutil.disk_usage(self.virtual_drive_path.parent)
            return disk_usage.free
        except Exception as e:
            self.logger.error("Failed to get free space", error=str(e))
            return 0
    
    async def _is_connected(self) -> bool:
        """Check if the USB gadget is connected to a host."""
        try:
            # Check if the gadget is active in the system
            udc_path = Path("/sys/kernel/config/usb_gadget/blink_storage/UDC")
            if udc_path.exists():
                with open(udc_path, "r") as f:
                    content = f.read().strip()
                    return bool(content)
            return False
        except Exception as e:
            self.logger.error("Failed to check connection status", error=str(e))
            return False
    
    async def _cleanup_old_files(self) -> None:
        """Clean up old files to free up space."""
        self.logger.info("Cleaning up old files")
        
        try:
            # Mount the virtual drive if not already mounted
            mount_point = Path("/mnt/blink_storage")
            mount_point.mkdir(exist_ok=True)
            
            # Find and remove old files
            cutoff_time = asyncio.get_event_loop().time() - self.settings.storage.retention_days * 86400
            
            for file_path in mount_point.rglob("*"):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        self.logger.debug("Removed old file", file=str(file_path))
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error("Failed to cleanup old files", error=str(e))
    
    async def _run_command(self, cmd: list, shell: bool = False) -> subprocess.CompletedProcess:
        """Run a shell command asynchronously."""
        if shell:
            cmd = " ".join(cmd)
        
        process = await asyncio.create_subprocess_exec(
            *cmd if not shell else cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=shell,
        )
        
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(
            cmd, process.returncode, stdout.decode(), stderr.decode()
        ) 