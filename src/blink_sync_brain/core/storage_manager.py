"""
Storage Manager for Blink Sync Brain.

This module handles storage operations, file management, and storage
monitoring for the Blink camera system enhancement.
"""

import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import psutil
import structlog

from blink_sync_brain.config.settings import Settings


class StorageManager:
    """
    Manages storage operations for the Blink camera system.
    
    This class handles file management, storage monitoring, cleanup,
    and storage statistics for the system.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the Storage Manager."""
        self.settings = settings
        self.logger = structlog.get_logger()
        self.is_monitoring = False
        
    async def start_storage_monitoring(self) -> None:
        """Start storage monitoring service."""
        self.logger.info("Starting storage monitoring service")
        self.is_monitoring = True
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Storage monitoring service started")
    
    async def stop_storage_monitoring(self) -> None:
        """Stop storage monitoring service."""
        self.logger.info("Stopping storage monitoring service")
        self.is_monitoring = False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive storage statistics.
        
        Returns:
            Dictionary containing storage statistics
        """
        try:
            # Get disk usage for video directory
            video_dir = self.settings.storage.video_directory
            if video_dir.exists():
                disk_usage = psutil.disk_usage(video_dir)
                video_stats = {
                    "total_bytes": disk_usage.total,
                    "used_bytes": disk_usage.used,
                    "free_bytes": disk_usage.free,
                    "usage_percent": (disk_usage.used / disk_usage.total) * 100,
                }
            else:
                video_stats = {"error": "Video directory does not exist"}
            
            # Get file statistics
            file_stats = await self._get_file_statistics()
            
            # Get cleanup statistics
            cleanup_stats = await self._get_cleanup_statistics()
            
            stats = {
                "video_directory": video_stats,
                "files": file_stats,
                "cleanup": cleanup_stats,
                "timestamp": datetime.now(),
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get storage statistics", error=str(e))
            return {"error": str(e)}
    
    async def cleanup_old_files(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Clean up old files based on retention policy.
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary containing cleanup results
        """
        try:
            self.logger.info("Starting file cleanup", dry_run=dry_run)
            
            results = {
                "files_processed": 0,
                "files_deleted": 0,
                "bytes_freed": 0,
                "errors": [],
                "deleted_files": [],
            }
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=self.settings.storage.retention_days)
            
            # Process video directory
            video_dir = self.settings.storage.video_directory
            if video_dir.exists():
                video_results = await self._cleanup_directory(
                    video_dir, cutoff_date, dry_run
                )
                results["files_processed"] += video_results["files_processed"]
                results["files_deleted"] += video_results["files_deleted"]
                results["bytes_freed"] += video_results["bytes_freed"]
                results["errors"].extend(video_results["errors"])
                results["deleted_files"].extend(video_results["deleted_files"])
            
            # Process results directory
            results_dir = self.settings.storage.results_directory
            if results_dir.exists():
                result_results = await self._cleanup_directory(
                    results_dir, cutoff_date, dry_run
                )
                results["files_processed"] += result_results["files_processed"]
                results["files_deleted"] += result_results["files_deleted"]
                results["bytes_freed"] += result_results["bytes_freed"]
                results["errors"].extend(result_results["errors"])
                results["deleted_files"].extend(result_results["deleted_files"])
            
            self.logger.info(
                "File cleanup completed",
                files_processed=results["files_processed"],
                files_deleted=results["files_deleted"],
                bytes_freed_mb=results["bytes_freed"] / (1024 * 1024),
                dry_run=dry_run,
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to cleanup old files", error=str(e))
            return {"error": str(e)}
    
    async def get_file_list(self, directory: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Get a list of files in the specified directory.
        
        Args:
            directory: Directory to list files from (defaults to video directory)
            
        Returns:
            List of file information dictionaries
        """
        try:
            if directory is None:
                directory = self.settings.storage.video_directory
            
            if not directory.exists():
                return []
            
            files = []
            
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime),
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "extension": file_path.suffix.lower(),
                    })
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x["modified"], reverse=True)
            
            return files
            
        except Exception as e:
            self.logger.error("Failed to get file list", error=str(e))
            return []
    
    async def move_file(self, source_path: Path, destination_path: Path) -> bool:
        """
        Move a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            bool: True if moved successfully, False otherwise
        """
        try:
            self.logger.info("Moving file", source=str(source_path), destination=str(destination_path))
            
            # Create destination directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(destination_path))
            
            self.logger.info("File moved successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to move file", error=str(e))
            return False
    
    async def copy_file(self, source_path: Path, destination_path: Path) -> bool:
        """
        Copy a file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            bool: True if copied successfully, False otherwise
        """
        try:
            self.logger.info("Copying file", source=str(source_path), destination=str(destination_path))
            
            # Create destination directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy the file
            shutil.copy2(str(source_path), str(destination_path))
            
            self.logger.info("File copied successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to copy file", error=str(e))
            return False
    
    async def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            self.logger.info("Deleting file", file=str(file_path))
            
            if file_path.exists():
                file_path.unlink()
                self.logger.info("File deleted successfully")
                return True
            else:
                self.logger.warning("File does not exist", file=str(file_path))
                return False
                
        except Exception as e:
            self.logger.error("Failed to delete file", error=str(e))
            return False
    
    async def _monitoring_loop(self) -> None:
        """Main storage monitoring loop."""
        self.logger.info("Starting storage monitoring loop")
        
        while self.is_monitoring:
            try:
                # Get storage statistics
                stats = await self.get_storage_statistics()
                
                # Check if cleanup is needed
                if "video_directory" in stats and "usage_percent" in stats["video_directory"]:
                    usage_percent = stats["video_directory"]["usage_percent"]
                    
                    if usage_percent > self.settings.storage.cleanup_threshold:
                        self.logger.warning(
                            "Storage usage above threshold, starting cleanup",
                            usage_percent=usage_percent,
                            threshold=self.settings.storage.cleanup_threshold,
                        )
                        
                        # Perform cleanup
                        await self.cleanup_old_files(dry_run=False)
                
                # Wait before next check
                await asyncio.sleep(self.settings.storage.monitor_interval)
                
            except Exception as e:
                self.logger.error("Error in storage monitoring loop", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _get_file_statistics(self) -> Dict[str, Any]:
        """Get file statistics for the storage directories."""
        try:
            stats = {
                "total_files": 0,
                "total_size_bytes": 0,
                "file_types": {},
                "oldest_file": None,
                "newest_file": None,
            }
            
            # Process video directory
            video_dir = self.settings.storage.video_directory
            if video_dir.exists():
                video_stats = await self._get_directory_stats(video_dir)
                stats["total_files"] += video_stats["total_files"]
                stats["total_size_bytes"] += video_stats["total_size_bytes"]
                
                # Merge file types
                for ext, count in video_stats["file_types"].items():
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + count
                
                # Update oldest/newest files
                if video_stats["oldest_file"]:
                    if not stats["oldest_file"] or video_stats["oldest_file"]["modified"] < stats["oldest_file"]["modified"]:
                        stats["oldest_file"] = video_stats["oldest_file"]
                
                if video_stats["newest_file"]:
                    if not stats["newest_file"] or video_stats["newest_file"]["modified"] > stats["newest_file"]["modified"]:
                        stats["newest_file"] = video_stats["newest_file"]
            
            # Process results directory
            results_dir = self.settings.storage.results_directory
            if results_dir.exists():
                result_stats = await self._get_directory_stats(results_dir)
                stats["total_files"] += result_stats["total_files"]
                stats["total_size_bytes"] += result_stats["total_size_bytes"]
                
                # Merge file types
                for ext, count in result_stats["file_types"].items():
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + count
                
                # Update oldest/newest files
                if result_stats["oldest_file"]:
                    if not stats["oldest_file"] or result_stats["oldest_file"]["modified"] < stats["oldest_file"]["modified"]:
                        stats["oldest_file"] = result_stats["oldest_file"]
                
                if result_stats["newest_file"]:
                    if not stats["newest_file"] or result_stats["newest_file"]["modified"] > stats["newest_file"]["modified"]:
                        stats["newest_file"] = result_stats["newest_file"]
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get file statistics", error=str(e))
            return {"error": str(e)}
    
    async def _get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Get statistics for a specific directory."""
        try:
            stats = {
                "total_files": 0,
                "total_size_bytes": 0,
                "file_types": {},
                "oldest_file": None,
                "newest_file": None,
            }
            
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += stat.st_size
                    
                    # Count file types
                    ext = file_path.suffix.lower()
                    stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1
                    
                    # Track oldest/newest files
                    file_info = {
                        "name": file_path.name,
                        "path": str(file_path),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                    }
                    
                    if not stats["oldest_file"] or file_info["modified"] < stats["oldest_file"]["modified"]:
                        stats["oldest_file"] = file_info
                    
                    if not stats["newest_file"] or file_info["modified"] > stats["newest_file"]["modified"]:
                        stats["newest_file"] = file_info
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get directory stats", error=str(e))
            return {"error": str(e)}
    
    async def _get_cleanup_statistics(self) -> Dict[str, Any]:
        """Get cleanup statistics."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.settings.storage.retention_days)
            
            stats = {
                "retention_days": self.settings.storage.retention_days,
                "cutoff_date": cutoff_date,
                "files_eligible_for_cleanup": 0,
                "bytes_eligible_for_cleanup": 0,
            }
            
            # Count eligible files
            for directory in [self.settings.storage.video_directory, self.settings.storage.results_directory]:
                if directory.exists():
                    for file_path in directory.rglob("*"):
                        if file_path.is_file():
                            stat = file_path.stat()
                            file_date = datetime.fromtimestamp(stat.st_mtime)
                            
                            if file_date < cutoff_date:
                                stats["files_eligible_for_cleanup"] += 1
                                stats["bytes_eligible_for_cleanup"] += stat.st_size
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get cleanup statistics", error=str(e))
            return {"error": str(e)}
    
    async def _cleanup_directory(self, directory: Path, cutoff_date: datetime, dry_run: bool) -> Dict[str, Any]:
        """Clean up files in a specific directory."""
        results = {
            "files_processed": 0,
            "files_deleted": 0,
            "bytes_freed": 0,
            "errors": [],
            "deleted_files": [],
        }
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    results["files_processed"] += 1
                    
                    try:
                        stat = file_path.stat()
                        file_date = datetime.fromtimestamp(stat.st_mtime)
                        
                        if file_date < cutoff_date:
                            if dry_run:
                                results["files_deleted"] += 1
                                results["bytes_freed"] += stat.st_size
                                results["deleted_files"].append(str(file_path))
                            else:
                                # Actually delete the file
                                file_path.unlink()
                                results["files_deleted"] += 1
                                results["bytes_freed"] += stat.st_size
                                results["deleted_files"].append(str(file_path))
                                
                                self.logger.debug("Deleted old file", file=str(file_path))
                    
                    except Exception as e:
                        error_msg = f"Failed to process {file_path}: {str(e)}"
                        results["errors"].append(error_msg)
                        self.logger.error(error_msg)
            
            return results
            
        except Exception as e:
            error_msg = f"Failed to cleanup directory {directory}: {str(e)}"
            results["errors"].append(error_msg)
            self.logger.error(error_msg)
            return results 