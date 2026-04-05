"""
Unit tests for blink_lens.core.notification_service.NotificationService.

SMTP and urllib are mocked so no real network calls are made.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from urllib.error import URLError

import pytest

from blink_lens.config.settings import Settings
from blink_lens.core.notification_service import NotificationService


@pytest.fixture
def service(settings: Settings) -> NotificationService:
    return NotificationService(settings)


@pytest.fixture
def email_settings(settings: Settings) -> Settings:
    settings.notifications.enable_notifications = True
    settings.notifications.email_enabled = True
    settings.notifications.smtp_host = "smtp.example.com"
    settings.notifications.smtp_port = 587
    settings.notifications.smtp_user = "user@example.com"
    settings.notifications.smtp_password = "secret"
    settings.notifications.email_from = "from@example.com"
    settings.notifications.email_to = "to@example.com"
    return settings


@pytest.fixture
def pushbullet_settings(settings: Settings) -> Settings:
    settings.notifications.enable_notifications = True
    settings.notifications.pushbullet_enabled = True
    settings.notifications.pushbullet_api_key = "pb-test-key"
    return settings


@pytest.fixture
def webhook_settings(settings: Settings) -> Settings:
    settings.notifications.enable_notifications = True
    settings.notifications.webhook_enabled = True
    settings.notifications.webhook_url = "https://hooks.example.com/blink"
    return settings


class TestNotifyUnknownFaceGating:
    async def test_no_dispatch_when_notifications_disabled(self, service: NotificationService):
        service.settings.notifications.enable_notifications = False
        with patch.object(service, "_dispatch") as mock_dispatch:
            await service.notify_unknown_face(Path("clip.mp4"), face_count=1)
        mock_dispatch.assert_not_called()

    async def test_no_dispatch_when_type_not_configured(self, service: NotificationService):
        service.settings.notifications.notification_types = ["system_alert"]
        with patch.object(service, "_dispatch") as mock_dispatch:
            await service.notify_unknown_face(Path("clip.mp4"), face_count=1)
        mock_dispatch.assert_not_called()

    async def test_dispatches_when_enabled(self, service: NotificationService):
        service.settings.notifications.enable_notifications = True
        service.settings.notifications.notification_types = ["unknown_face"]
        with patch.object(service, "_dispatch") as mock_dispatch:
            await service.notify_unknown_face(Path("clip.mp4"), face_count=2)
        mock_dispatch.assert_called_once()


class TestEmailNotification:
    def test_sends_via_starttls(self, email_settings: Settings):
        service = NotificationService(email_settings)
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = MagicMock()
            mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
            service._send_email("Test subject", "Test body")
        mock_smtp_cls.assert_called_once_with("smtp.example.com", 587)

    def test_sends_via_ssl_on_port_465(self, email_settings: Settings):
        email_settings.notifications.smtp_port = 465
        service = NotificationService(email_settings)
        with patch("smtplib.SMTP_SSL") as mock_ssl_cls:
            mock_smtp = MagicMock()
            mock_ssl_cls.return_value.__enter__ = MagicMock(return_value=mock_smtp)
            mock_ssl_cls.return_value.__exit__ = MagicMock(return_value=False)
            service._send_email("Test subject", "Test body")
        mock_ssl_cls.assert_called_once()

    def test_skips_when_missing_smtp_host(self, settings: Settings):
        settings.notifications.email_enabled = True
        settings.notifications.smtp_host = ""
        service = NotificationService(settings)
        # Should not raise
        service._send_email("subject", "body")

    def test_handles_smtp_exception_gracefully(self, email_settings: Settings):
        service = NotificationService(email_settings)
        with patch("smtplib.SMTP", side_effect=OSError("connection refused")):
            # Should not raise
            service._send_email("subject", "body")


class TestPushbulletNotification:
    def test_sends_post_request(self, pushbullet_settings: Settings):
        service = NotificationService(pushbullet_settings)
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
            service._send_pushbullet("title", "body")
        mock_open.assert_called_once()

    def test_skips_when_no_api_key(self, settings: Settings):
        settings.notifications.pushbullet_api_key = None
        service = NotificationService(settings)
        with patch("urllib.request.urlopen") as mock_open:
            service._send_pushbullet("title", "body")
        mock_open.assert_not_called()

    def test_handles_url_error_gracefully(self, pushbullet_settings: Settings):
        service = NotificationService(pushbullet_settings)
        with patch("urllib.request.urlopen", side_effect=URLError("network error")):
            # Should not raise
            service._send_pushbullet("title", "body")


class TestWebhookNotification:
    def test_sends_json_payload(self, webhook_settings: Settings):
        service = NotificationService(webhook_settings)
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.status = 200

        captured_requests: list = []

        def capturing_urlopen(req, timeout=None):
            captured_requests.append(req)
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capturing_urlopen):
            service._send_webhook("subject", "body", {"face_count": 3})

        assert len(captured_requests) == 1
        req = captured_requests[0]
        payload = json.loads(req.data.decode())
        assert payload["subject"] == "subject"
        assert payload["face_count"] == 3
        assert "timestamp" in payload

    def test_skips_when_no_url(self, settings: Settings):
        settings.notifications.webhook_url = None
        service = NotificationService(settings)
        with patch("urllib.request.urlopen") as mock_open:
            service._send_webhook("subject", "body", {})
        mock_open.assert_not_called()

    def test_handles_url_error_gracefully(self, webhook_settings: Settings):
        service = NotificationService(webhook_settings)
        with patch("urllib.request.urlopen", side_effect=URLError("timeout")):
            # Should not raise
            service._send_webhook("subject", "body", {})


class TestSystemAlert:
    async def test_dispatches_system_alert(self, service: NotificationService):
        service.settings.notifications.enable_notifications = True
        service.settings.notifications.notification_types = ["system_alert"]
        with patch.object(service, "_dispatch") as mock_dispatch:
            await service.notify_system_alert("Disk nearly full", details="90% used")
        mock_dispatch.assert_called_once()

    async def test_no_dispatch_when_type_not_listed(self, service: NotificationService):
        service.settings.notifications.notification_types = ["unknown_face"]
        with patch.object(service, "_dispatch") as mock_dispatch:
            await service.notify_system_alert("alert")
        mock_dispatch.assert_not_called()
