#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
import structlog.stdlib

from blink_lens.config.settings import Settings
from blink_lens.drive.usb_gadget import USBGadgetManager

# Commands that require root (invoke modprobe, mount, losetup, rsync via sudo)
_PRIVILEGED_COMMANDS = {"start", "stop", "watch"}


def _configure_logging() -> None:
    """Configure structlog to print human-readable lines to the console."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def _watcher_running() -> bool:
    """Return True if the blink-watcher systemd service is active."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "--quiet", "blink-watcher"],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False  # systemctl not available (non-systemd environment)


def _format_status(status: Dict[str, Any], watcher_running: bool, clips_pushed: int) -> str:
    """Format the gadget status dict as a human-readable string."""
    if status["drive_size"]:
        drive_str = f"{status['drive_size'] / (1024 ** 3):.1f} GB ({status['virtual_drive_path']})"
    else:
        drive_str = (
            f"not found ({status['virtual_drive_path']}) — "
            f"run: sudo /opt/blink-lens/scripts/drive/install.sh"
        )
    if watcher_running:
        watcher_str = f"RUNNING ({clips_pushed} clip{'s' if clips_pushed != 1 else ''} pushed)"
    else:
        watcher_str = "STOPPED (start with: sudo systemctl start blink-watcher)"
    return (
        f"Storage Mode:  {'ACTIVE' if status['active'] else 'INACTIVE'}\n"
        f"Virtual Drive: {drive_str}\n"
        f"Watcher:       {watcher_str}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blink Drive (Pi #1) CLI")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start", help="Start USB gadget service")
    start.add_argument("--config", type=Path)

    stop = sub.add_parser("stop", help="Stop USB gadget service")
    stop.add_argument("--config", type=Path)

    status = sub.add_parser("status", help="Show gadget status")
    status.add_argument("--config", type=Path)

    watch = sub.add_parser("watch", help="Watch for new clips and push to processor Pi")
    watch.add_argument("--config", type=Path)

    return parser.parse_args()


async def _run() -> int:
    _configure_logging()
    args = parse_args()
    logger = structlog.get_logger()

    if args.command in _PRIVILEGED_COMMANDS and os.geteuid() != 0:
        logger.error(
            "This command must be run as root",
            command=args.command,
            hint="Try: sudo blink-drive " + args.command,
        )
        return 1

    settings = Settings.from_file(args.config) if getattr(args, "config", None) else Settings()

    errors = settings.validate()
    if errors:
        for error in errors:
            logger.error("Configuration error", detail=error)
        return 1

    manager = USBGadgetManager(settings)

    if args.command == "start":
        ok = await manager.start_usb_gadget()
        if ok:
            logger.info(
                "Storage Mode active — now run: sudo blink-drive watch",
                hint="blink-drive watch pushes clips to the Processor Pi",
            )
        return 0 if ok else 1
    if args.command == "stop":
        ok = await manager.stop_usb_gadget()
        return 0 if ok else 1
    if args.command == "status":
        gadget_status = await manager.get_status()
        watcher_running = _watcher_running()
        clips_pushed = 0
        state_file = settings.watcher.state_file
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                clips_pushed = len(data.get("pushed_files", []))
            except Exception:
                pass
        print(_format_status(gadget_status, watcher_running, clips_pushed))
        return 0
    if args.command == "watch":
        from blink_lens.core.file_watcher import FileWatcher
        try:
            watcher = FileWatcher(settings)
            await watcher.start()
        except (ValueError, FileNotFoundError, PermissionError) as e:
            logger.error("Watcher configuration error", detail=str(e))
            return 1
        # start() only returns if the watch loop exits — unexpected in normal operation
        logger.error("Watcher exited unexpectedly — check logs for errors")
        return 1

    logger.error("No command provided. See --help")
    return 2


def main() -> None:
    try:
        raise SystemExit(asyncio.run(_run()))
    except KeyboardInterrupt:
        raise SystemExit(0)


if __name__ == "__main__":
    main()
