from __future__ import annotations

import csv
import io
from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_tz
from app.database.session import get_db
from app.models import FoodLog, ScanResult, SymptomLog, User
from app.schemas import LogIn, LogUpdate
from app.services.common import NUTRIENT_KEYS, aware, iso, log_out, scan_out

router = APIRouter(tags=["logs"])


class ClearIn(BaseModel):
    confirm_text: str = Field(max_length=20)


def _own_log(db: Session, user: User, log_id: int) -> FoodLog:
    l = db.get(FoodLog, log_id)
    if not l or l.user_id != user.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Log entry not found.")
    return l


def _check_time(dt: datetime | None) -> datetime:
    now = datetime.now(timezone.utc)
    if dt is None:
        return now
    dt = aware(dt).astimezone(timezone.utc)
    if dt > now + timedelta(minutes=5):
        raise HTTPException(422, "The time eaten can't be in the future.")
    if dt < now - timedelta(days=365):
        raise HTTPException(422, "The time eaten is too far in the past.")
    return dt


def _apply_nutrition(l: FoodLog, per_serving: dict, qty: float):
    for k in NUTRIENT_KEYS:
        v = per_serving.get(k)
        setattr(l, k, round(float(v) * qty, 2) if isinstance(v, (int, float)) else None)


@router.post("/logs", status_code=201)
def create_log(body: LogIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """'I Ate This' — saves food, nutrition (x servings), risk, input method and timestamp."""
    scan = db.get(ScanResult, body.scan_id)
    if not scan or scan.user_id != user.user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Result not found.")
    meta = scan.meta or {}
    flags = meta.get("flags") or {}
    l = FoodLog(user_id=user.user_id, food_id=scan.food_id, scan_id=scan.scan_id, food_name=scan.food_name,
                category=meta.get("category"), meal_type=body.meal_type, quantity=body.quantity,
                risk_level=scan.risk_level, input_method=scan.input_method,
                is_processed=bool(flags.get("is_processed")), is_fruit_veg=bool(flags.get("is_fruit_veg")),
                added_sugar_likely=bool(flags.get("added_sugar_likely")),
                is_unpackaged=bool(flags.get("is_unpackaged")), is_demo=False,
                consumed_at=_check_time(body.consumed_at))
    _apply_nutrition(l, scan.extracted_nutrition or {}, body.quantity)
    db.add(l)
    db.flush()
    scan.meta = {**meta, "logged_log_id": l.log_id}
    db.commit()
    db.refresh(l)
    return {**log_out(l), "message": "Added to your diet history."}


def _filtered(db: Session, user: User, tz, q, meal, risk, date_from, date_to, method=None):
    qry = db.query(FoodLog).filter(FoodLog.user_id == user.user_id)
    if q:
        qry = qry.filter(func.lower(FoodLog.food_name).contains(q.strip().lower()))
    if meal:
        qry = qry.filter(FoodLog.meal_type == meal)
    if risk:
        qry = qry.filter(FoodLog.risk_level == risk.upper())
    if method:
        qry = qry.filter(FoodLog.input_method == method)
    if date_from:
        qry = qry.filter(FoodLog.consumed_at >= datetime.combine(date_from, time.min, tz).astimezone(timezone.utc))
    if date_to:
        qry = qry.filter(FoodLog.consumed_at < datetime.combine(date_to + timedelta(days=1), time.min, tz).astimezone(timezone.utc))
    return qry


def _paged(db, user, tz, page, page_size, q, meal, risk, date_from, date_to, method):
    qry = _filtered(db, user, tz, q, meal, risk, date_from, date_to, method)
    total = qry.count()
    rows = qry.order_by(FoodLog.consumed_at.desc(), FoodLog.log_id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    sym = {s.food_log_id: s for s in db.query(SymptomLog).filter(SymptomLog.food_log_id.in_([r.log_id for r in rows])).all()} if rows else {}
    return {"items": [log_out(r, sym.get(r.log_id)) for r in rows], "total": total, "page": page,
            "page_size": page_size, "pages": max(1, -(-total // page_size))}



@router.get("/logs")
@router.get("/history")
def list_logs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              q: str | None = Query(None, max_length=80),
              meal: str | None = Query(None, pattern="^(breakfast|lunch|snack|dinner)$"),
              risk: str | None = Query(None, pattern="^(LOW|CAUTION|HIGH|low|caution|high)$"),
              method: str | None = Query(None, pattern="^(scan|search|manual|eating_out)$"),
              date_from: date | None = None, date_to: date | None = None,
              user: User = Depends(get_current_user), tz=Depends(get_tz), db: Session = Depends(get_db)):
    return _paged(db, user, tz, page, page_size, q, meal, risk, date_from, date_to, method)


@router.get("/logs/export")
def export_logs(format: str = Query("csv", pattern="^(csv|json)$"), user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    rows = db.query(FoodLog).filter_by(user_id=user.user_id).order_by(FoodLog.consumed_at).all()
    if format == "json":
        return {"exported_at": iso(datetime.now(timezone.utc)), "logs": [log_out(r) for r in rows]}
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["log_id", "consumed_at", "food_name", "meal_type", "quantity", *NUTRIENT_KEYS, "risk_level", "input_method", "demo_data"]
    w.writerow(cols)
    for r in rows:
        w.writerow([r.log_id, iso(r.consumed_at), _csv_safe(r.food_name), r.meal_type, r.quantity,
                    *[getattr(r, k) for k in NUTRIENT_KEYS], r.risk_level, r.input_method, r.is_demo])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="safebite-diet-history.csv"'})


def _csv_safe(v: str) -> str:
    # guard against spreadsheet formula injection
    return "'" + v if v and v[0] in "=+-@" else v


@router.post("/logs/clear")
def clear_logs(body: ClearIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.confirm_text.strip().upper() != "CLEAR":
        raise HTTPException(422, 'Type CLEAR to confirm.')
    n = db.query(FoodLog).filter_by(user_id=user.user_id).delete(synchronize_session=False)
    db.commit()
    return {"deleted": n, "message": "Your diet history was cleared."}


@router.get("/logs/{log_id}")
@router.get("/history/{log_id}")
def get_log(log_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    l = _own_log(db, user, log_id)
    sym = db.query(SymptomLog).filter_by(food_log_id=l.log_id).first()
    out = log_out(l, sym)
    scan = db.get(ScanResult, l.scan_id) if l.scan_id else None
    out["analysis"] = scan_out(scan) if scan and scan.user_id == user.user_id else None
    from app.api.symptoms import association_for, symptom_due
    out["symptom_association"] = association_for(db, user, l.food_name)
    out["symptom_prompt_due"] = symptom_due(l) and sym is None
    return out


@router.put("/logs/{log_id}")
def update_log(log_id: int, body: LogUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    l = _own_log(db, user, log_id)
    if body.meal_type:
        l.meal_type = body.meal_type
    if body.quantity is not None and body.quantity != l.quantity:
        factor = body.quantity / (l.quantity or 1)
        for k in NUTRIENT_KEYS:
            v = getattr(l, k)
            if v is not None:
                setattr(l, k, round(v * factor, 2))
        l.quantity = body.quantity
    if body.consumed_at:
        l.consumed_at = _check_time(body.consumed_at)
    db.commit()
    return log_out(l)


@router.delete("/logs/{log_id}", status_code=204)
def delete_log(log_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    l = _own_log(db, user, log_id)
    db.delete(l)
    db.commit()
    return None
