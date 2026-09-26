"""Smart Alternatives ("Try Instead"). Phase 2.

Candidates come from data/substitutions.json (by food keyword first, then by the conflict groups the
Risk Engine produced). Every candidate is looked up in the foods table and RE-SCREENED with the Risk
Engine against the same profile; anything that is HIGH, or that reproduces one of the original
conflict groups, is dropped. So an alternative is never suggested blindly.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.engines.risk_engine import RiskEngine
from app.models import Food

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "substitutions.json")


@lru_cache
def _subs() -> dict:
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def candidate_names(food_name: str, conflict_groups: list[str]) -> list[tuple[str, str]]:
    subs = _subs()
    out: list[tuple[str, str]] = []
    name = (food_name or "").lower()
    for kw, items in subs["by_food_keyword"].items():
        if kw in name:
            out += [tuple(x) for x in items]
    for g in conflict_groups:
        out += [tuple(x) for x in subs["by_conflict"].get(g, [])]
    seen, uniq = set(), []
    for n, why in out:
        if n.lower() not in seen and n.lower() != name:
            seen.add(n.lower())
            uniq.append((n, why))
    return uniq


def find_alternatives(db: Session, *, food_name: str, conflicts: list[dict], profile: dict,
                      engine: RiskEngine | None = None, limit: int = 3) -> list[dict]:
    engine = engine or RiskEngine()
    groups = []
    for c in conflicts:
        g = c.get("conflict_group")
        if g and g not in groups:
            groups.append(g)
    results = []
    for name, why in candidate_names(food_name, groups):
        food = db.query(Food).filter(func.lower(Food.name) == name.lower()).first()
        if not food:
            continue
        r = engine.analyze(profile=profile, raw_ingredients=food.ingredients or [],
                           nutrition=food.nutrition_data or {}, food_meta=food.meta or {},
                           data_certainty="estimated")
        if r.risk_level == "HIGH":
            continue
        if any(c.get("conflict_group") in groups for c in r.detected_conflicts):
            continue
        results.append({"name": food.name, "food_id": food.food_id, "reason": why,
                        "category": food.category, "risk_level": r.risk_level,
                        "screen_note": ("No potential conflict with your profile based on typical ingredients."
                                        if r.risk_level == "LOW" else
                                        "Avoids the flagged issue, but check: " + r.detected_conflicts[0]["reason"])})
        if len(results) >= limit:
            break
    return results
