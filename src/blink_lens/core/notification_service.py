"""
Notification Service for Blink Lens.

Sends alerts when unknown faces are detected. Supports email (SMTP),
Pushbullet, and generic webhooks. All channels are disabled by default
and enabled via NotificationSettings / environment variables.
"""

import json
import smtplib
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from blink_lens.config.settings import Settings


class NotificationService:
    """
    Sends alerts through configured notification channels.

    Channels are fire-and-forget: failures are logged but never raise,
    so a broken notification channel never stops video processing.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = structlog.get_logger()

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    async def notify_unknown_face(
        self,
        video_path: Path,
        face_count: int,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Send an alert that unknown face(s) were detected in a clip."""
        if not self.settings.notifications.enable_notifications:
            return
        if "unknown_face" not in self.settings.notifications.notification_types:
            return

        if timestamp is None:
            timestamp = datetime.now()

        subject = f"Blink Lens: {face_count} unknown face(s) detected"
        body = (
            f"Unknown face(s) detected in clip.\n\n"
            f"File:       {video_path.name}\n"
            f"Faces:      {face_count}\n"
            f"Detected:   {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        await self._dispatch(subject, body, {"video": str(video_path), "face_count": face_count})

    async def notify_system_alert(self, message: str, details: Optional[str] = None) -> None:
        """Send a system-level alert (storage full, service restart, etc.)."""
        if not self.settings.notifications.enable_notifications:
            return
        if "system_alert" not in self.settings.notifications.notification_types:
            return

        subject = "Blink Lens: System alert"
        body = message if not details else f"{message}\n\nDetails:\n{details}"
        await self._dispatch(subject, body, {"message": message})

    # -------------------------------------------------------------------------
    # Internal dispatch
    # -------------------------------------------------------------------------

    async def _dispatch(self, subject: str, body: str, metadata: Dict[str, Any]) -> None:
        """Send through all enabled channels. Errors are logged, not raised."""
        cfg = self.settings.notifications

        if cfg.email_enabled:
            self._send_email(subject, body)

        if cfg.pushbullet_enabled:
            self._send_pushbullet(subject, body)

        if cfg.webhook_enabled:
            self._send_webhook(subject, body, metadata)

    # -------------------------------------------------------------------------
    # Email (SMTP)
    # -------------------------------------------------------------------------

    def _send_email(self, subject: str, body: str) -> None:
        cfg = self.settings.notifications

        missing = [
            field for field in ("smtp_host", "email_from", "email_to")
            if not getattr(cfg, field)
        ]
        if missing:
            self.logger.warning(
                "Email notification skipped — missing config", missing=missing
            )
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = cfg.email_from
            msg["To"] = cfg.email_to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            context = ssl.create_default_context()

            if cfg.smtp_port == 465:
                with smtplib.SMTP_SSL(cfg.smtp_host, cfg.smtp_port, context=context) as server:
                    if cfg.smtp_user and cfg.smtp_password:
                        server.login(cfg.smtp_user, cfg.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    if cfg.smtp_user and cfg.smtp_password:
                        server.login(cfg.smtp_user, cfg.smtp_password)
                    server.send_message(msg)

            self.logger.info("Email notification sent", to=cfg.email_to, subject=subject)

        except Exception as e:
            self.logger.error("Failed to send email notification", error=str(e))

    # -------------------------------------------------------------------------
    # Pushbullet
    # -------------------------------------------------------------------------

    def _send_pushbullet(self, title: str, body: str) -> None:
        cfg = self.settings.notifications

        if not cfg.pushbullet_api_key:
            self.logger.warning("Pushbullet notification skipped — no API key configured")
            return

        try:
            payload = json.dumps({"type": "note", "title": title, "body": body}).encode()
            req = urllib.request.Request(
                "https://api.pushbullet.com/v2/pushes",
                data=payload,
                headers={
                    "Access-Token": cfg.pushbullet_api_key,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    self.logger.info("Pushbullet notification sent", title=title)
                else:
                    self.logger.warning(
                        "Pushbullet returned non-200", status=resp.status
                    )

        except urllib.error.URLError as e:
            self.logger.error("Failed to send Pushbullet notification", error=str(e))
        except Exception as e:
            self.logger.error("Failed to send Pushbullet notification", error=str(e))

    # -------------------------------------------------------------------------
    # Webhook
    # -------------------------------------------------------------------------

    def _send_webhook(self, subject: str, body: str, metadata: Dict[str, Any]) -> None:
        cfg = self.settings.notifications

        if not cfg.webhook_url:
            self.logger.warning("Webhook notification skipped — no URL configured")
            return

        try:
            payload = json.dumps(
                {
                    "subject": subject,
                    "body": body,
                    "timestamp": datetime.now().isoformat(),
                    **metadata,
                }
            ).encode()
            req = urllib.request.Request(
                cfg.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 201, 202, 204):
                    self.logger.info("Webhook notification sent", url=cfg.webhook_url)
                else:
                    self.logger.warning(
                        "Webhook returned unexpected status",
                        status=resp.status,
                        url=cfg.webhook_url,
                    )

        except urllib.error.URLError as e:
            self.logger.error("Failed to send webhook notification", error=str(e))
        except Exception as e:
            self.logger.error("Failed to send webhook notification", error=str(e))
