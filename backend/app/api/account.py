from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.security import verify_password
from app.database.session import get_db
from app.models import FoodLog, Goal, ScanResult, SymptomLog, User
from app.schemas import AccountUpdate, PasswordConfirm, UserOut
from app.services.common import (get_profile, get_user_settings, iso, log_out, profile_dict, scan_out, settings_dict,
                                 symptom_out)

router = APIRouter(prefix="/account", tags=["account"])
DEMO_LOCKED = "The shared demo account can't be changed or deleted. Create your own account to try this."


@router.put("")
def update_account(body: AccountUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.is_demo and body.email:
        raise HTTPException(status.HTTP_403_FORBIDDEN, DEMO_LOCKED)
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(422, "Name is required.")
        user.name = name
    if body.email and body.email.lower() != user.email:
        if not body.current_password or not verify_password(body.current_password, user.password_hash):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Enter your current password to change your email.")
        if db.query(User).filter(func.lower(User.email) == body.email.lower()).first():
            raise HTTPException(status.HTTP_409_CONFLICT, "That email is already in use.")
        user.email = body.email.lower()
    db.commit()
    return UserOut.model_validate(user)


@router.get("/export")
def export_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Everything SafeBite stores about the user (data portability)."""
    uid = user.user_id
    return {
        "exported_at": iso(datetime.now(timezone.utc)),
        "account": UserOut.model_validate(user).model_dump(mode="json"),
        "profile": profile_dict(get_profile(db, user)),
        "settings": settings_dict(*get_user_settings(db, user)),
        "goals": [{"goal_type": g.goal_type, "target": g.target, "active": g.active} for g in db.query(Goal).filter_by(user_id=uid)],
        "food_logs": [log_out(l) for l in db.query(FoodLog).filter_by(user_id=uid).order_by(FoodLog.consumed_at)],
        "analyses": [scan_out(s) for s in db.query(ScanResult).filter_by(user_id=uid).order_by(ScanResult.created_at)],
        "symptoms": [symptom_out(s) for s in db.query(SymptomLog).filter_by(user_id=uid)],
    }


@router.post("/delete", status_code=204)
@router.delete("", status_code=204, include_in_schema=False)
def delete_account(body: PasswordConfirm, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.is_demo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, DEMO_LOCKED)
    if body.confirm_text.strip().upper() != "DELETE":
        raise HTTPException(422, "Type DELETE to confirm.")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Password is incorrect.")
    db.delete(user)  # FK ON DELETE CASCADE + ORM cascade remove all of the user's data
    db.commit()
    return None
