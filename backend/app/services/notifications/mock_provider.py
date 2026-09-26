"""Local-development provider: nothing leaves the machine; the message is logged and stored in
the notification_outbox table so it can be inspected in the app (Settings > Notifications)."""
from __future__ import annotations

import logging

from app.services.notifications.base import Message, NotificationProvider

log = logging.getLogger("safebite.notify")


class MockProvider(NotificationProvider):
    name = "mock"

    def send(self, msg: Message) -> str:
        log.info("mock notification", extra={"to": msg.to, "subject": msg.subject, "channel": msg.channel})
        return "delivered_mock"
