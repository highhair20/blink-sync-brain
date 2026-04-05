"""
Video Processor for Blink Lens.

This module handles video processing, analysis, and management for the
Blink camera system enhancement.
"""

import asyncio
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import structlog

from blink_lens.config.settings import Settings
from blink_lens.core.face_recognition import FaceRecognitionEngine
from blink_lens.core.utils import run_command
from blink_lens.models.processing_result import ProcessingResult
from blink_lens.models.video_metadata import VideoMetadata


class VideoProcessor:
    """
    Handles video processing and analysis for Blink camera recordings.

    This class manages video file processing, face recognition, video stitching,
    and storage management for the Blink camera system.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the Video Processor."""
        self.settings = settings
        self.logger = structlog.get_logger()
        self.face_engine: Optional[FaceRecognitionEngine] = None
        self.processing_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.is_processing = False
        self._tasks: List[asyncio.Task] = []

    async def start_processing(self, face_engine: FaceRecognitionEngine) -> None:
        """
        Start the video processing service.

        Args:
            face_engine: Face recognition engine instance
        """
        self.face_engine = face_engine
        self.is_processing = True

        self.logger.info("Starting video processing service")

        # Retain task handles so exceptions are observable and tasks can be cancelled
        proc_task = asyncio.create_task(self._processing_loop())
        proc_task.add_done_callback(self._on_background_task_done)
        self._tasks.append(proc_task)

        monitor_task = asyncio.create_task(self._monitor_video_directory())
        monitor_task.add_done_callback(self._on_background_task_done)
        self._tasks.append(monitor_task)

        self.logger.info("Video processing service started")

    def _on_background_task_done(self, task: "asyncio.Task[None]") -> None:
        """Log any unhandled exception from a background task."""
        if not task.cancelled():
            exc = task.exception()
            if exc:
                self.logger.error(
                    "Background task terminated unexpectedly", error=str(exc)
                )

    async def stop_processing(self) -> None:
        """Stop the video processing service and cancel background tasks."""
        self.logger.info("Stopping video processing service")
        self.is_processing = False

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

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
            metadata = await self._extract_metadata(video_path)
            face_results = await self._analyze_faces(video_path)

            result = ProcessingResult(
                video_path=video_path,
                metadata=metadata,
                face_detections=face_results["detections"],
                recognized_faces=face_results["recognized"],
                processing_time=face_results["processing_time"],
                timestamp=datetime.now(),
            )

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
            self.logger.error(
                "Failed to process video", video_path=str(video_path), error=str(e)
            )
            raise

    async def stitch_videos(
        self,
        video_paths: List[Path],
        output_path: Path,
        criteria: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Stitch multiple video files together.

        Args:
            video_paths: List of video file paths
            output_path: Output path for stitched video
            criteria: Stitching criteria (time gap, events, etc.) — reserved for future use

        Returns:
            Path to the stitched video file
        """
        self.logger.info(
            "Stitching videos", count=len(video_paths), output=str(output_path)
        )

        sorted_videos = await self._sort_videos_by_time(video_paths)

        # Write ffmpeg concat list to a uniquely named temp file to avoid collisions
        file_list_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=output_path.parent,
                suffix=".txt",
                delete=False,
                prefix="blink_concat_",
            ) as f:
                file_list_path = Path(f.name)
                for vp in sorted_videos:
                    f.write(f"file '{vp.absolute()}'\n")

            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(file_list_path),
                "-c", "copy",
                str(output_path),
                "-y",
            ]

            result = await self._run_command(cmd)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        except Exception as e:
            self.logger.error("Failed to stitch videos", error=str(e))
            raise
        finally:
            if file_list_path and file_list_path.exists():
                file_list_path.unlink()

        self.logger.info("Video stitching completed", output=str(output_path))
        return output_path

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
            file_size = video_path.stat().st_size
            bitrate = (file_size * 8) / metadata.duration

            return {
                "file_size_mb": file_size / (1024 * 1024),
                "duration_seconds": metadata.duration,
                "resolution": f"{metadata.width}x{metadata.height}",
                "fps": metadata.fps,
                "bitrate_kbps": bitrate / 1000,
                "codec": metadata.codec,
                "created": metadata.created,
            }

        except Exception as e:
            self.logger.error("Failed to get video statistics", error=str(e))
            raise

    # -------------------------------------------------------------------------
    # Background loops
    # -------------------------------------------------------------------------

    async def _processing_loop(self) -> None:
        """Main processing loop for handling video files."""
        self.logger.info("Starting video processing loop")

        while self.is_processing:
            try:
                try:
                    video_path = await asyncio.wait_for(
                        self.processing_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                try:
                    await self.process_video(video_path)
                finally:
                    # Always release the queue slot, even if processing raises
                    self.processing_queue.task_done()

            except Exception as e:
                self.logger.error("Error in processing loop", error=str(e))
                await asyncio.sleep(5)

    async def _monitor_video_directory(self) -> None:
        """Monitor video directory for new files."""
        if not self.settings:
            return

        video_dir = Path(self.settings.storage.video_directory)
        video_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("Monitoring video directory", directory=str(video_dir))

        # Track processed files in insertion order so eviction removes oldest entries
        processed_files: Dict[Path, None] = {}

        while self.is_processing:
            try:
                video_extensions = {".mp4", ".avi", ".mov", ".mkv"}
                candidates = [
                    f for f in video_dir.rglob("*")
                    if f.is_file()
                    and f.suffix.lower() in video_extensions
                    and f not in processed_files
                ]

                if candidates:
                    # Check all candidates in parallel — serial would be 2s × N
                    complete_flags = await asyncio.gather(
                        *[self._is_file_complete(f) for f in candidates]
                    )
                    for video_file, is_complete in zip(candidates, complete_flags):
                        if is_complete:
                            await self.processing_queue.put(video_file)
                            processed_files[video_file] = None
                            self.logger.info(
                                "Queued video for processing", video=str(video_file)
                            )

                # Evict oldest half when the tracking dict exceeds 1000 entries
                if len(processed_files) > 1000:
                    oldest = list(processed_files.keys())[:500]
                    for k in oldest:
                        del processed_files[k]

                await asyncio.sleep(self.settings.processing.monitor_interval)

            except Exception as e:
                self.logger.error("Error in video monitoring", error=str(e))
                await asyncio.sleep(30)

    # -------------------------------------------------------------------------
    # Core processing
    # -------------------------------------------------------------------------

    async def _extract_metadata(self, video_path: Path) -> VideoMetadata:
        """Extract metadata from video file using ffprobe."""
        try:
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

            video_stream = next(
                (s for s in data["streams"] if s["codec_type"] == "video"), None
            )
            if not video_stream:
                raise RuntimeError("No video stream found")

            created = datetime.fromtimestamp(video_path.stat().st_ctime)

            fps_parts = video_stream["r_frame_rate"].split("/")
            fps = (
                float(fps_parts[0]) / float(fps_parts[1])
                if len(fps_parts) == 2
                else float(fps_parts[0])
            )

            return VideoMetadata(
                width=int(video_stream["width"]),
                height=int(video_stream["height"]),
                fps=fps,
                duration=float(data["format"]["duration"]),
                codec=video_stream["codec_name"],
                created=created,
                file_size=video_path.stat().st_size,
            )

        except Exception as e:
            self.logger.error("Failed to extract metadata", error=str(e))
            raise

    def _sync_analyze_faces(self, video_path: Path) -> Dict[str, Any]:
        """
        CPU-bound frame-by-frame face detection loop.

        This is a plain synchronous method intentionally — it is called via
        run_in_executor so it runs in a thread pool and does not block the event loop.
        """
        if not self.settings:
            raise RuntimeError("VideoProcessor settings not configured")
        if not self.face_engine:
            raise RuntimeError("Face engine not initialized")

        start_time = datetime.now()
        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise RuntimeError("Could not open video file")

        detections: List[Dict[str, Any]] = []
        recognized_faces: List[Dict[str, Any]] = []
        frame_count = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % self.settings.processing.frame_skip == 0:
                    face_locations = self.face_engine.detect_faces(frame)

                    for face_location in face_locations:
                        face_encoding = self.face_engine.get_face_encoding(
                            frame, face_location
                        )
                        if face_encoding is not None:
                            name, confidence = (
                                self.face_engine.recognize_face_with_confidence(
                                    face_encoding
                                )
                            )
                            detection: Dict[str, Any] = {
                                "frame": frame_count,
                                "timestamp": frame_count / cap.get(cv2.CAP_PROP_FPS),
                                "location": face_location,
                                "name": name,
                                "confidence": confidence,
                            }
                            detections.append(detection)
                            if name and name != "Unknown":
                                recognized_faces.append(detection)

                frame_count += 1
        finally:
            cap.release()

        processing_time = (datetime.now() - start_time).total_seconds()
        return {
            "detections": detections,
            "recognized": recognized_faces,
            "processing_time": processing_time,
        }

    async def _analyze_faces(self, video_path: Path) -> Dict[str, Any]:
        """
        Offload CPU-bound face analysis to a thread executor.

        cv2 frame decode and face_recognition are blocking C-extensions — running
        them directly in an async method would stall the event loop for the full
        duration of the clip.
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, self._sync_analyze_faces, video_path
            )
        except Exception as e:
            self.logger.error(
                "Failed to analyze faces", video_path=str(video_path), error=str(e)
            )
            raise

    async def _sort_videos_by_time(self, video_paths: List[Path]) -> List[Path]:
        """Sort video files by creation time using parallel ffprobe calls."""

        async def _get_time(p: Path) -> Tuple[Path, datetime]:
            try:
                meta = await self._extract_metadata(p)
                return p, meta.created
            except Exception:
                self.logger.warning(
                    "Could not get metadata for video — using mtime", video=str(p)
                )
                return p, datetime.fromtimestamp(p.stat().st_mtime)

        results = await asyncio.gather(*[_get_time(p) for p in video_paths])
        results_sorted = sorted(results, key=lambda x: x[1])
        return [p for p, _ in results_sorted]

    async def _is_file_complete(self, file_path: Path) -> bool:
        """Check if file is complete (not being written) by comparing size twice."""
        try:
            initial_size = file_path.stat().st_size
            await asyncio.sleep(2)
            return initial_size == file_path.stat().st_size
        except Exception:
            return False

    async def _save_results(self, result: ProcessingResult, output_dir: Path) -> None:
        """Save processing results to JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = output_dir / f"{result.video_path.stem}_results.json"
        with open(results_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        self.logger.info("Results saved", file=str(results_file))

    async def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Delegate to the shared async run_command utility."""
        return await run_command(cmd)
