"""
Settings configuration for Blink Sync Brain.

This module handles configuration management for the Blink camera
system enhancement application.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass
class StorageSettings:
    """Storage configuration settings."""
    virtual_drive_path: Path = Path("/var/blink_storage/virtual_drive.img")
    virtual_drive_size_gb: int = 32
    video_directory: Path = Path("/var/blink_storage/videos")
    results_directory: Path = Path("/var/blink_storage/results")
    cleanup_threshold: float = 80.0  # Percentage
    retention_days: int = 30
    monitor_interval: int = 300  # seconds


@dataclass
class ProcessingSettings:
    """Video processing configuration settings."""
    frame_skip: int = 5  # Process every nth frame
    monitor_interval: int = 60  # seconds
    max_concurrent_videos: int = 2
    processing_timeout: int = 300  # seconds
    enable_face_recognition: bool = True
    enable_video_stitching: bool = True


@dataclass
class FaceRecognitionSettings:
    """Face recognition configuration settings."""
    database_path: Path = Path("/var/blink_storage/face_database.pkl")
    confidence_threshold: float = 0.6
    tolerance: float = 0.6
    min_face_size: int = 20
    enable_batch_processing: bool = True


@dataclass
class NotificationSettings:
    """Notification configuration settings."""
    enable_notifications: bool = True
    notification_types: list = None
    email_enabled: bool = False
    pushbullet_enabled: bool = False
    webhook_enabled: bool = False
    
    def __post_init__(self):
        if self.notification_types is None:
            self.notification_types = ["unknown_face", "motion_detected", "system_alert"]


@dataclass
class NetworkSettings:
    """Network configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8080
    enable_ssl: bool = False
    ssl_cert_path: Optional[Path] = None
    ssl_key_path: Optional[Path] = None


@dataclass
class LoggingSettings:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "json"
    file_path: Optional[Path] = None
    max_size_mb: int = 100
    backup_count: int = 5


@dataclass
class Settings:
    """Main application settings."""
    
    # Load environment variables
    load_dotenv()
    
    # Application settings
    app_name: str = "Blink Sync Brain"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Component settings
    storage: StorageSettings = StorageSettings()
    processing: ProcessingSettings = ProcessingSettings()
    face_recognition: FaceRecognitionSettings = FaceRecognitionSettings()
    notifications: NotificationSettings = NotificationSettings()
    network: NetworkSettings = NetworkSettings()
    logging: LoggingSettings = LoggingSettings()
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Override with environment variables if present
        self._load_from_env()
    
    def _load_from_env(self):
        """Load settings from environment variables."""
        # Storage settings
        if os.getenv("VIRTUAL_DRIVE_PATH"):
            self.storage.virtual_drive_path = Path(os.getenv("VIRTUAL_DRIVE_PATH"))
        
        if os.getenv("VIRTUAL_DRIVE_SIZE_GB"):
            self.storage.virtual_drive_size_gb = int(os.getenv("VIRTUAL_DRIVE_SIZE_GB"))
        
        if os.getenv("VIDEO_DIRECTORY"):
            self.storage.video_directory = Path(os.getenv("VIDEO_DIRECTORY"))
        
        # Processing settings
        if os.getenv("FRAME_SKIP"):
            self.processing.frame_skip = int(os.getenv("FRAME_SKIP"))
        
        if os.getenv("MAX_CONCURRENT_VIDEOS"):
            self.processing.max_concurrent_videos = int(os.getenv("MAX_CONCURRENT_VIDEOS"))
        
        # Face recognition settings
        if os.getenv("FACE_DATABASE_PATH"):
            self.face_recognition.database_path = Path(os.getenv("FACE_DATABASE_PATH"))
        
        if os.getenv("FACE_CONFIDENCE_THRESHOLD"):
            self.face_recognition.confidence_threshold = float(os.getenv("FACE_CONFIDENCE_THRESHOLD"))
        
        # Network settings
        if os.getenv("HOST"):
            self.network.host = os.getenv("HOST")
        
        if os.getenv("PORT"):
            self.network.port = int(os.getenv("PORT"))
        
        # Logging settings
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")
        
        if os.getenv("LOG_FILE"):
            self.logging.file_path = Path(os.getenv("LOG_FILE"))
    
    @classmethod
    def from_file(cls, config_path: Path) -> "Settings":
        """
        Load settings from a YAML configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Settings instance
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        
        # Create settings instance
        settings = cls()
        
        # Update settings from config file
        settings._update_from_dict(config_data)
        
        return settings
    
    def _update_from_dict(self, config_data: dict):
        """Update settings from a dictionary."""
        # Storage settings
        if "storage" in config_data:
            storage_data = config_data["storage"]
            if "virtual_drive_path" in storage_data:
                self.storage.virtual_drive_path = Path(storage_data["virtual_drive_path"])
            if "virtual_drive_size_gb" in storage_data:
                self.storage.virtual_drive_size_gb = storage_data["virtual_drive_size_gb"]
            if "video_directory" in storage_data:
                self.storage.video_directory = Path(storage_data["video_directory"])
            if "cleanup_threshold" in storage_data:
                self.storage.cleanup_threshold = storage_data["cleanup_threshold"]
            if "retention_days" in storage_data:
                self.storage.retention_days = storage_data["retention_days"]
        
        # Processing settings
        if "processing" in config_data:
            processing_data = config_data["processing"]
            if "frame_skip" in processing_data:
                self.processing.frame_skip = processing_data["frame_skip"]
            if "max_concurrent_videos" in processing_data:
                self.processing.max_concurrent_videos = processing_data["max_concurrent_videos"]
            if "enable_face_recognition" in processing_data:
                self.processing.enable_face_recognition = processing_data["enable_face_recognition"]
            if "enable_video_stitching" in processing_data:
                self.processing.enable_video_stitching = processing_data["enable_video_stitching"]
        
        # Face recognition settings
        if "face_recognition" in config_data:
            face_data = config_data["face_recognition"]
            if "database_path" in face_data:
                self.face_recognition.database_path = Path(face_data["database_path"])
            if "confidence_threshold" in face_data:
                self.face_recognition.confidence_threshold = face_data["confidence_threshold"]
            if "tolerance" in face_data:
                self.face_recognition.tolerance = face_data["tolerance"]
        
        # Notification settings
        if "notifications" in config_data:
            notif_data = config_data["notifications"]
            if "enable_notifications" in notif_data:
                self.notifications.enable_notifications = notif_data["enable_notifications"]
            if "notification_types" in notif_data:
                self.notifications.notification_types = notif_data["notification_types"]
            if "email_enabled" in notif_data:
                self.notifications.email_enabled = notif_data["email_enabled"]
            if "pushbullet_enabled" in notif_data:
                self.notifications.pushbullet_enabled = notif_data["pushbullet_enabled"]
        
        # Network settings
        if "network" in config_data:
            network_data = config_data["network"]
            if "host" in network_data:
                self.network.host = network_data["host"]
            if "port" in network_data:
                self.network.port = network_data["port"]
            if "enable_ssl" in network_data:
                self.network.enable_ssl = network_data["enable_ssl"]
        
        # Logging settings
        if "logging" in config_data:
            logging_data = config_data["logging"]
            if "level" in logging_data:
                self.logging.level = logging_data["level"]
            if "file_path" in logging_data:
                self.logging.file_path = Path(logging_data["file_path"])
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "storage": {
                "virtual_drive_path": str(self.storage.virtual_drive_path),
                "virtual_drive_size_gb": self.storage.virtual_drive_size_gb,
                "video_directory": str(self.storage.video_directory),
                "results_directory": str(self.storage.results_directory),
                "cleanup_threshold": self.storage.cleanup_threshold,
                "retention_days": self.storage.retention_days,
                "monitor_interval": self.storage.monitor_interval,
            },
            "processing": {
                "frame_skip": self.processing.frame_skip,
                "monitor_interval": self.processing.monitor_interval,
                "max_concurrent_videos": self.processing.max_concurrent_videos,
                "processing_timeout": self.processing.processing_timeout,
                "enable_face_recognition": self.processing.enable_face_recognition,
                "enable_video_stitching": self.processing.enable_video_stitching,
            },
            "face_recognition": {
                "database_path": str(self.face_recognition.database_path),
                "confidence_threshold": self.face_recognition.confidence_threshold,
                "tolerance": self.face_recognition.tolerance,
                "min_face_size": self.face_recognition.min_face_size,
                "enable_batch_processing": self.face_recognition.enable_batch_processing,
            },
            "notifications": {
                "enable_notifications": self.notifications.enable_notifications,
                "notification_types": self.notifications.notification_types,
                "email_enabled": self.notifications.email_enabled,
                "pushbullet_enabled": self.notifications.pushbullet_enabled,
                "webhook_enabled": self.notifications.webhook_enabled,
            },
            "network": {
                "host": self.network.host,
                "port": self.network.port,
                "enable_ssl": self.network.enable_ssl,
                "ssl_cert_path": str(self.network.ssl_cert_path) if self.network.ssl_cert_path else None,
                "ssl_key_path": str(self.network.ssl_key_path) if self.network.ssl_key_path else None,
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file_path": str(self.logging.file_path) if self.logging.file_path else None,
                "max_size_mb": self.logging.max_size_mb,
                "backup_count": self.logging.backup_count,
            },
        }
    
    def save_to_file(self, config_path: Path) -> None:
        """
        Save settings to a YAML configuration file.
        
        Args:
            config_path: Path to save the configuration file
        """
        config_data = self.to_dict()
        
        # Create directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
    
    def validate(self) -> list:
        """
        Validate settings and return any errors.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check storage paths
        if not self.storage.virtual_drive_path.parent.exists():
            errors.append(f"Virtual drive directory does not exist: {self.storage.virtual_drive_path.parent}")
        
        # Check processing settings
        if self.processing.frame_skip < 1:
            errors.append("Frame skip must be at least 1")
        
        if self.processing.max_concurrent_videos < 1:
            errors.append("Max concurrent videos must be at least 1")
        
        # Check face recognition settings
        if not (0.0 <= self.face_recognition.confidence_threshold <= 1.0):
            errors.append("Face confidence threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self.face_recognition.tolerance <= 1.0):
            errors.append("Face tolerance must be between 0.0 and 1.0")
        
        # Check network settings
        if not (1 <= self.network.port <= 65535):
            errors.append("Port must be between 1 and 65535")
        
        # Check logging settings
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_log_levels:
            errors.append(f"Log level must be one of: {valid_log_levels}")
        
        return errors 