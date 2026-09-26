from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_tz
from app.database.session import get_db
from app.models import DietInsight, FoodLog, ScanResult, User
from app.services.common import diet_analysis, get_profile, log_out, profile_dict, scan_out

router = APIRouter(tags=["insights"])


def _persist(db: Session, user: User, window: int, a: dict) -> None:
    """Store the latest computed insights (one current row per metric per period)."""
    period = f"{window}d"
    db.query(DietInsight).filter_by(user_id=user.user_id, period=period).delete(synchronize_session=False)
    alerts = {al["metric"]: al for al in a.get("alerts", [])}
    for m in a.get("metrics", []):
        al = alerts.get(m["key"])
        db.add(DietInsight(user_id=user.user_id, period=period, metric=m["key"], value=m["value"],
                           severity="attention" if m["attention"] else m["classification"].lower(),
                           message=al["message"] if al else m["explanation"]))
    db.commit()


def _insight(window: int, user, tz, db):
    a = diet_analysis(db, user, window, tz)
    _persist(db, user, window, a)
    return a


@router.get("/insights/15-day")
def insights_15(user: User = Depends(get_current_user), tz=Depends(get_tz), db: Session = Depends(get_db)):
    return _insight(15, user, tz, db)


@router.get("/insights/30-day")
def insights_30(user: User = Depends(get_current_user), tz=Depends(get_tz), db: Session = Depends(get_db)):
    return _insight(30, user, tz, db)


@router.get("/trends")
def trends(window: int = Query(15, ge=1, le=90), user: User = Depends(get_current_user), tz=Depends(get_tz),
           db: Session = Depends(get_db)):
    window = 30 if window >= 30 else 15
    return _insight(window, user, tz, db)


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), tz=Depends(get_tz), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    local = now.astimezone(tz)
    start = datetime.combine(local.date(), time.min, tz).astimezone(timezone.utc)
    today = db.query(FoodLog).filter(FoodLog.user_id == user.user_id, FoodLog.consumed_at >= start,
                                     FoodLog.consumed_at < start + timedelta(days=1)).order_by(FoodLog.consumed_at).all()
    meals = {m: [] for m in ("breakfast", "lunch", "snack", "dinner")}
    for l in today:
        meals.setdefault(l.meal_type, []).append(log_out(l))
    totals = {k: round(sum((getattr(l, k) or 0) for l in today), 1) for k in ("calories", "protein", "sugar", "fiber", "sodium")}
    recent = db.query(ScanResult).filter_by(user_id=user.user_id).order_by(ScanResult.created_at.desc()).first()
    a = diet_analysis(db, user, 15, tz)
    snap = [{"key": m["key"], "label": m["label"], "classification": m["classification"], "attention": m["attention"]}
            for m in a["metrics"] if m["key"] in ("added_sugar", "sodium", "fiber", "protein")]
    h = local.hour
    greeting = "Good morning" if 5 <= h < 12 else ("Good afternoon" if 12 <= h < 17 else "Good evening")
    from app.api.symptoms import pending
    pend = pending(user=user, db=db)
    return {"greeting": greeting, "name": user.name, "is_demo": user.is_demo, "today": meals, "today_totals": totals,
            "recent_check": scan_out(recent) if recent else None,
            "snapshot": {"status": a["status"], "metrics": snap, "top_alert": (a["alerts"] or [None])[0]},
            "pending_symptoms": pend["items"][:2], "symptom_question": pend["question"],
            "profile": profile_dict(get_profile(db, user))}
