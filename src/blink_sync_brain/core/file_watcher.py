"""
File watcher for Blink Sync Brain Drive Pi.

Monitors the virtual drive image for new clips written by Blink and pushes
them to the Processor Pi via rsync over SSH. Uses a short-lived read-only
shadow mount alongside g_mass_storage so Blink never loses access to its drive.

Flow:
  1. Poll virtual_drive.img mtime every poll_interval seconds.
  2. When mtime changes, mark pending and reset a settle timer.
  3. Once the image has been stable for settle_seconds (Blink finished writing),
     loop-mount it read-only, scan for new video files, rsync each to Pi #2,
     then unmount.
  4. Track pushed files in a JSON state file so restarts don't re-push clips.
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Set

import structlog

from blink_sync_brain.config.settings import Settings


VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".h264"}


class FileWatcher:
    """
    Watches the virtual drive image for new Blink clips and pushes them to Pi #2.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = structlog.get_logger()
        self._running = False
        self._pushed_files: Set[str] = set()
        self._last_mtime: float = 0.0
        self._last_changed_at: float = 0.0
        self._pending_scan: bool = False

    async def start(self) -> None:
        """Start watching for new clips."""
        self._running = True
        self._load_state()
        self.logger.info(
            "File watcher started",
            drive=str(self.settings.storage.virtual_drive_path),
            processor=self.settings.watcher.processor_host,
        )
        await self._watch_loop()

    async def stop(self) -> None:
        """Stop the watcher and clean up any active mount."""
        self._running = False
        self._save_state()
        await self._unmount_shadow()
        self.logger.info("File watcher stopped")

    # -------------------------------------------------------------------------
    # Main watch loop
    # -------------------------------------------------------------------------

    async def _watch_loop(self) -> None:
        drive_path = self.settings.storage.virtual_drive_path

        while self._running:
            try:
                await self._tick(drive_path)
            except Exception as e:
                self.logger.error("Error in watch loop", error=str(e))
            await asyncio.sleep(self.settings.watcher.poll_interval)

    async def _tick(self, drive_path: Path) -> None:
        """Single poll cycle: detect image changes and trigger scan when settled."""
        try:
            current_mtime = drive_path.stat().st_mtime
        except FileNotFoundError:
            self.logger.warning("Virtual drive image not found", path=str(drive_path))
            return

        now = asyncio.get_event_loop().time()

        if current_mtime != self._last_mtime:
            # Image changed — reset settle timer and wait
            self._last_mtime = current_mtime
            self._last_changed_at = now
            self._pending_scan = True
            self.logger.debug("Drive image changed, waiting to settle")
            return

        if self._pending_scan and (now - self._last_changed_at) >= self.settings.watcher.settle_seconds:
            self._pending_scan = False
            await self._scan_and_push()

    # -------------------------------------------------------------------------
    # Scan and push
    # -------------------------------------------------------------------------

    async def _scan_and_push(self) -> None:
        """Mount the drive read-only, find new clips, push to processor."""
        drive_path = self.settings.storage.virtual_drive_path
        mount_point = self.settings.watcher.shadow_mount_point

        self.logger.info("Scanning virtual drive for new clips")

        if not await self._mount_shadow(drive_path, mount_point):
            return

        try:
            new_files = self._find_new_files(mount_point)
            if not new_files:
                self.logger.debug("No new clips found")
                return

            self.logger.info("New clips found", count=len(new_files))

            for file_path in new_files:
                if await self._push_file(file_path):
                    self._pushed_files.add(str(file_path.relative_to(mount_point)))
                    self._save_state()
        finally:
            await self._unmount_shadow()

    def _find_new_files(self, mount_point: Path) -> list:
        """Return video files on the mount that have not yet been pushed."""
        new_files = []
        for ext in VIDEO_EXTENSIONS:
            for file_path in mount_point.rglob(f"*{ext}"):
                if str(file_path.relative_to(mount_point)) not in self._pushed_files:
                    new_files.append(file_path)
        return sorted(new_files)

    async def _push_file(self, file_path: Path) -> bool:
        """Rsync a single clip to the Processor Pi."""
        watcher = self.settings.watcher

        if not watcher.processor_host:
            self.logger.error("watcher.processor_host is not configured")
            return False

        destination = (
            f"{watcher.processor_user}@{watcher.processor_host}:"
            f"{watcher.processor_video_path}/"
        )

        ssh_opts = "-o StrictHostKeyChecking=no -o BatchMode=yes"
        if watcher.ssh_key_path:
            ssh_opts += f" -i {watcher.ssh_key_path}"

        cmd = [
            "rsync", "-az",
            f"--timeout={watcher.rsync_timeout}",
            "-e", f"ssh {ssh_opts}",
            str(file_path),
            destination,
        ]

        self.logger.info("Pushing clip to processor", file=file_path.name)
        result = await self._run_command(cmd)

        if result.returncode != 0:
            self.logger.error("rsync failed", file=str(file_path), stderr=result.stderr)
            return False

        self.logger.info("Clip pushed successfully", file=file_path.name)
        return True

    # -------------------------------------------------------------------------
    # Shadow mount management
    # -------------------------------------------------------------------------

    async def _mount_shadow(self, drive_path: Path, mount_point: Path) -> bool:
        """Loop-mount the virtual drive image read-only alongside g_mass_storage."""
        mount_point.mkdir(parents=True, exist_ok=True)

        # Create a new loop device backed by the image file
        result = await self._run_command(["losetup", "-fP", str(drive_path)])
        if result.returncode != 0:
            self.logger.error("Failed to create loop device", stderr=result.stderr)
            return False

        # Resolve which loop device was just created
        result = await self._run_command(["losetup", "-j", str(drive_path)])
        if result.returncode != 0 or not result.stdout.strip():
            self.logger.error("Could not find loop device for image")
            return False

        loop_dev = result.stdout.strip().splitlines()[0].split(":")[0]
        partition = f"{loop_dev}p1"

        # Wait for the partition device node to appear
        for _ in range(10):
            if Path(partition).exists():
                break
            await self._run_command(["partprobe", loop_dev])
            await asyncio.sleep(0.5)

        if not Path(partition).exists():
            self.logger.error("Partition device not found", partition=partition)
            await self._run_command(["losetup", "-d", loop_dev])
            return False

        result = await self._run_command(
            ["mount", "-t", "vfat", "-o", "ro", partition, str(mount_point)]
        )
        if result.returncode != 0:
            self.logger.error("Failed to mount shadow drive", stderr=result.stderr)
            await self._run_command(["losetup", "-d", loop_dev])
            return False

        self.logger.debug("Shadow mount active", mount_point=str(mount_point))
        return True

    async def _unmount_shadow(self) -> None:
        """Unmount the shadow mount and detach the loop device."""
        mount_point = self.settings.watcher.shadow_mount_point
        drive_path = self.settings.storage.virtual_drive_path

        result = await self._run_command(["mountpoint", "-q", str(mount_point)])
        if result.returncode == 0:
            await self._run_command(["umount", str(mount_point)])

        result = await self._run_command(["losetup", "-j", str(drive_path)])
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                loop_dev = line.split(":")[0].strip()
                await self._run_command(["losetup", "-d", loop_dev])

    # -------------------------------------------------------------------------
    # State persistence
    # -------------------------------------------------------------------------

    def _load_state(self) -> None:
        """Load the pushed-files set from disk."""
        state_path = self.settings.watcher.state_file
        if state_path.exists():
            try:
                data = json.loads(state_path.read_text())
                self._pushed_files = set(data.get("pushed_files", []))
                self.logger.debug("Loaded watcher state", known_files=len(self._pushed_files))
            except Exception as e:
                self.logger.warning("Could not load watcher state", error=str(e))

    def _save_state(self) -> None:
        """Persist the pushed-files set to disk."""
        state_path = self.settings.watcher.state_file
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps({"pushed_files": list(self._pushed_files)}, indent=2)
            )
        except Exception as e:
            self.logger.warning("Could not save watcher state", error=str(e))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def _run_command(self, cmd: list) -> subprocess.CompletedProcess:
        """Run a shell command asynchronously."""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return subprocess.CompletedProcess(
            cmd, process.returncode, stdout.decode(), stderr.decode()
        )
