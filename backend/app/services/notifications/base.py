"""Notification service abstraction (email / push). Swap with NOTIFICATION_PROVIDER."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    to: str
    subject: str
    body: str
    channel: str = "email"


class NotificationProvider(ABC):
    name = "base"

    @abstractmethod
    def send(self, msg: Message) -> str:
        """Returns a status string ('sent', 'queued', ...). Raises on failure."""
