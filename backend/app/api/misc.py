"""Consultation directory (Phase 3), household preview (Future), demo reset, health check."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_tz
from app.config import get_settings
from app.database.session import get_db
from app.models import ConsultationProvider, User
from app.schemas import HouseholdIn
from app.services.common import diet_analysis
from app.services.household import analyze_household_text

router = APIRouter(tags=["misc"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        ok = True
    except Exception:
        ok = False
    s = get_settings()
    from app.services.ocr.factory import get_provider
    return {"status": "ok" if ok else "degraded", "database": ok, "ocr_provider": s.OCR_PROVIDER,
            "ocr_available": get_provider().available(), "demo_mode": s.DEMO_MODE}


@router.get("/consult/providers")
def providers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ConsultationProvider).order_by(ConsultationProvider.provider_id).all()
    return [{"provider_id": p.provider_id, "name": p.name, "specialty": p.specialty, "rate": p.rate,
             "contact": p.contact, "available": p.available, "is_sample": p.is_sample} for p in rows]


@router.get("/consult/attention")
def attention(user: User = Depends(get_current_user), tz=Depends(get_tz), db: Session = Depends(get_db)):
    a = diet_analysis(db, user, 30, tz)
    return {**a["attention"], "status": a["status"],
            "disclaimer": "Pattern Attention Level is an educational indicator based on your logs. It is not a medical risk score."}


@router.post("/household/analyze")
def household(body: HouseholdIn, user: User = Depends(get_current_user)):
    return analyze_household_text(body.text)


@router.post("/demo/reset")
def demo_reset(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_demo:
        raise HTTPException(403, "Only the demo account can be reset.")
    from app.database.seed import seed_demo_user
    seed_demo_user(db, reset=True)
    return {"message": "Demo data was reset."}
