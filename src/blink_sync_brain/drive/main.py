#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path

import structlog

from blink_sync_brain.config.settings import Settings
from blink_sync_brain.drive.usb_gadget import USBGadgetManager


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blink Drive (Pi #1) CLI")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start", help="Start USB gadget service")
    start.add_argument("--config", type=Path)

    stop = sub.add_parser("stop", help="Stop USB gadget service")
    stop.add_argument("--config", type=Path)

    sub.add_parser("status", help="Show gadget status")

    setup = sub.add_parser("setup", help="Setup USB gadget (create drive, config gadget)")
    setup.add_argument("--config", type=Path)

    return parser.parse_args()


async def _run() -> int:
    args = parse_args()
    logger = structlog.get_logger()
    settings = Settings(config_path=args.config) if getattr(args, "config", None) else Settings()
    manager = USBGadgetManager(settings)

    if args.command == "start":
        ok = await manager.start_usb_gadget()
        return 0 if ok else 1
    if args.command == "stop":
        ok = await manager.stop_usb_gadget()
        return 0 if ok else 1
    if args.command == "setup":
        ok = await manager.setup_usb_gadget()
        return 0 if ok else 1
    if args.command == "status":
        status = await manager.get_status()
        print(status)
        return 0

    logger.error("No command provided. See --help")
    return 2


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()

