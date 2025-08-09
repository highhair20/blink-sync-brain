"""
Blink Sync Brain - Enhanced Blink camera system using Raspberry Pi Zero 2 W.

This package provides a comprehensive solution for local video processing,
face recognition, and intelligent video management for Blink cameras.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core.usb_gadget import USBGadgetManager
from .core.video_processor import VideoProcessor
from .core.face_recognition import FaceRecognitionEngine
from .core.storage_manager import StorageManager
from .core.notification_service import NotificationService

__all__ = [
    "USBGadgetManager",
    "VideoProcessor", 
    "FaceRecognitionEngine",
    "StorageManager",
    "NotificationService",
] 