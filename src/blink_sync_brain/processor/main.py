#!/usr/bin/env python3
import argparse
import asyncio
from pathlib import Path

import structlog

from blink_sync_brain.config.settings import Settings
from blink_sync_brain.processor.face_recognition import FaceRecognitionEngine
from blink_sync_brain.processor.video_processor import VideoProcessor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blink Processor (Pi #2) CLI")
    sub = parser.add_subparsers(dest="command")

    proc = sub.add_parser("process-video", help="Process a single video file")
    proc.add_argument("video_path", type=Path)
    proc.add_argument("--output-dir", type=Path)
    proc.add_argument("--config", type=Path)

    start = sub.add_parser("start", help="Start background processing (watch directory)")
    start.add_argument("--config", type=Path)

    sub.add_parser("status", help="Show simple status")

    return parser.parse_args()


async def _start_processing(settings: Settings) -> int:
    logger = structlog.get_logger()
    face = FaceRecognitionEngine(settings)
    await face.load_face_database()
    processor = VideoProcessor(settings)
    await processor.start_processing(face)
    logger.info("Processor running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await processor.stop_processing()
        return 0


async def _run() -> int:
    args = parse_args()
    settings = Settings(config_path=args.config) if getattr(args, "config", None) else Settings()

    if args.command == "process-video":
        face = FaceRecognitionEngine(settings)
        await face.load_face_database()
        processor = VideoProcessor(settings)
        await processor.process_video(args.video_path, args.output_dir, face)
        return 0

    if args.command == "start":
        return await _start_processing(settings)

    if args.command == "status":
        print({"video_dir": str(settings.storage.video_directory)})
        return 0

    print("No command provided. See --help")
    return 2


def main() -> None:
    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    main()

