#!/usr/bin/env python3
"""
Main entry point for Blink Sync Brain application.

This module provides the command-line interface for the Blink camera
system enhancement using Raspberry Pi Zero 2 W.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from dotenv import load_dotenv

from blink_sync_brain.core.system_manager import SystemManager
from blink_sync_brain.config.settings import Settings
from blink_sync_brain.utils.logging import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Blink Sync Brain - Enhanced Blink camera system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the complete system
  blink-sync-brain start

  # Start only USB gadget mode (Pi #1)
  blink-sync-brain start --mode usb-gadget

  # Start only video processing (Pi #2)
  blink-sync-brain start --mode video-processor

  # Run face recognition on specific video
  blink-sync-brain process-video /path/to/video.mp4

  # Check system status
  blink-sync-brain status

  # Run tests
  blink-sync-brain test
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the Blink Sync Brain system")
    start_parser.add_argument(
        "--mode",
        choices=["complete", "usb-gadget", "video-processor"],
        default="complete",
        help="Operation mode (default: complete)",
    )
    start_parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    start_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    # Process video command
    process_parser = subparsers.add_parser(
        "process-video", help="Process a single video file"
    )
    process_parser.add_argument("video_path", type=Path, help="Path to video file")
    process_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for processed video",
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed status information",
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run system tests")
    test_parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run (default: all)",
    )

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Setup system components")
    setup_parser.add_argument(
        "component",
        choices=["usb-gadget", "face-database", "storage", "notifications"],
        help="Component to setup",
    )

    return parser.parse_args()


async def start_system(mode: str, config_path: Optional[Path], log_level: str) -> None:
    """Start the Blink Sync Brain system."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging(log_level)
    logger = structlog.get_logger()

    logger.info("Starting Blink Sync Brain system", mode=mode)

    try:
        # Load settings
        settings = Settings(config_path=config_path)
        
        # Initialize system manager
        system_manager = SystemManager(settings)
        
        # Start system based on mode
        if mode == "complete":
            await system_manager.start_complete_system()
        elif mode == "usb-gadget":
            await system_manager.start_usb_gadget_mode()
        elif mode == "video-processor":
            await system_manager.start_video_processor_mode()
        
        logger.info("System started successfully", mode=mode)
        
        # Keep the system running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            
    except Exception as e:
        logger.error("Failed to start system", error=str(e), exc_info=True)
        sys.exit(1)
    finally:
        await system_manager.shutdown()


async def process_video(video_path: Path, output_dir: Optional[Path]) -> None:
    """Process a single video file."""
    from blink_sync_brain.core.video_processor import VideoProcessor
    from blink_sync_brain.core.face_recognition import FaceRecognitionEngine
    
    load_dotenv()
    setup_logging("INFO")
    logger = structlog.get_logger()
    
    try:
        processor = VideoProcessor()
        face_engine = FaceRecognitionEngine()
        
        logger.info("Processing video", video_path=str(video_path))
        
        # Process the video
        result = await processor.process_video(
            video_path=video_path,
            output_dir=output_dir,
            face_engine=face_engine,
        )
        
        logger.info("Video processing completed", result=result)
        
    except Exception as e:
        logger.error("Failed to process video", error=str(e), exc_info=True)
        sys.exit(1)


async def show_status(detailed: bool) -> None:
    """Show system status."""
    from blink_sync_brain.core.system_manager import SystemManager
    
    load_dotenv()
    setup_logging("INFO")
    logger = structlog.get_logger()
    
    try:
        system_manager = SystemManager()
        status = await system_manager.get_status(detailed=detailed)
        
        # Print status information
        print("Blink Sync Brain System Status")
        print("=" * 40)
        
        for component, info in status.items():
            print(f"\n{component}:")
            for key, value in info.items():
                print(f"  {key}: {value}")
                
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        sys.exit(1)


def run_tests(test_type: str) -> None:
    """Run system tests."""
    import subprocess
    import sys
    
    test_commands = {
        "unit": ["pytest", "tests/unit", "-v"],
        "integration": ["pytest", "tests/integration", "-v"],
        "all": ["pytest", "tests", "-v"],
    }
    
    try:
        result = subprocess.run(test_commands[test_type], check=True)
        print(f"Tests completed successfully: {test_type}")
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Tests failed: {e}")
        sys.exit(e.returncode)


async def setup_component(component: str) -> None:
    """Setup a specific component."""
    from blink_sync_brain.core.setup_manager import SetupManager
    
    load_dotenv()
    setup_logging("INFO")
    logger = structlog.get_logger()
    
    try:
        setup_manager = SetupManager()
        
        logger.info("Setting up component", component=component)
        
        if component == "usb-gadget":
            await setup_manager.setup_usb_gadget()
        elif component == "face-database":
            await setup_manager.setup_face_database()
        elif component == "storage":
            await setup_manager.setup_storage()
        elif component == "notifications":
            await setup_manager.setup_notifications()
        
        logger.info("Component setup completed", component=component)
        
    except Exception as e:
        logger.error("Failed to setup component", component=component, error=str(e))
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    if not args.command:
        print("Error: No command specified")
        print("Use 'blink-sync-brain --help' for usage information")
        sys.exit(1)
    
    try:
        if args.command == "start":
            asyncio.run(start_system(args.mode, args.config, args.log_level))
        elif args.command == "process-video":
            asyncio.run(process_video(args.video_path, args.output_dir))
        elif args.command == "status":
            asyncio.run(show_status(args.detailed))
        elif args.command == "test":
            run_tests(args.test_type)
        elif args.command == "setup":
            asyncio.run(setup_component(args.component))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 