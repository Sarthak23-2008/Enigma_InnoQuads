"""FUTURE module: household / personal-care label awareness. Uses a SEPARATE dictionary
(data/household_ingredients.json) and never touches food allergen rules."""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "household_ingredients.json")


@lru_cache
def _entries() -> list[dict]:
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)["entries"]


def analyze_household_text(text: str) -> dict:
    low = " " + re.sub(r"\s+", " ", text.lower()) + " "
    found = []
    for e in _entries():
        hits = [a for a in e["aliases"] if re.search(r"(?<![a-z])" + re.escape(a.lower()) + r"(?![a-z])", low)]
        if hits:
            found.append({"name": e["name"], "level": e["level"], "matched": sorted(set(hits)), "reason": e["reason"]})
    level = "CAUTION" if found else "LOW"
    return {"level": level, "flags": found,
            "summary": (f"{len(found)} ingredient group(s) some people prefer to avoid were found."
                        if found else "None of the ingredient groups in SafeBite's household list were found."),
            "disclaimer": "Household/personal-care awareness is a future-scope preview using a separate dictionary. "
                          "It is not a safety certification."}
