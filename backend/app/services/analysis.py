"""Orchestrates Engine 1 for every input path (scan, search, manual, eating-out) and stores a ScanResult.
All four paths share one Risk Engine and one result page."""
from __future__ import annotations

import json
import os
from functools import lru_cache

from sqlalchemy.orm import Session

from app.engines.diet_pattern_engine import food_flags
from app.engines.ingredient_normalizer import get_dictionary, normalize_list
from app.engines.risk_engine import RiskEngine
from app.models import Food, ScanResult, User
from app.schemas import AnalyzeIn
from app.services.alternatives import find_alternatives
from app.services.common import get_profile, profile_dict

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

SCAN_CATEGORY_KEYWORDS = [
    (("biscuit", "cookie", "cracker", "wafer", "chips", "crisps", "namkeen", "bhujia", "makhana", "puffs"), "Snack"),
    (("noodle", "pasta", "soup", "ready to eat", "instant"), "Packaged Meal"),
    (("chocolate", "candy", "sweet", "cake", "ice cream", "jam"), "Sweet"),
    (("juice", "cola", "soda", "drink", "beverage"), "Beverage"),
    (("bread", "bun", "rusk"), "Bakery"),
    (("cereal", "flakes", "muesli", "oats"), "Breakfast"),
    (("milk", "curd", "yogurt", "yoghurt", "cheese", "paneer"), "Dairy"),
    (("sauce", "ketchup", "pickle", "spread", "butter"), "Condiment"),
]


class AnalysisError(ValueError):
    pass


@lru_cache
def restaurant_dishes() -> list[dict]:
    with open(os.path.join(DATA, "restaurant_dishes.json"), encoding="utf-8") as f:
        return json.load(f)


def guess_category(name: str) -> str:
    n = (name or "").lower()
    for kws, cat in SCAN_CATEGORY_KEYWORDS:
        if any(k in n for k in kws):
            return cat
    return "Packaged Food"


def _clean_nutrition(n: dict) -> dict:
    out = {}
    for k, v in (n or {}).items():
        if v is None:
            continue
        out[k] = round(float(v), 2) if isinstance(v, (int, float)) else v
    return out


def analyze_food(db: Session, user: User, body: AnalyzeIn) -> ScanResult:
    profile = profile_dict(get_profile(db, user))
    engine = RiskEngine(get_dictionary())
    method = body.input_method
    food: Food | None = None
    meta: dict = {}
    nutrition = _clean_nutrition(body.nutrition.model_dump(exclude_none=True))
    ingredients = list(body.ingredients)
    statements = body.allergen_statements.model_dump()
    food_meta: dict = {}
    name = body.food_name
    estimate = None

    if method == "search":
        if not body.food_id:
            raise AnalysisError("Choose a food from the search results.")
        food = db.get(Food, body.food_id)
        if not food:
            raise AnalysisError("That food wasn't found.")
        name = food.name
        ingredients = list(food.ingredients or [])
        nutrition = _clean_nutrition(food.nutrition_data or {})
        food_meta = food.meta or {}
        certainty = "estimated" if not food.is_packaged or "estimate" in (food_meta.get("ingredients_basis") or "") else "known"
        category, is_packaged = food.category, food.is_packaged
        if certainty == "estimated":
            estimate = {"label": "Typical recipe",
                        "note": "Ingredients are based on a typical recipe. How it was made may differ."}
    elif method == "eating_out":
        dish = next((d for d in restaurant_dishes() if d["name"].lower() == (body.dish_name or name).lower()), None)
        if not dish:
            raise AnalysisError("That dish isn't in the eating-out list yet. Try Enter Manually instead.")
        name = dish["name"]
        ingredients = list(dish["ingredients"])
        nutrition = _clean_nutrition(dish["nutrition"])
        certainty, category, is_packaged = "estimated", "Restaurant", False
        estimate = {"label": "ESTIMATE", "note": dish.get("note") or "Estimated ingredients — restaurant recipes vary.",
                    "ranges": dish.get("ranges", {})}
    elif method == "scan":
        certainty = "known" if ingredients else "unknown"
        category, is_packaged = guess_category(name), True
    else:  # manual
        certainty = "known" if ingredients else "unknown"
        category, is_packaged = "Homemade / Other", False

    result = engine.analyze(profile=profile, raw_ingredients=ingredients, allergen_statements=statements,
                            nutrition=nutrition, food_meta=food_meta, data_certainty=certainty,
                            ocr_confidence=body.ocr_confidence if method == "scan" else None)

    flags = food_flags(result.ingredient_details, category, is_packaged, method)
    if method == "scan":
        tags = {t for i in result.ingredient_details for t in (i.get("dietary_tags") or [])}
        flags["is_processed"] = flags["is_processed"] or bool(tags & {"refined_flour", "added_sugar", "hidden_sugar"}) \
            or category in ("Packaged Meal", "Sweet", "Bakery")

    alternatives = []
    if result.risk_level in ("CAUTION", "HIGH"):
        alternatives = find_alternatives(db, food_name=name, conflicts=result.detected_conflicts,
                                         profile=profile, engine=engine)

    meta.update({"notes": result.notes, "unrecognized": result.unrecognized, "disclaimer": result.disclaimer,
                 "estimate": estimate, "category": category, "is_packaged": is_packaged, "flags": flags,
                 "meal_type": body.meal_type, "profile_snapshot": profile,
                 "ocr_scan_token": body.ocr_scan_token})
    scan = ScanResult(
        user_id=user.user_id, food_id=food.food_id if food else None, food_name=name, input_method=method,
        image_path=body.ocr_scan_token if method == "scan" else None,
        raw_ocr_text=body.raw_ocr_text if method == "scan" else None,
        raw_ingredients=ingredients, normalized_ingredients=result.ingredient_details,
        extracted_nutrition=nutrition, allergen_statements=statements, risk_level=result.risk_level,
        detected_conflicts=result.detected_conflicts, explanation=result.explanation, warnings=result.warnings,
        confidence=result.confidence, ocr_confidence=body.ocr_confidence if method == "scan" else None,
        data_certainty=certainty, alternatives=alternatives, meta=meta)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


def preview_ingredients(raw: list[str]) -> list[dict]:
    """Used by the OCR review screen: shows how each line will be interpreted."""
    return [i.to_dict() for i in normalize_list(raw, get_dictionary())]
