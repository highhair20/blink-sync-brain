"""
Face data models for Blink Sync Brain.

This module defines the data structures for face recognition
and face database management.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np


@dataclass
class FaceData:
    """Basic face data structure."""
    
    encoding: np.ndarray
    location: tuple  # (top, right, bottom, left)
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "encoding": self.encoding.tolist(),
            "location": self.location,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FaceData":
        """Create from dictionary."""
        return cls(
            encoding=np.array(data["encoding"]),
            location=tuple(data["location"]),
            confidence=data["confidence"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class KnownFace:
    """Known face information for the database."""
    
    name: str
    encoding: np.ndarray
    description: str = ""
    confidence_threshold: float = 0.6
    added_date: Optional[datetime] = None
    image_path: Optional[str] = None
    last_seen: Optional[datetime] = None
    detection_count: int = 0
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.added_date is None:
            self.added_date = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "encoding": self.encoding.tolist(),
            "description": self.description,
            "confidence_threshold": self.confidence_threshold,
            "added_date": self.added_date.isoformat() if self.added_date else None,
            "image_path": self.image_path,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "detection_count": self.detection_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KnownFace":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            encoding=np.array(data["encoding"]),
            description=data.get("description", ""),
            confidence_threshold=data.get("confidence_threshold", 0.6),
            added_date=datetime.fromisoformat(data["added_date"]) if data.get("added_date") else None,
            image_path=data.get("image_path"),
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else None,
            detection_count=data.get("detection_count", 0),
        )
    
    def update_detection(self, timestamp: datetime = None) -> None:
        """Update detection information."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.last_seen = timestamp
        self.detection_count += 1
    
    def get_age_days(self) -> float:
        """Get the age of this face record in days."""
        if self.added_date:
            return (datetime.now() - self.added_date).days
        return 0.0
    
    def get_days_since_last_seen(self) -> Optional[float]:
        """Get days since last detection."""
        if self.last_seen:
            return (datetime.now() - self.last_seen).days
        return None 