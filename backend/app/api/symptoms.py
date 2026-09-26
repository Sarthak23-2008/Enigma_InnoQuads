"""Phase 2 — symptom check-ins for unpackaged foods, 2–3 days after eating. Never a diagnosis."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models import FoodLog, SymptomLog, User
from app.schemas import SymptomIn
from app.services.common import aware, log_out, symptom_out

router = APIRouter(prefix="/symptoms", tags=["symptoms"])
PROMPT_AFTER = timedelta(hours=48)
PROMPT_UNTIL = timedelta(days=4)  # "after 2–3 days": ask in the 48–96 h window
QUESTION = "Any discomfort or reaction since eating this?"


def symptom_due(l: FoodLog, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    age = now - aware(l.consumed_at)
    return bool(l.is_unpackaged) and PROMPT_AFTER <= age <= PROMPT_UNTIL


def association_for(db: Session, user: User, food_name: str) -> dict | None:
    n = db.query(func.count(SymptomLog.symptom_id)).join(FoodLog, FoodLog.log_id == SymptomLog.food_log_id).filter(
        SymptomLog.user_id == user.user_id, SymptomLog.severity != "none",
        func.lower(FoodLog.food_name) == food_name.lower()).scalar() or 0
    if n >= 2:
        return {"count": n,
                "message": "You have logged similar symptoms after this food multiple times.",
                "note": "This is a pattern in your own logs, not a diagnosis. Consider discussing it with a qualified professional."}
    return None


@router.get("/pending")
def pending(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    rows = db.query(FoodLog).outerjoin(SymptomLog, SymptomLog.food_log_id == FoodLog.log_id).filter(
        FoodLog.user_id == user.user_id, FoodLog.is_unpackaged.is_(True), SymptomLog.symptom_id.is_(None),
        FoodLog.consumed_at <= now - PROMPT_AFTER, FoodLog.consumed_at >= now - PROMPT_UNTIL,
    ).order_by(FoodLog.consumed_at.desc()).limit(5).all()
    return {"question": QUESTION, "items": [log_out(r) for r in rows]}


@router.post("", status_code=201)
def submit(body: SymptomIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    l = db.get(FoodLog, body.food_log_id)
    if not l or l.user_id != user.user_id:
        raise HTTPException(404, "Log entry not found.")
    s = db.query(SymptomLog).filter_by(food_log_id=l.log_id).first()
    if s:
        s.severity, s.symptom, s.notes = body.severity, body.symptom.strip(), body.notes.strip()
    else:
        s = SymptomLog(user_id=user.user_id, food_log_id=l.log_id, severity=body.severity,
                       symptom=body.symptom.strip(), notes=body.notes.strip())
        db.add(s)
    db.commit()
    return {**symptom_out(s), "association": association_for(db, user, l.food_name),
            "message": "Thanks — your check-in was saved."}


@router.get("")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(SymptomLog, FoodLog).join(FoodLog, FoodLog.log_id == SymptomLog.food_log_id).filter(
        SymptomLog.user_id == user.user_id).order_by(SymptomLog.created_at.desc()).limit(100).all()
    return [{**symptom_out(s), "food_name": l.food_name, "consumed_at": log_out(l)["consumed_at"]} for s, l in rows]
