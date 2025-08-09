"""
Processing result model for Blink Sync Brain.

This module defines the data structures for video processing results
and analysis information.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .video_metadata import VideoMetadata


@dataclass
class ProcessingResult:
    """Video processing result information."""
    
    video_path: Path
    metadata: VideoMetadata
    face_detections: List[Dict[str, Any]]
    recognized_faces: List[Dict[str, Any]]
    processing_time: float
    timestamp: datetime
    status: str = "completed"
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "video_path": str(self.video_path),
            "metadata": self.metadata.to_dict(),
            "face_detections": self.face_detections,
            "recognized_faces": self.recognized_faces,
            "processing_time": self.processing_time,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "error_message": self.error_message,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProcessingResult":
        """Create from dictionary."""
        return cls(
            video_path=Path(data["video_path"]),
            metadata=VideoMetadata.from_dict(data["metadata"]),
            face_detections=data["face_detections"],
            recognized_faces=data["recognized_faces"],
            processing_time=data["processing_time"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data.get("status", "completed"),
            error_message=data.get("error_message"),
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the processing result."""
        return {
            "video_name": self.video_path.name,
            "duration_seconds": self.metadata.duration,
            "faces_detected": len(self.face_detections),
            "faces_recognized": len(self.recognized_faces),
            "processing_time": self.processing_time,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def get_recognized_names(self) -> List[str]:
        """Get list of recognized face names."""
        names = []
        for face in self.recognized_faces:
            name = face.get("name")
            if name and name not in names:
                names.append(name)
        return names
    
    def has_unknown_faces(self) -> bool:
        """Check if there are any unknown faces detected."""
        return len(self.face_detections) > len(self.recognized_faces)
    
    def get_unknown_face_count(self) -> int:
        """Get count of unknown faces."""
        return len(self.face_detections) - len(self.recognized_faces) 