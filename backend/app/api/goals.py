from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models import Goal, User
from app.schemas import GOAL_OPTIONS, GoalIn, GoalUpdate
from app.services.common import get_profile, iso

router = APIRouter(prefix="/goals", tags=["goals"])
LABEL = {g["key"]: g["label"] for g in GOAL_OPTIONS}


def goal_out(g: Goal) -> dict:
    return {"goal_id": g.goal_id, "goal_type": g.goal_type, "label": LABEL.get(g.goal_type, g.goal_type),
            "target": g.target, "active": g.active, "created_at": iso(g.created_at)}


def _sync_profile(db: Session, user: User):
    p = get_profile(db, user)
    p.goals = [g.goal_type for g in db.query(Goal).filter_by(user_id=user.user_id, active=True).order_by(Goal.goal_id)]


@router.get("")
def list_goals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [goal_out(g) for g in db.query(Goal).filter_by(user_id=user.user_id).order_by(Goal.goal_id)]


@router.post("", status_code=201)
def create_goal(body: GoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.query(Goal).filter_by(user_id=user.user_id, goal_type=body.goal_type).first()
    if g:
        g.active, g.target = body.active, body.target if body.target is not None else g.target
    else:
        g = Goal(user_id=user.user_id, goal_type=body.goal_type, target=body.target, active=body.active)
        db.add(g)
    db.flush()
    _sync_profile(db, user)
    db.commit()
    return goal_out(g)


@router.put("/{goal_id}")
def update_goal(goal_id: int, body: GoalUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.get(Goal, goal_id)
    if not g or g.user_id != user.user_id:
        raise HTTPException(404, "Goal not found.")
    if body.target is not None:
        g.target = body.target
    if body.active is not None:
        g.active = body.active
    db.flush()
    _sync_profile(db, user)
    db.commit()
    return goal_out(g)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    g = db.get(Goal, goal_id)
    if not g or g.user_id != user.user_id:
        raise HTTPException(404, "Goal not found.")
    db.delete(g)
    db.flush()
    _sync_profile(db, user)
    db.commit()
    return None
