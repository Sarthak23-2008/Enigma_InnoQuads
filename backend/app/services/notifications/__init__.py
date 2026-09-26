from app.config import get_settings
from app.services.notifications.base import Message, NotificationProvider


def get_notification_provider() -> NotificationProvider:
    if get_settings().NOTIFICATION_PROVIDER.lower() == "resend":
        from app.services.notifications.resend_provider import ResendProvider
        return ResendProvider()
    from app.services.notifications.mock_provider import MockProvider
    return MockProvider()


__all__ = ["Message", "NotificationProvider", "get_notification_provider"]
