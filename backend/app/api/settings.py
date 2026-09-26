from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models import NotificationOutbox, User
from app.schemas import SettingsIn
from app.services.common import get_user_settings, iso, settings_dict
from app.services.reports import send_report

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def read_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return settings_dict(*get_user_settings(db, user))


@router.put("")
def update_settings(body: SettingsIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    us, ns = get_user_settings(db, user)
    for section, target in ((body.notifications, ns), (body.input_prefs, us), (body.accessibility, us)):
        if section is None:
            continue
        for k, v in section.model_dump(exclude_none=True).items():
            setattr(target, k, v)
    db.commit()
    return settings_dict(us, ns)


@router.post("/notifications/send-test")
def send_test(period: str = Query("weekly", pattern="^(weekly|biweekly|monthly)$"),
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a report now through the configured provider (mock in development)."""
    rec = send_report(db, user, period)
    us, ns = get_user_settings(db, user)
    ns.last_sent = {**(ns.last_sent or {}), period: datetime.now(timezone.utc).isoformat()}
    db.commit()
    if rec.status == "failed":
        raise HTTPException(502, "The report couldn't be sent. Check the notification provider settings.")
    return {"outbox_id": rec.outbox_id, "status": rec.status, "provider": rec.provider, "subject": rec.subject,
            "body": rec.body}


@router.get("/notifications/outbox")
def outbox(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(NotificationOutbox).filter_by(user_id=user.user_id).order_by(NotificationOutbox.created_at.desc()).limit(10)
    return [{"outbox_id": r.outbox_id, "channel": r.channel, "subject": r.subject, "body": r.body,
             "provider": r.provider, "status": r.status, "created_at": iso(r.created_at)} for r in rows]
