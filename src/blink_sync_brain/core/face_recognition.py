"""
Face Recognition Engine for Blink Sync Brain.

This module provides face detection and recognition capabilities for
the Blink camera system enhancement.
"""

import asyncio
import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import face_recognition
import numpy as np
import structlog
from PIL import Image

from blink_sync_brain.models.face_data import FaceData, KnownFace


class FaceRecognitionEngine:
    """
    Face recognition engine for detecting and identifying faces in videos.
    
    This class provides face detection, encoding, and recognition capabilities
    using the face_recognition library and custom machine learning models.
    """
    
    def __init__(self, settings=None):
        """Initialize the Face Recognition Engine."""
        self.settings = settings
        self.logger = structlog.get_logger()
        self.known_faces: List[KnownFace] = []
        self.face_encodings: List[np.ndarray] = []
        self.face_names: List[str] = []
        self.model_path: Optional[Path] = None
        self.is_loaded = False
        
    async def load_face_database(self, database_path: Optional[Path] = None) -> bool:
        """
        Load the face recognition database.
        
        Args:
            database_path: Path to the face database file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if database_path is None:
                database_path = self.settings.face_recognition.database_path
            
            self.model_path = Path(database_path)
            
            if not self.model_path.exists():
                self.logger.warning("Face database not found, creating new one", path=str(self.model_path))
                await self._create_new_database()
                return True
            
            self.logger.info("Loading face database", path=str(self.model_path))
            
            # Load the face database
            with open(self.model_path, "rb") as f:
                data = pickle.load(f)
                
            self.known_faces = data.get("known_faces", [])
            self.face_encodings = data.get("encodings", [])
            self.face_names = data.get("names", [])
            
            self.is_loaded = True
            
            self.logger.info(
                "Face database loaded successfully",
                known_faces=len(self.known_faces),
                encodings=len(self.face_encodings),
            )
            
            return True
            
        except Exception as e:
            self.logger.error("Failed to load face database", error=str(e))
            return False
    
    async def save_face_database(self) -> bool:
        """
        Save the face recognition database.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            if not self.model_path:
                raise RuntimeError("No database path specified")
            
            self.logger.info("Saving face database", path=str(self.model_path))
            
            # Create directory if it doesn't exist
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for saving
            data = {
                "known_faces": self.known_faces,
                "encodings": self.face_encodings,
                "names": self.face_names,
                "last_updated": datetime.now(),
            }
            
            # Save to file
            with open(self.model_path, "wb") as f:
                pickle.dump(data, f)
            
            self.logger.info("Face database saved successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to save face database", error=str(e))
            return False
    
    async def add_known_face(
        self,
        name: str,
        image_path: Path,
        description: str = "",
        confidence_threshold: float = 0.6,
    ) -> bool:
        """
        Add a new known face to the database.
        
        Args:
            name: Name of the person
            image_path: Path to the face image
            description: Optional description
            confidence_threshold: Recognition confidence threshold
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            self.logger.info("Adding known face", name=name, image=str(image_path))
            
            # Load and process the image
            image = face_recognition.load_image_file(str(image_path))
            
            # Detect faces in the image
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                self.logger.warning("No faces detected in image", image=str(image_path))
                return False
            
            if len(face_locations) > 1:
                self.logger.warning("Multiple faces detected, using first one", image=str(image_path))
            
            # Get face encoding
            face_encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]
            
            # Create known face record
            known_face = KnownFace(
                name=name,
                encoding=face_encoding,
                description=description,
                confidence_threshold=confidence_threshold,
                added_date=datetime.now(),
                image_path=str(image_path),
            )
            
            # Add to database
            self.known_faces.append(known_face)
            self.face_encodings.append(face_encoding)
            self.face_names.append(name)
            
            # Save database
            await self.save_face_database()
            
            self.logger.info("Known face added successfully", name=name)
            return True
            
        except Exception as e:
            self.logger.error("Failed to add known face", error=str(e))
            return False
    
    async def remove_known_face(self, name: str) -> bool:
        """
        Remove a known face from the database.
        
        Args:
            name: Name of the person to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        try:
            self.logger.info("Removing known face", name=name)
            
            # Find and remove the face
            indices_to_remove = []
            
            for i, face_name in enumerate(self.face_names):
                if face_name == name:
                    indices_to_remove.append(i)
            
            # Remove in reverse order to maintain indices
            for i in reversed(indices_to_remove):
                del self.face_names[i]
                del self.face_encodings[i]
                del self.known_faces[i]
            
            # Save database
            await self.save_face_database()
            
            self.logger.info("Known face removed successfully", name=name, removed_count=len(indices_to_remove))
            return True
            
        except Exception as e:
            self.logger.error("Failed to remove known face", error=str(e))
            return False
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in an image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        try:
            # Use face_recognition library for detection
            face_locations = face_recognition.face_locations(image)
            return face_locations
            
        except Exception as e:
            self.logger.error("Failed to detect faces", error=str(e))
            return []
    
    def get_face_encoding(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Get face encoding for a detected face.
        
        Args:
            image: Input image as numpy array
            face_location: Face location as (top, right, bottom, left) tuple
            
        Returns:
            Face encoding as numpy array, or None if failed
        """
        try:
            # Extract face encoding
            face_encodings = face_recognition.face_encodings(image, [face_location])
            
            if face_encodings:
                return face_encodings[0]
            else:
                return None
                
        except Exception as e:
            self.logger.error("Failed to get face encoding", error=str(e))
            return None
    
    def recognize_face(self, face_encoding: np.ndarray, tolerance: float = 0.6) -> str:
        """
        Recognize a face from its encoding.
        
        Args:
            face_encoding: Face encoding to recognize
            tolerance: Recognition tolerance (lower = more strict)
            
        Returns:
            Name of the recognized person, or "Unknown" if not recognized
        """
        try:
            if not self.is_loaded or not self.face_encodings:
                return "Unknown"
            
            # Compare with known faces
            matches = face_recognition.compare_faces(
                self.face_encodings,
                face_encoding,
                tolerance=tolerance
            )
            
            if True in matches:
                # Find the best match
                face_distances = face_recognition.face_distance(self.face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    # Check confidence threshold
                    confidence = 1 - face_distances[best_match_index]
                    known_face = self.known_faces[best_match_index]
                    
                    if confidence >= known_face.confidence_threshold:
                        return known_face.name
            
            return "Unknown"
            
        except Exception as e:
            self.logger.error("Failed to recognize face", error=str(e))
            return "Unknown"
    
    async def batch_process_images(self, image_directory: Path) -> Dict[str, Any]:
        """
        Process a directory of images to build the face database.
        
        Args:
            image_directory: Directory containing face images
            
        Returns:
            Dictionary with processing results
        """
        self.logger.info("Starting batch image processing", directory=str(image_directory))
        
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
        }
        
        try:
            # Find all image files
            image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
            
            for image_file in image_directory.rglob("*"):
                if image_file.is_file() and image_file.suffix.lower() in image_extensions:
                    results["processed"] += 1
                    
                    try:
                        # Extract name from filename (assuming format: name.jpg)
                        name = image_file.stem
                        
                        # Add to database
                        success = await self.add_known_face(
                            name=name,
                            image_path=image_file,
                            description=f"Auto-added from {image_file.name}",
                        )
                        
                        if success:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Failed to process {image_file.name}")
                            
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"Error processing {image_file.name}: {str(e)}")
            
            self.logger.info(
                "Batch processing completed",
                processed=results["processed"],
                successful=results["successful"],
                failed=results["failed"],
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Failed to batch process images", error=str(e))
            results["errors"].append(f"Batch processing failed: {str(e)}")
            return results
    
    async def get_face_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the face database.
        
        Returns:
            Dictionary containing face database statistics
        """
        try:
            stats = {
                "total_faces": len(self.known_faces),
                "unique_names": len(set(self.face_names)),
                "database_size_mb": self._get_database_size(),
                "last_updated": None,
                "name_distribution": {},
            }
            
            # Calculate name distribution
            name_counts = {}
            for name in self.face_names:
                name_counts[name] = name_counts.get(name, 0) + 1
            
            stats["name_distribution"] = name_counts
            
            # Get last updated time
            if self.known_faces:
                latest_face = max(self.known_faces, key=lambda x: x.added_date)
                stats["last_updated"] = latest_face.added_date
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get face statistics", error=str(e))
            return {}
    
    async def validate_database(self) -> Dict[str, Any]:
        """
        Validate the face database for consistency.
        
        Returns:
            Dictionary containing validation results
        """
        try:
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
            }
            
            # Check for consistency
            if len(self.known_faces) != len(self.face_encodings):
                validation_results["is_valid"] = False
                validation_results["errors"].append("Face count mismatch")
            
            if len(self.face_encodings) != len(self.face_names):
                validation_results["is_valid"] = False
                validation_results["errors"].append("Name count mismatch")
            
            # Check for duplicate names
            name_counts = {}
            for name in self.face_names:
                name_counts[name] = name_counts.get(name, 0) + 1
            
            for name, count in name_counts.items():
                if count > 1:
                    validation_results["warnings"].append(f"Multiple encodings for {name}")
            
            # Check encoding quality
            for i, encoding in enumerate(self.face_encodings):
                if encoding is None or len(encoding) == 0:
                    validation_results["errors"].append(f"Invalid encoding at index {i}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error("Failed to validate database", error=str(e))
            return {"is_valid": False, "errors": [str(e)], "warnings": []}
    
    async def _create_new_database(self) -> None:
        """Create a new face database."""
        try:
            self.logger.info("Creating new face database")
            
            self.known_faces = []
            self.face_encodings = []
            self.face_names = []
            
            # Create directory if it doesn't exist
            if self.model_path:
                self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save empty database
            await self.save_face_database()
            
            self.is_loaded = True
            self.logger.info("New face database created successfully")
            
        except Exception as e:
            self.logger.error("Failed to create new database", error=str(e))
            raise
    
    def _get_database_size(self) -> float:
        """Get the size of the face database in MB."""
        try:
            if self.model_path and self.model_path.exists():
                size_bytes = self.model_path.stat().st_size
                return size_bytes / (1024 * 1024)
            return 0.0
        except Exception:
            return 0.0 