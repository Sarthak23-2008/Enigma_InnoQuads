"""Shared helpers used by several routers (serialization, profile access, diet analysis)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.engines.diet_pattern_engine import DietPatternEngine
from app.models import DietaryProfile, Food, FoodLog, Goal, NotificationSetting, ScanResult, SymptomLog, User, UserSetting

NUTRIENT_KEYS = ("calories", "protein", "carbohydrates", "fat", "sugar", "fiber", "sodium", "potassium")


def aware(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; everything is stored as UTC."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def iso(dt: datetime | None) -> str | None:
    dt = aware(dt)
    return dt.isoformat() if dt else None


def get_profile(db: Session, user: User) -> DietaryProfile:
    p = db.query(DietaryProfile).filter_by(user_id=user.user_id).first()
    if not p:
        p = DietaryProfile(user_id=user.user_id, allergies=[], intolerances=[], dietary_preferences=[],
                           health_conditions=[], goals=[])
        db.add(p)
        db.commit()
    return p


def profile_dict(p: DietaryProfile) -> dict:
    return {"allergies": p.allergies or [], "intolerances": p.intolerances or [],
            "dietary_preferences": p.dietary_preferences or [], "health_conditions": p.health_conditions or [],
            "goals": p.goals or [], "updated_at": iso(p.updated_at)}


def get_user_settings(db: Session, user: User) -> tuple[UserSetting, NotificationSetting]:
    us = db.query(UserSetting).filter_by(user_id=user.user_id).first()
    ns = db.query(NotificationSetting).filter_by(user_id=user.user_id).first()
    changed = False
    if not us:
        us = UserSetting(user_id=user.user_id)
        db.add(us)
        changed = True
    if not ns:
        ns = NotificationSetting(user_id=user.user_id, last_sent={})
        db.add(ns)
        changed = True
    if changed:
        db.commit()
    return us, ns


def settings_dict(us: UserSetting, ns: NotificationSetting) -> dict:
    return {
        "notifications": {"weekly_reports": ns.weekly_reports, "biweekly_reports": ns.biweekly_reports,
                          "monthly_reports": ns.monthly_reports, "push_enabled": ns.push_enabled,
                          "email_enabled": ns.email_enabled, "last_sent": ns.last_sent or {}},
        "input_prefs": {"default_input_method": us.default_input_method, "ocr_language": us.ocr_language,
                        "auto_log": us.auto_log},
        "accessibility": {"text_size": us.text_size, "high_contrast": us.high_contrast,
                          "voice_assistance": us.voice_assistance},
    }


def active_goals(db: Session, user: User) -> list[str]:
    return [g.goal_type for g in db.query(Goal).filter_by(user_id=user.user_id, active=True).order_by(Goal.goal_id).all()]


def food_out(f: Food, full: bool = False) -> dict:
    n = f.nutrition_data or {}
    out = {"food_id": f.food_id, "name": f.name, "category": f.category, "source": f.source,
           "is_packaged": f.is_packaged,
           "nutrition": {k: n.get(k) for k in NUTRIENT_KEYS},
           "serving_size_g": (f.meta or {}).get("serving_size_g")}
    if full:
        m = f.meta or {}
        out.update({"ingredients": f.ingredients or [], "ingredients_basis": m.get("ingredients_basis"),
                    "notes": m.get("notes"), "declared_allergens": m.get("declared_allergens", []),
                    "may_contain": m.get("may_contain", []), "food_type": m.get("food_type")})
    return out


def scan_out(s: ScanResult) -> dict:
    meta = s.meta or {}
    return {
        "scan_id": s.scan_id, "id": s.scan_id, "food_name": s.food_name, "food_id": s.food_id,
        "input_method": s.input_method, "risk_level": s.risk_level, "confidence": s.confidence,
        "ocr_confidence": s.ocr_confidence, "data_certainty": s.data_certainty,
        "explanation": s.explanation, "detected_conflicts": s.detected_conflicts or [],
        "warnings": s.warnings or [], "notes": meta.get("notes", []),
        "ingredients": [i.get("name") for i in (s.normalized_ingredients or []) if i.get("name")],
        "ingredient_details": s.normalized_ingredients or [], "raw_ingredients": s.raw_ingredients or [],
        "unrecognized": meta.get("unrecognized", []),
        "nutrition": s.extracted_nutrition or {}, "allergen_statements": s.allergen_statements or {},
        "alternatives": s.alternatives or [], "disclaimer": meta.get("disclaimer"),
        "estimate": meta.get("estimate"), "category": meta.get("category"),
        "suggested_meal_type": meta.get("meal_type"), "logged_log_id": meta.get("logged_log_id"),
        "created_at": iso(s.created_at),
    }


def log_out(l: FoodLog, symptom: SymptomLog | None = None) -> dict:
    return {
        "log_id": l.log_id, "id": l.log_id, "food_id": l.food_id, "scan_id": l.scan_id, "food_name": l.food_name,
        "category": l.category, "meal_type": l.meal_type, "quantity": l.quantity,
        "nutrition": {k: getattr(l, k) for k in NUTRIENT_KEYS},
        "calories": l.calories, "risk_level": l.risk_level, "input_method": l.input_method,
        "is_processed": l.is_processed, "is_fruit_veg": l.is_fruit_veg, "is_unpackaged": l.is_unpackaged,
        "is_demo": l.is_demo, "consumed_at": iso(l.consumed_at), "created_at": iso(l.created_at),
        "symptom": symptom_out(symptom) if symptom else None,
    }


def symptom_out(s: SymptomLog) -> dict:
    return {"symptom_id": s.symptom_id, "food_log_id": s.food_log_id, "severity": s.severity,
            "symptom": s.symptom, "notes": s.notes, "created_at": iso(s.created_at)}


def log_as_engine_dict(l: FoodLog) -> dict:
    d = {k: getattr(l, k) for k in NUTRIENT_KEYS}
    d.update({"consumed_at": aware(l.consumed_at), "food_name": l.food_name, "category": l.category,
              "quantity": l.quantity, "is_processed": l.is_processed, "is_fruit_veg": l.is_fruit_veg,
              "added_sugar_likely": l.added_sugar_likely, "risk_level": l.risk_level})
    return d


def diet_analysis(db: Session, user: User, window: int, tz=timezone.utc, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=window * 2 + 2)
    logs = db.query(FoodLog).filter(FoodLog.user_id == user.user_id, FoodLog.consumed_at >= since) \
        .order_by(FoodLog.consumed_at).all()
    rows = [log_as_engine_dict(l) for l in logs]
    engine = DietPatternEngine(tz=tz)
    result = engine.analyze(rows, window=window, now=now, goals=active_goals(db, user), previous_logs=rows)
    result["is_demo_data"] = any(l.is_demo for l in logs)
    return result
