from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models import ScanResult, User
from app.schemas import AnalyzeIn
from app.services.analysis import AnalysisError, analyze_food, preview_ingredients, restaurant_dishes
from app.services.common import scan_out

router = APIRouter(tags=["analysis"])


@router.post("/analysis/analyze", status_code=201)
def analyze(body: AnalyzeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.input_method in ("scan", "manual") and not body.ingredients:
        raise HTTPException(422,
                            "Add at least one ingredient so SafeBite can check it against your profile.")
    try:
        scan = analyze_food(db, user, body)
    except AnalysisError as e:
        raise HTTPException(422, str(e))
    return scan_out(scan)


@router.post("/analysis/preview")
def preview(body: dict, user: User = Depends(get_current_user)):
    items = body.get("ingredients") or []
    if not isinstance(items, list) or len(items) > 150:
        raise HTTPException(422, "Send a list of up to 150 ingredients.")
    return {"ingredients": preview_ingredients([str(x)[:200] for x in items])}


@router.get("/analysis/recent")
def recent(limit: int = Query(5, ge=1, le=20), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ScanResult).filter_by(user_id=user.user_id).order_by(ScanResult.created_at.desc()).limit(limit).all()
    return [scan_out(s) for s in rows]


@router.get("/analysis/{scan_id}")
def get_result(scan_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(ScanResult, scan_id)
    if not s or s.user_id != user.user_id:  # authorization: users only see their own results
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Result not found.")
    return scan_out(s)


@router.get("/eating-out/dishes")
def dishes(user: User = Depends(get_current_user)):
    return [{"name": d["name"], "nutrition": d["nutrition"], "ranges": d.get("ranges", {}),
             "ingredients": d["ingredients"], "note": d.get("note")} for d in restaurant_dishes()]
