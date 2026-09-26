"""Ingredient Intelligence: cleaning, splitting, normalization and synonym resolution.

Pipeline for each raw ingredient token:
  strip percentages/negations -> detect trace wording -> longest-alias match (word boundaries)
  -> OCR-error corrections -> fuzzy match (difflib) -> 'unrecognized'.
The dictionary comes from the ingredient_mapping table (seeded from data/ingredient_mappings.json),
so synonyms are data, not UI logic.
"""
from __future__ import annotations

import difflib
import json
import os
import re
from dataclasses import dataclass, field

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ingredient_mappings.json")

TRACE_RE = re.compile(r"\b(may\s+contain\s+traces?\s+of|may\s+contain|traces?\s+of|traces?)\b", re.I)
PERCENT_RE = re.compile(r"\(?\s*\d+(?:[.,]\d+)?\s*%\s*\)?")
NEGATION_LEAD_RE = re.compile(r"^(no\s+added|no|free\s+from|without|contains\s+no)\b", re.I)
X_FREE_RE = re.compile(r"\b[a-z]+[- ]free\b", re.I)
OCR_FIXES = [("rn", "m"), ("0", "o"), ("1", "l"), ("5", "s"), ("vv", "w"), ("cl", "d"), ("ii", "ll"), ("|", "l"), ("$", "s")]


@dataclass
class Mapping:
    standard_name: str
    category: str
    allergen_groups: list[str]
    intolerance_groups: list[str]
    dietary_tags: list[str]
    aliases: list[str]


@dataclass
class NormalizedIngredient:
    raw: str
    name: str | None                    # standard name, None if unrecognized
    matched_alias: str | None = None
    match_type: str = "unrecognized"    # exact | ocr_corrected | fuzzy | unrecognized
    category: str | None = None
    allergen_groups: list[str] = field(default_factory=list)
    intolerance_groups: list[str] = field(default_factory=list)
    dietary_tags: list[str] = field(default_factory=list)
    is_trace: bool = False
    trace_type: str | None = None       # "listed" (e.g. "peanut traces") | "may_contain" (precautionary)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


class IngredientDictionary:
    def __init__(self, rows: list[dict]):
        self.by_alias: dict[str, Mapping] = {}
        self.by_name: dict[str, Mapping] = {}
        for r in rows:
            groups = r.get("allergen_group") or ""
            m = Mapping(
                standard_name=r["standard_name"],
                category=r.get("category") or "other",
                allergen_groups=[g.strip() for g in groups.split(",") if g.strip()],
                intolerance_groups=list(r.get("intolerance_group") or []),
                dietary_tags=list(r.get("dietary_tags") or []),
                aliases=[a.lower() for a in r.get("aliases") or []],
            )
            self.by_name[m.standard_name.lower()] = m
            for a in m.aliases + [m.standard_name.lower()]:
                self.by_alias.setdefault(a, m)
        aliases = sorted(self.by_alias, key=len, reverse=True)
        self._alias_list = aliases
        self._regex = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(a) for a in aliases) + r")(?![a-z0-9])")

    @classmethod
    def from_file(cls, path: str = DATA_FILE) -> "IngredientDictionary":
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    # --- matching -------------------------------------------------------------------
    def find_all(self, text: str) -> list[tuple[str, Mapping]]:
        return [(m.group(1), self.by_alias[m.group(1)]) for m in self._regex.finditer(text)]

    def fuzzy(self, text: str, cutoff: float = 0.84) -> tuple[str, Mapping] | None:
        if len(text) < 4:
            return None
        hit = difflib.get_close_matches(text, self._alias_list, n=1, cutoff=cutoff)
        return (hit[0], self.by_alias[hit[0]]) if hit else None

    def lookup(self, term: str) -> Mapping | None:
        t = term.lower().strip()
        return self.by_name.get(t) or self.by_alias.get(t)


def clean_token(token: str) -> str:
    t = token.lower()
    t = PERCENT_RE.sub(" ", t)
    t = re.sub(r"[\[\]{}]", " ", t)
    t = re.sub(r"[*•·_\"“”]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" .:;,-")
    return t


def split_ingredients(text: str) -> list[str]:
    """Split an ingredient paragraph on commas/semicolons at parenthesis depth 0."""
    if not text:
        return []
    text = text.replace("\n", " ")
    parts, buf, depth = [], [], 0
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch in ",;" and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    out = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip(" .:;,-")
        # "salt and pepper" at depth 0 -> two items
        if p and "(" not in p and re.search(r"\sand\s", p, re.I) and len(p.split()) <= 6:
            out += [x.strip() for x in re.split(r"\s+and\s+", p, flags=re.I) if x.strip()]
        elif p:
            out.append(p)
    return out


def _mk(raw, alias, m: Mapping, match_type, is_trace) -> NormalizedIngredient:
    return NormalizedIngredient(raw=raw, name=m.standard_name, matched_alias=alias, match_type=match_type,
                                category=m.category, allergen_groups=list(m.allergen_groups),
                                intolerance_groups=list(m.intolerance_groups), dietary_tags=list(m.dietary_tags),
                                is_trace=is_trace)


def normalize_token(raw: str, d: IngredientDictionary, force_trace: bool = False) -> list[NormalizedIngredient]:
    """Return one or more normalized ingredients for a raw token (a token can hold several,
    e.g. 'emulsifier (soy lecithin)' -> Emulsifier + Soy)."""
    t = clean_token(raw)
    if not t:
        return []
    if NEGATION_LEAD_RE.search(t):
        # "no added sugar", "free from nuts" describe absence, not an ingredient
        return []
    t = X_FREE_RE.sub(" ", t).strip()  # "gluten-free oats" -> "oats"
    if not t:
        return []
    tm = TRACE_RE.search(t)
    is_trace = force_trace or bool(tm)
    trace_type = "may_contain" if (force_trace or (tm and "may" in tm.group(1).lower())) else ("listed" if tm else None)
    t = TRACE_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    hits = d.find_all(t)
    match_type = "exact"
    if not hits:
        fixed = t
        for a, b in OCR_FIXES:
            fixed = fixed.replace(a, b)
        if fixed != t:
            hits = d.find_all(fixed)
            match_type = "ocr_corrected"
    if not hits:
        f = d.fuzzy(t)
        if f:
            hits, match_type = [f], "fuzzy"
        else:
            words = [w for w in re.split(r"[\s()/]+", t) if len(w) >= 4]
            for w in words:
                f = d.fuzzy(w, cutoff=0.8)
                if f:
                    hits.append(f)
            match_type = "fuzzy" if hits else "unrecognized"
    if not hits:
        return [NormalizedIngredient(raw=raw.strip(), name=None, is_trace=is_trace, trace_type=trace_type)]

    seen, out = set(), []
    for alias, m in hits:
        if m.standard_name in seen:
            continue
        seen.add(m.standard_name)
        n = _mk(raw.strip(), alias, m, match_type, is_trace)
        n.trace_type = trace_type
        out.append(n)
    return out


def normalize_list(raw_items: list[str], d: IngredientDictionary, force_trace: bool = False) -> list[NormalizedIngredient]:
    out: list[NormalizedIngredient] = []
    for item in raw_items:
        for sub in split_ingredients(item) if ("," in item and "(" not in item) else [item]:
            out.extend(normalize_token(sub, d, force_trace=force_trace))
    # merge duplicates: keep one entry per standard name; a non-trace mention wins over a trace one
    merged: dict[str, NormalizedIngredient] = {}
    unknown: list[NormalizedIngredient] = []
    for n in out:
        if n.name is None:
            unknown.append(n)
            continue
        prev = merged.get(n.name)
        if prev is None:
            merged[n.name] = n
        elif prev.is_trace and not n.is_trace:
            merged[n.name] = n
    return list(merged.values()) + unknown


_default: IngredientDictionary | None = None


def get_dictionary() -> IngredientDictionary:
    """Dictionary loaded from the DB (ingredient_mapping); falls back to the JSON seed file."""
    global _default
    if _default is None:
        rows = None
        try:
            from app.database.session import SessionLocal
            from app.models import IngredientMapping
            with SessionLocal() as db:
                recs = db.query(IngredientMapping).all()
                if recs:
                    rows = [{"standard_name": r.standard_name, "category": r.category, "aliases": r.aliases,
                             "allergen_group": r.allergen_group, "intolerance_group": r.intolerance_group,
                             "dietary_tags": r.dietary_tags} for r in recs]
        except Exception:  # table missing before init — use file
            rows = None
        _default = IngredientDictionary(rows) if rows else IngredientDictionary.from_file()
    return _default


def reset_dictionary_cache() -> None:
    global _default
    _default = None
