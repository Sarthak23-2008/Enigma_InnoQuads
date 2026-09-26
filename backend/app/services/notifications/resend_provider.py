"""Optional email provider (Resend REST API). Credentials come only from environment variables."""
from __future__ import annotations

import json
import urllib.request

from app.config import get_settings
from app.services.notifications.base import Message, NotificationProvider


class ResendProvider(NotificationProvider):
    name = "resend"

    def send(self, msg: Message) -> str:
        s = get_settings()
        if not s.RESEND_API_KEY:
            raise RuntimeError("RESEND_API_KEY is not configured.")
        req = urllib.request.Request(
            "https://api.resend.com/emails", method="POST",
            data=json.dumps({"from": s.REPORT_FROM_EMAIL, "to": [msg.to], "subject": msg.subject,
                             "text": msg.body}).encode(),
            headers={"Authorization": f"Bearer {s.RESEND_API_KEY}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:  # noqa: S310 (fixed https URL)
            return "sent" if 200 <= r.status < 300 else f"error_{r.status}"
