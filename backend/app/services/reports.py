"""Scheduled diet reports (weekly / bi-weekly / monthly). Reuses the same Diet Pattern Engine output
as /trends; only the trigger differs (a scheduler instead of a page visit)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import NotificationOutbox, NotificationSetting, User
from app.services.common import diet_analysis
from app.services.notifications import Message, get_notification_provider

log = logging.getLogger("safebite.reports")
PERIODS = {"weekly": (7, 15), "biweekly": (14, 15), "monthly": (30, 30)}  # (send every N days, analysis window)


def build_report(db: Session, user: User, period: str) -> tuple[str, str]:
    _, window = PERIODS[period]
    a = diet_analysis(db, user, window)
    label = {"weekly": "Weekly", "biweekly": "Bi-weekly", "monthly": "Monthly"}[period]
    subject = f"Your SafeBite {label.lower()} diet report"
    lines = [f"Hi {user.name},", "", f"{label} dietary pattern summary ({a['start_date']} to {a['end_date']}):", ""]
    if a["status"] == "insufficient":
        lines.append("Keep logging your meals. More data will help SafeBite identify meaningful dietary patterns.")
    else:
        lines.append(a["summary"])
        lines.append("")
        for m in a["metrics"]:
            lines.append(f"- {m['label']}: {m['classification']} ({m['value']} {m['unit']})")
        for al in a["alerts"]:
            lines += ["", "Pattern alert: " + al["message"], "Suggestion: " + al["action"]]
        for g in a["goal_progress"]:
            lines += ["", f"Goal ({g['label']}): {g['statement']}"]
    lines += ["", "This report reflects your logged foods only. It is not medical advice.",
              "Open SafeBite > Trends for charts and details."]
    return subject, "\n".join(lines)


def send_report(db: Session, user: User, period: str, channel: str = "email") -> NotificationOutbox:
    subject, body = build_report(db, user, period)
    provider = get_notification_provider()
    try:
        status = provider.send(Message(to=user.email, subject=subject, body=body, channel=channel))
    except Exception as e:  # never crash the scheduler on one user
        log.warning("report send failed", extra={"user_id": user.user_id, "error": str(e)})
        status = "failed"
    rec = NotificationOutbox(user_id=user.user_id, channel=channel, subject=subject, body=body,
                             provider=provider.name, status=status)
    db.add(rec)
    db.commit()
    return rec


def due_periods(ns: NotificationSetting, now: datetime) -> list[str]:
    due = []
    flags = {"weekly": ns.weekly_reports, "biweekly": ns.biweekly_reports, "monthly": ns.monthly_reports}
    for period, enabled in flags.items():
        if not enabled:
            continue
        last = (ns.last_sent or {}).get(period)
        every, _ = PERIODS[period]
        if not last or now - datetime.fromisoformat(last) >= timedelta(days=every):
            due.append(period)
    return due


def run_due_reports(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    sent = 0
    for ns in db.query(NotificationSetting).all():
        periods = due_periods(ns, now)
        if not periods:
            continue
        user = db.get(User, ns.user_id)
        if not user:
            continue
        last = dict(ns.last_sent or {})
        for p in periods:
            send_report(db, user, p, channel="email" if ns.email_enabled else "push")
            last[p] = now.isoformat()
            sent += 1
        ns.last_sent = last
        db.commit()
    return sent
