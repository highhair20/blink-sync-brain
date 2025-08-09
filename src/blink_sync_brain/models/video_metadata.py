"""
Video metadata model for Blink Sync Brain.

This module defines the data structures for video metadata
and processing information.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class VideoMetadata:
    """Video metadata information."""
    
    width: int
    height: int
    fps: float
    duration: float
    codec: str
    created: datetime
    file_size: int
    bitrate: Optional[float] = None
    resolution: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.resolution is None:
            self.resolution = f"{self.width}x{self.height}"
        
        if self.bitrate is None and self.duration > 0:
            self.bitrate = (self.file_size * 8) / self.duration  # bits per second
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration": self.duration,
            "codec": self.codec,
            "created": self.created.isoformat(),
            "file_size": self.file_size,
            "bitrate": self.bitrate,
            "resolution": self.resolution,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "VideoMetadata":
        """Create from dictionary."""
        return cls(
            width=data["width"],
            height=data["height"],
            fps=data["fps"],
            duration=data["duration"],
            codec=data["codec"],
            created=datetime.fromisoformat(data["created"]),
            file_size=data["file_size"],
            bitrate=data.get("bitrate"),
            resolution=data.get("resolution"),
        ) 