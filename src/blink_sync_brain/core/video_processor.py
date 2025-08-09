"""
Video Processor for Blink Sync Brain.

This module handles video processing, analysis, and management for the
Blink camera system enhancement.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import cv2
import ffmpeg
import numpy as np
import structlog
from moviepy.editor import VideoFileClip

from blink_sync_brain.core.face_recognition import FaceRecognitionEngine
from blink_sync_brain.models.video_metadata import VideoMetadata
from blink_sync_brain.models.processing_result import ProcessingResult


class VideoProcessor:
    """
    Handles video processing and analysis for Blink camera recordings.
    
    This class manages video file processing, face recognition, video stitching,
    and storage management for the Blink camera system.
    """
    
    def __init__(self, settings=None):
        """Initialize the Video Processor."""
        self.settings = settings
        self.logger = structlog.get_logger()
        self.face_engine: Optional[FaceRecognitionEngine] = None
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.is_processing = False
        
    async def start_processing(self, face_engine: FaceRecognitionEngine) -> None:
        """
        Start the video processing service.
        
        Args:
            face_engine: Face recognition engine instance
        """
        self.face_engine = face_engine
        self.is_processing = True
        
        self.logger.info("Starting video processing service")
        
        # Start processing loop
        asyncio.create_task(self._processing_loop())
        
        # Start video monitoring
        asyncio.create_task(self._monitor_video_directory())
        
        self.logger.info("Video processing service started")
    
    async def stop_processing(self) -> None:
        """Stop the video processing service."""
        self.logger.info("Stopping video processing service")
        self.is_processing = False
        
        # Wait for processing queue to empty
        while not self.processing_queue.empty():
            await asyncio.sleep(1)
        
        self.logger.info("Video processing service stopped")
    
    async def process_video(
        self,
        video_path: Path,
        output_dir: Optional[Path] = None,
        face_engine: Optional[FaceRecognitionEngine] = None,
    ) -> ProcessingResult:
        """
        Process a single video file.
        
        Args:
            video_path: Path to the video file
            output_dir: Output directory for processed video
            face_engine: Face recognition engine (optional)
            
        Returns:
            ProcessingResult containing analysis results
        """
        if face_engine:
            self.face_engine = face_engine
        
        if not self.face_engine:
            raise RuntimeError("Face recognition engine not initialized")
        
        self.logger.info("Processing video", video_path=str(video_path))
        
        try:
            # Extract video metadata
            metadata = await self._extract_metadata(video_path)
            
            # Perform face recognition
            face_results = await self._analyze_faces(video_path)
            
            # Create processing result
            result = ProcessingResult(
                video_path=video_path,
                metadata=metadata,
                face_detections=face_results["detections"],
                recognized_faces=face_results["recognized"],
                processing_time=face_results["processing_time"],
                timestamp=datetime.now(),
            )
            
            # Save results
            if output_dir:
                await self._save_results(result, output_dir)
            
            self.logger.info(
                "Video processing completed",
                video_path=str(video_path),
                faces_detected=len(face_results["detections"]),
                faces_recognized=len(face_results["recognized"]),
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Failed to process video", video_path=str(video_path), error=str(e))
            raise
    
    async def stitch_videos(
        self,
        video_paths: List[Path],
        output_path: Path,
        criteria: Dict[str, Any] = None,
    ) -> Path:
        """
        Stitch multiple video files together.
        
        Args:
            video_paths: List of video file paths
            output_path: Output path for stitched video
            criteria: Stitching criteria (time gap, events, etc.)
            
        Returns:
            Path to the stitched video file
        """
        self.logger.info("Stitching videos", count=len(video_paths), output=str(output_path))
        
        try:
            # Sort videos by timestamp
            sorted_videos = await self._sort_videos_by_time(video_paths)
            
            # Create temporary file list for ffmpeg
            file_list_path = output_path.parent / "file_list.txt"
            
            with open(file_list_path, "w") as f:
                for video_path in sorted_videos:
                    f.write(f"file '{video_path.absolute()}'\n")
            
            # Use ffmpeg to concatenate videos
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(file_list_path),
                "-c", "copy",
                str(output_path),
                "-y",  # Overwrite output file
            ]
            
            result = await self._run_command(cmd)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
            
            # Clean up temporary file
            file_list_path.unlink()
            
            self.logger.info("Video stitching completed", output=str(output_path))
            return output_path
            
        except Exception as e:
            self.logger.error("Failed to stitch videos", error=str(e))
            raise
    
    async def get_video_statistics(self, video_path: Path) -> Dict[str, Any]:
        """
        Get statistics for a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary containing video statistics
        """
        try:
            metadata = await self._extract_metadata(video_path)
            
            # Get file size
            file_size = video_path.stat().st_size
            
            # Calculate bitrate
            bitrate = (file_size * 8) / metadata.duration  # bits per second
            
            stats = {
                "file_size_mb": file_size / (1024 * 1024),
                "duration_seconds": metadata.duration,
                "resolution": f"{metadata.width}x{metadata.height}",
                "fps": metadata.fps,
                "bitrate_kbps": bitrate / 1000,
                "codec": metadata.codec,
                "created": metadata.created,
            }
            
            return stats
            
        except Exception as e:
            self.logger.error("Failed to get video statistics", error=str(e))
            raise
    
    async def _processing_loop(self) -> None:
        """Main processing loop for handling video files."""
        self.logger.info("Starting video processing loop")
        
        while self.is_processing:
            try:
                # Get next video from queue
                try:
                    video_path = await asyncio.wait_for(
                        self.processing_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the video
                await self.process_video(video_path)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Exception as e:
                self.logger.error("Error in processing loop", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _monitor_video_directory(self) -> None:
        """Monitor video directory for new files."""
        if not self.settings:
            return
        
        video_dir = Path(self.settings.storage.video_directory)
        video_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Monitoring video directory", directory=str(video_dir))
        
        # Track processed files
        processed_files = set()
        
        while self.is_processing:
            try:
                # Find new video files
                video_extensions = {".mp4", ".avi", ".mov", ".mkv"}
                
                for video_file in video_dir.rglob("*"):
                    if (
                        video_file.is_file()
                        and video_file.suffix.lower() in video_extensions
                        and video_file not in processed_files
                    ):
                        # Check if file is complete (not being written)
                        if await self._is_file_complete(video_file):
                            await self.processing_queue.put(video_file)
                            processed_files.add(video_file)
                            
                            self.logger.info(
                                "Queued video for processing", video=str(video_file)
                            )
                
                # Clean up old processed files from memory
                if len(processed_files) > 1000:
                    processed_files.clear()
                
                await asyncio.sleep(self.settings.processing.monitor_interval)
                
            except Exception as e:
                self.logger.error("Error in video monitoring", error=str(e))
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _extract_metadata(self, video_path: Path) -> VideoMetadata:
        """Extract metadata from video file."""
        try:
            # Use ffprobe to get video information
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]
            
            result = await self._run_command(cmd)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe failed: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Extract video stream
            video_stream = None
            for stream in data["streams"]:
                if stream["codec_type"] == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                raise RuntimeError("No video stream found")
            
            # Get file creation time
            created = datetime.fromtimestamp(video_path.stat().st_ctime)
            
            metadata = VideoMetadata(
                width=int(video_stream["width"]),
                height=int(video_stream["height"]),
                fps=float(eval(video_stream["r_frame_rate"])),
                duration=float(data["format"]["duration"]),
                codec=video_stream["codec_name"],
                created=created,
                file_size=video_path.stat().st_size,
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error("Failed to extract metadata", error=str(e))
            raise
    
    async def _analyze_faces(self, video_path: Path) -> Dict[str, Any]:
        """Analyze faces in video file."""
        start_time = datetime.now()
        
        try:
            # Open video file
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                raise RuntimeError("Could not open video file")
            
            detections = []
            recognized_faces = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every nth frame for performance
                if frame_count % self.settings.processing.frame_skip == 0:
                    # Detect faces in frame
                    face_locations = self.face_engine.detect_faces(frame)
                    
                    for face_location in face_locations:
                        # Extract face encoding
                        face_encoding = self.face_engine.get_face_encoding(frame, face_location)
                        
                        if face_encoding is not None:
                            # Recognize face
                            name = self.face_engine.recognize_face(face_encoding)
                            
                            detection = {
                                "frame": frame_count,
                                "timestamp": frame_count / cap.get(cv2.CAP_PROP_FPS),
                                "location": face_location,
                                "name": name,
                                "confidence": 0.8,  # Placeholder
                            }
                            
                            detections.append(detection)
                            
                            if name and name != "Unknown":
                                recognized_faces.append(detection)
                
                frame_count += 1
            
            cap.release()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "detections": detections,
                "recognized": recognized_faces,
                "processing_time": processing_time,
            }
            
        except Exception as e:
            self.logger.error("Failed to analyze faces", error=str(e))
            raise
    
    async def _sort_videos_by_time(self, video_paths: List[Path]) -> List[Path]:
        """Sort video files by creation time."""
        video_times = []
        
        for video_path in video_paths:
            try:
                metadata = await self._extract_metadata(video_path)
                video_times.append((video_path, metadata.created))
            except Exception as e:
                self.logger.warning("Could not get metadata for video", video=str(video_path))
                # Use file modification time as fallback
                video_times.append((video_path, datetime.fromtimestamp(video_path.stat().st_mtime)))
        
        # Sort by creation time
        video_times.sort(key=lambda x: x[1])
        
        return [video_path for video_path, _ in video_times]
    
    async def _is_file_complete(self, file_path: Path) -> bool:
        """Check if file is complete (not being written)."""
        try:
            # Get initial file size
            initial_size = file_path.stat().st_size
            
            # Wait a bit
            await asyncio.sleep(2)
            
            # Check if file size changed
            current_size = file_path.stat().st_size
            
            return initial_size == current_size
            
        except Exception:
            return False
    
    async def _save_results(self, result: ProcessingResult, output_dir: Path) -> None:
        """Save processing results to file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save results as JSON
        results_file = output_dir / f"{result.video_path.stem}_results.json"
        
        with open(results_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        self.logger.info("Results saved", file=str(results_file))
    
    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
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