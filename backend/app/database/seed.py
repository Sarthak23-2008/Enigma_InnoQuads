"""Seed reference data (ingredient mappings, foods, sample consultation listings) and the DEMO account.

Usage:
    python -m app.database.seed               # idempotent: seeds whatever is missing
    python -m app.database.seed --reset-demo  # rebuild the demo user's logs relative to "now"
    python -m app.database.seed --refresh-reference  # reload mappings/foods from app/data
Demo data is clearly separated: the demo user has is_demo=True and every seeded log has is_demo=True.
"""
from __future__ import annotations

import json
import logging
import os
import random
import sys
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.data.food_catalog import all_foods
from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.engines.diet_pattern_engine import food_flags
from app.engines.ingredient_normalizer import IngredientDictionary, reset_dictionary_cache
from app.engines.risk_engine import RiskEngine
from app.models import (ConsultationProvider, DietaryProfile, Food, FoodLog, Goal, IngredientMapping,
                        NotificationSetting, ScanResult, SymptomLog, User, UserSetting)

log = logging.getLogger("safebite.seed")
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEMO_EMAIL = "demo@safebite.app"
DEMO_PASSWORD = "SafeBiteDemo1"   # documented demo credential for the hackathon; not a secret
DEMO_TZ = ZoneInfo("Asia/Kolkata")
DEMO_PROFILE = {"allergies": ["Peanut"], "intolerances": ["Lactose"], "dietary_preferences": ["Vegetarian"],
                "health_conditions": [], "goals": ["reduce_sodium"]}


def _json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def seed_reference(db: Session, refresh: bool = False) -> None:
    if refresh:
        db.query(IngredientMapping).delete()
        db.commit()
    if db.query(IngredientMapping).count() == 0:
        for r in _json("ingredient_mappings.json"):
            db.add(IngredientMapping(standard_name=r["standard_name"], category=r["category"], aliases=r["aliases"],
                                     allergen_group=r.get("allergen_group") or None,
                                     intolerance_group=r.get("intolerance_group") or [],
                                     dietary_tags=r.get("dietary_tags") or []))
        db.commit()
        reset_dictionary_cache()
    existing = {f.name.lower(): f for f in db.query(Food).all()}
    for f in all_foods():
        cur = existing.get(f["name"].lower())
        if cur is None:
            db.add(Food(external_id=f.get("external_id"), name=f["name"], category=f["category"],
                        ingredients=f["ingredients"], nutrition_data=f["nutrition_data"], source=f["source"],
                        is_packaged=f["is_packaged"], meta=f["meta"]))
        elif refresh:
            cur.category, cur.ingredients, cur.nutrition_data = f["category"], f["ingredients"], f["nutrition_data"]
            cur.source, cur.is_packaged, cur.meta = f["source"], f["is_packaged"], f["meta"]
    db.commit()
    if db.query(ConsultationProvider).count() == 0:
        for p in _json("consultation_providers.json"):
            db.add(ConsultationProvider(name=p["name"], specialty=p["specialty"], rate=p["rate"],
                                        contact=p["contact"], available=p.get("available", True), is_sample=True))
        db.commit()


# ---------------------------------------------------------------- demo user
# Meal plans chosen to produce the documented demo story: high sodium, low fiber, moderate protein,
# several LOW foods, some CAUTION (dairy) and a few HIGH (peanut) checks. Values come from the food table.
BREAKFAST = [("Idli (2 pieces)", 1), ("Upma", 1), ("White Bread (2 slices)", 1), ("Cornflakes", 1),
             ("Masala Dosa", 1), ("Cornflakes", 1), ("Poha", 1), ("Plain Dosa", 1)]
LUNCH = [[("White Rice (Cooked)", 1.5), ("Dal Tadka (Toor Dal)", 1)], [("Veg Biryani", 1)], [("Veg Biryani", 1), ("Papad (Roasted)", 1)],
         [("Paneer Butter Masala", 1), ("Plain Roti (Wheat)", 2)], [("Sambar", 1), ("White Rice (Cooked)", 1.5), ("Papad (Roasted)", 1)],
         [("Paneer Butter Masala", 1), ("White Rice (Cooked)", 1.5)]]
SNACK = [("Salted Potato Chips", 1.5), ("Instant Noodles (Masala)", 1), ("Samosa (2 pieces)", 1), ("Vada Pav", 1),
         ("Instant Noodles (Masala)", 1), ("Buttermilk/Chaas (Salted)", 1), ("Cream Biscuits", 1), ("Masala Namkeen Mix", 1),
         ("Vada Pav", 1)]
DINNER = [[("Dal Khichdi", 1)], [("Veg Burger", 1)], [("Margherita Pizza (2 slices)", 1)],
          [("Paneer Tikka", 1)], [("Paneer Tikka", 1), ("Plain Roti (Wheat)", 1)],
          [("Veg Biryani", 1)], [("Margherita Pizza (2 slices)", 1)]]
MEAL_TIME = {"breakfast": time(8, 30), "lunch": time(13, 15), "snack": time(17, 30), "dinner": time(20, 45)}


def _ensure_demo_user(db: Session) -> User:
    u = db.query(User).filter_by(email=DEMO_EMAIL).first()
    if not u:
        u = User(name="Aryan Demo", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD), is_demo=True,
                 onboarding_complete=True)
        db.add(u)
        db.flush()
    u.name, u.is_demo, u.onboarding_complete = "Aryan Demo", True, True
    p = db.query(DietaryProfile).filter_by(user_id=u.user_id).first() or DietaryProfile(user_id=u.user_id)
    for k, v in DEMO_PROFILE.items():
        setattr(p, k, list(v))
    db.add(p)
    if not db.query(UserSetting).filter_by(user_id=u.user_id).first():
        db.add(UserSetting(user_id=u.user_id))
    if not db.query(NotificationSetting).filter_by(user_id=u.user_id).first():
        db.add(NotificationSetting(user_id=u.user_id, weekly_reports=True, last_sent={}))
    db.query(Goal).filter_by(user_id=u.user_id).delete()
    db.add(Goal(user_id=u.user_id, goal_type="reduce_sodium", target=2000, active=True))
    db.commit()
    return u


def seed_demo_user(db: Session, reset: bool = False, now: datetime | None = None) -> User:
    u = _ensure_demo_user(db)
    has_logs = db.query(FoodLog).filter_by(user_id=u.user_id).count() > 0
    if has_logs and not reset:
        return u
    db.query(FoodLog).filter_by(user_id=u.user_id).delete()
    db.query(ScanResult).filter_by(user_id=u.user_id).delete()
    db.commit()

    now = now or datetime.now(timezone.utc)
    rng = random.Random(20260926)
    engine = RiskEngine(IngredientDictionary.from_file())
    foods = {f.name: f for f in db.query(Food).all()}
    scans: dict[str, ScanResult] = {}

    def scan_for(name: str) -> ScanResult:
        if name in scans:
            return scans[name]
        f = foods[name]
        r = engine.analyze(profile=DEMO_PROFILE, raw_ingredients=f.ingredients, nutrition=f.nutrition_data,
                           food_meta=f.meta or {}, data_certainty="estimated")
        flags = food_flags(r.ingredient_details, f.category, f.is_packaged, "search")
        s = ScanResult(user_id=u.user_id, food_id=f.food_id, food_name=f.name, input_method="search",
                       raw_ingredients=f.ingredients, normalized_ingredients=r.ingredient_details,
                       extracted_nutrition=f.nutrition_data, allergen_statements={}, risk_level=r.risk_level,
                       detected_conflicts=r.detected_conflicts, explanation=r.explanation, warnings=r.warnings,
                       confidence=r.confidence, data_certainty="estimated", alternatives=[],
                       meta={"notes": r.notes, "unrecognized": r.unrecognized, "disclaimer": r.disclaimer,
                             "category": f.category, "is_packaged": f.is_packaged, "flags": flags, "demo": True,
                             "estimate": {"label": "Typical recipe", "note": "Ingredients are based on a typical recipe. How it was made may differ."}},
                       created_at=now - timedelta(days=31))
        db.add(s)
        db.flush()
        scans[name] = s
        return s

    def add_log(name, qty, meal, day, minute_jitter=0, symptom=None):
        s = scan_for(name)
        f = foods[name]
        local = datetime.combine(day, MEAL_TIME[meal], DEMO_TZ) + timedelta(minutes=minute_jitter)
        ts = local.astimezone(timezone.utc)
        if ts > now:
            return None
        flags = s.meta["flags"]
        n = f.nutrition_data
        l = FoodLog(user_id=u.user_id, food_id=f.food_id, scan_id=s.scan_id, food_name=f.name, category=f.category,
                    meal_type=meal, quantity=qty, risk_level=s.risk_level, input_method="search",
                    is_processed=flags["is_processed"], is_fruit_veg=flags["is_fruit_veg"],
                    added_sugar_likely=flags["added_sugar_likely"], is_unpackaged=flags["is_unpackaged"],
                    is_demo=True, consumed_at=ts, created_at=ts,
                    **{k: (round(n[k] * qty, 2) if n.get(k) is not None else None)
                       for k in ("calories", "protein", "carbohydrates", "fat", "sugar", "fiber", "sodium", "potassium")})
        db.add(l)
        db.flush()
        if symptom:
            db.add(SymptomLog(user_id=u.user_id, food_log_id=l.log_id, severity=symptom[0], symptom=symptom[1],
                              notes="Demo check-in", created_at=ts + timedelta(days=2)))
        return l

    today = now.astimezone(DEMO_TZ).date()
    for back in range(30, -1, -1):
        day = today - timedelta(days=back)
        older = back >= 15  # previous period: a little saltier, so the Reduce-Sodium goal shows progress
        j = lambda: rng.randint(-20, 25)  # noqa: E731
        b = BREAKFAST[rng.randrange(len(BREAKFAST))]
        sym = None
        if b[0] == "Masala Dosa" and back in range(5, 30):
            sym = ("mild", "Bloating")
        add_log(b[0], b[1], "breakfast", day, j(), symptom=sym)
        if rng.random() < 0.5:
            add_log("Masala Chai (with sugar)", 1, "breakfast", day, j() + 10)
        for name, q in LUNCH[rng.randrange(len(LUNCH))]:
            add_log(name, q, "lunch", day, j())
        n_snacks = 2 if rng.random() < (0.85 if older else 0.55) else 1
        for _ in range(n_snacks):
            sn = SNACK[rng.randrange(len(SNACK))]
            if sn[0] == "Masala Namkeen Mix" and back < 3:
                sn = ("Salted Potato Chips", 1)
            if not older and sn[0] in ("Instant Noodles (Masala)", "Vada Pav") and rng.random() < 0.45:
                sn = ("Roasted Makhana (Fox Nuts)", 1)  # recent swaps -> sodium trending down (goal progress)
            add_log(sn[0], sn[1], "snack", day, j())
        if rng.random() < 0.18:
            add_log(rng.choice(["Banana (Medium)", "Apple (Medium)", "Orange (Medium)"]), 1, "snack", day, j() + 40)
        for name, q in DINNER[rng.randrange(len(DINNER))]:
            add_log(name, q, "dinner", day, j())
        if older and rng.random() < 0.6:
            add_log("Papad (Roasted)", 1, "dinner", day, j() + 5)

    # guarantee two Masala Dosa check-ins with mild symptoms -> repeated-association demo
    dosa_days = [today - timedelta(days=d) for d in (9, 17)]
    for d in dosa_days:
        add_log("Masala Dosa", 1, "breakfast", d, 90, symptom=("mild", "Bloating"))

    # answered check-ins inside the prompt window, except one manual entry left pending for the demo
    window_logs = db.query(FoodLog).filter(FoodLog.user_id == u.user_id, FoodLog.is_unpackaged.is_(True),
                                           FoodLog.consumed_at <= now - timedelta(hours=48),
                                           FoodLog.consumed_at >= now - timedelta(days=4)).all()
    for l in window_logs:
        if not db.query(SymptomLog).filter_by(food_log_id=l.log_id).first():
            db.add(SymptomLog(user_id=u.user_id, food_log_id=l.log_id, severity="none", symptom="", notes="Demo check-in"))
    pending_day = (now - timedelta(hours=60)).astimezone(DEMO_TZ)
    pb_scan = ScanResult(user_id=u.user_id, food_name="Homemade Pav Bhaji", input_method="manual",
                         raw_ingredients=["pav (bread)", "potato", "mixed vegetables", "butter", "pav bhaji masala", "salt"],
                         normalized_ingredients=[], extracted_nutrition={"calories": 480, "protein": 11, "sodium": 950,
                                                                         "fiber": 6, "sugar": 7, "fat": 18, "carbohydrates": 68},
                         allergen_statements={}, risk_level="CAUTION",
                         detected_conflicts=[{"ingredient": "Butter", "standard_name": "Butter", "profile_match": "lactose intolerance",
                                              "type": "intolerance", "severity": "caution",
                                              "reason": "Butter may conflict with your lactose intolerance.", "conflict_group": "lactose"}],
                         explanation="Butter may conflict with your lactose intolerance.",
                         warnings=["Ingredient information may be incomplete. Always check the physical label if you have a severe allergy."],
                         confidence=0.8, data_certainty="known", alternatives=[],
                         meta={"category": "Homemade / Other", "demo": True, "flags": {"is_unpackaged": True}})
    # run the real engine for this manual entry so its details are genuine
    r = engine.analyze(profile=DEMO_PROFILE, raw_ingredients=pb_scan.raw_ingredients, nutrition=pb_scan.extracted_nutrition)
    pb_scan.normalized_ingredients, pb_scan.risk_level = r.ingredient_details, r.risk_level
    pb_scan.detected_conflicts, pb_scan.explanation, pb_scan.warnings = r.detected_conflicts, r.explanation, r.warnings
    db.add(pb_scan)
    db.flush()
    n = pb_scan.extracted_nutrition
    db.add(FoodLog(user_id=u.user_id, scan_id=pb_scan.scan_id, food_name="Homemade Pav Bhaji", category="Homemade / Other",
                   meal_type="dinner", quantity=1, risk_level=r.risk_level, input_method="manual", is_processed=False,
                   is_unpackaged=True, is_demo=True, consumed_at=pending_day.astimezone(timezone.utc),
                   calories=n["calories"], protein=n["protein"], sodium=n["sodium"], fiber=n["fiber"], sugar=n["sugar"],
                   fat=n["fat"], carbohydrates=n["carbohydrates"]))
    db.commit()
    log.info("demo data seeded", extra={"logs": db.query(FoodLog).filter_by(user_id=u.user_id).count()})
    return u


def demo_is_stale(db: Session, now: datetime | None = None) -> bool:
    """Seeded dates are relative to seeding time; refresh if the newest demo log is > 36 h old."""
    now = now or datetime.now(timezone.utc)
    u = db.query(User).filter_by(email=DEMO_EMAIL).first()
    if not u:
        return True
    last = db.query(FoodLog).filter_by(user_id=u.user_id).order_by(FoodLog.consumed_at.desc()).first()
    if not last:
        return True
    ts = last.consumed_at if last.consumed_at.tzinfo else last.consumed_at.replace(tzinfo=timezone.utc)
    return now - ts > timedelta(hours=36)


def run(reset_demo: bool = False, refresh_reference: bool = False, with_demo: bool = True) -> None:
    init_db()
    with SessionLocal() as db:
        seed_reference(db, refresh=refresh_reference)
        if with_demo:
            seed_demo_user(db, reset=reset_demo or demo_is_stale(db))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run(reset_demo="--reset-demo" in sys.argv, refresh_reference="--refresh-reference" in sys.argv)
    print("Seed complete. Demo login: demo@safebite.app / SafeBiteDemo1")
