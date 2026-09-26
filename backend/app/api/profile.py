from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models import Goal, User
from app.schemas import (ALLERGY_OPTIONS, CONDITION_OPTIONS, GOAL_OPTIONS, INTOLERANCE_OPTIONS, PREFERENCE_OPTIONS,
                         ProfileIn)
from app.services.common import get_profile, profile_dict

router = APIRouter(prefix="/profile", tags=["profile"])


def sync_goals(db: Session, user: User, goal_types: list[str]) -> None:
    """Profile goals and the goals table stay in sync (the goals table also stores targets)."""
    existing = {g.goal_type: g for g in db.query(Goal).filter_by(user_id=user.user_id).all()}
    for gt, g in existing.items():
        g.active = gt in goal_types
    for gt in goal_types:
        if gt not in existing:
            db.add(Goal(user_id=user.user_id, goal_type=gt, active=True))


@router.get("/options")
def options():
    return {"allergies": ALLERGY_OPTIONS, "intolerances": INTOLERANCE_OPTIONS, "preferences": PREFERENCE_OPTIONS,
            "health_conditions": CONDITION_OPTIONS, "goals": GOAL_OPTIONS}


@router.get("")
def read_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {**profile_dict(get_profile(db, user)), "onboarding_complete": user.onboarding_complete}


@router.put("")
def update_profile(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = get_profile(db, user)
    p.allergies, p.intolerances = body.allergies, body.intolerances
    p.dietary_preferences, p.health_conditions, p.goals = body.dietary_preferences, body.health_conditions, body.goals
    sync_goals(db, user, body.goals)
    if body.complete_onboarding:
        user.onboarding_complete = True
    db.commit()
    return {**profile_dict(p), "onboarding_complete": user.onboarding_complete}
