"""Turns raw OCR text into structured label data.

RAW OCR TEXT -> TEXT CLEANING -> INGREDIENT SECTION DETECTION -> ALLERGEN STATEMENTS
-> NUTRITION SECTION DETECTION. Normalization happens later in the ingredient engine,
after the user has reviewed/edited the extracted list.
"""
from __future__ import annotations

import difflib
import re

from app.engines.ingredient_normalizer import split_ingredients

ING_HEAD = re.compile(r"[il1|!]ngred[il1|!]ents?\s*(?:list)?\s*[:;.\-]?", re.I)
SECTION_END = re.compile(
    r"(nutrition(?:al)?\s*(?:information|facts|value|info)?|allergen(?:s)?\s*(?:information|advice|declaration)?\s*[:;]|"
    r"\bcontains\s*[:;]|\bmay\s+contain|manufactured\s+(?:by|for|in|on)|processed\s+in\s+a\s+facility|"
    r"best\s+before|\bmfd\b|\bmfg\b|marketed\s+by|net\s+(?:wt|weight|quantity)|\bstorage\b|store\s+in|\bfssai\b|\bmrp\b|"
    r"use\s+by|packed\s+on|batch\s+no|lic\.?\s*no|veg(?:etarian)?\s+symbol|customer\s+care|"
    r"\n[^\n,]{0,25}\binformation\b|\b[a-z0-9]{1,5}\s?[ef]?ergen\s*(?:information|info)?\s*[:;])",
    re.I,
)
CONTAINS_RE = re.compile(r"(?:allergen(?:s)?\s*(?:information|advice|declaration)?\s*[:;]\s*)?\bcontains\s*[:;]?\s*([^.\n]+)", re.I)
MAY_CONTAIN_RE = re.compile(
    r"(?:ma[yv]\s+contain(?:\s+traces\s+of)?|(?:manufactured|made|processed|produced|packed)\s+(?:in|on)\s*(?:a\s+)?"
    r"(?:facility|plant|line|premises|equipment)[^.\n]*?(?:also\s+)?(?:processes|handles|uses|with)|shared\s+equipment\s+with)\s*:?\s*([^.\n]+)",
    re.I,
)

NUTRIENTS = {
    "calories": re.compile(r"\b(energy|calories|calorie|kcal)\b", re.I),
    "protein": re.compile(r"\bprotein[s]?\b", re.I),
    "carbohydrates": re.compile(r"\b(total\s+)?carbo\s*hydrates?\b|\bcarbs\b", re.I),
    "added_sugar": re.compile(r"\badded\s+sugars?\b", re.I),
    "sugar": re.compile(r"\b(total\s+)?sugars?\b", re.I),
    "fiber": re.compile(r"\b(dietary\s+)?fib(re|er)s?\b", re.I),
    "fat": re.compile(r"\b(total\s+)?fats?\b", re.I),
    "saturated_fat": re.compile(r"\bsaturated(\s+fat(ty acids)?)?\b", re.I),
    "trans_fat": re.compile(r"\btrans(\s+fat(ty acids)?)?\b", re.I),
    "sodium": re.compile(r"\bsodium\b", re.I),
    "salt": re.compile(r"\bsalt\b", re.I),
    "potassium": re.compile(r"\bpotassium\b", re.I),
}
NUM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kcal|kj|mg|mcg|µg|g)?", re.I)


def clean_text(raw: str) -> str:
    t = raw.replace("\r", "\n")
    t = re.sub(r"-\n(?=[a-z])", "", t)  # re-join hyphenated line breaks
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"(?<=\d)[oO](?=\d)", "0", t)  # 1O.5 -> 10.5
    t = re.sub(r"(?<=\d)[lI](?=\d)", "1", t)
    t = t.replace("’", "'").replace("‘", "'")
    return "\n".join(ln.strip() for ln in t.split("\n")).strip()


ALLERGEN_WORDS = ["wheat", "milk", "soy", "soya", "peanut", "peanuts", "tree nuts", "nuts", "egg", "eggs", "fish",
                  "shellfish", "crustaceans", "molluscs", "sesame", "mustard", "gluten", "celery", "sulphites",
                  "lupin", "almond", "cashew", "barley", "oats", "rye"]
_OCR_SWAPS = str.maketrans({"a": "o", "v": "y", "0": "o", "1": "l", "5": "s", "|": "l"})


def _fix_allergen_word(w: str) -> str:
    """Allergen statements are short, well-known words, so OCR slips ('sav' for 'soy') can be fixed safely."""
    low = w.lower().strip()
    if low in ALLERGEN_WORDS or len(low) > 20:
        return w
    for cand in (low.translate(_OCR_SWAPS), low.replace("rn", "m")):
        if cand in ALLERGEN_WORDS:
            return cand
    close = difflib.get_close_matches(low, ALLERGEN_WORDS, n=1, cutoff=0.75)
    return close[0] if close else w


def _split_statement(s: str) -> list[str]:
    s = re.sub(r"\b(traces\s+of|trace\s+amounts\s+of|other|products|ingredients)\b", " ", s, flags=re.I)
    items = re.split(r",|;|/|\band\b|&", s, flags=re.I)
    return [_fix_allergen_word(re.sub(r"\s+", " ", i).strip(" .:-")) for i in items if i.strip(" .:-")]


def extract_ingredient_section(text: str) -> tuple[str, bool]:
    """Returns (ingredient_text, heading_found)."""
    m = ING_HEAD.search(text)
    if m:
        rest = text[m.end():]
        end = SECTION_END.search(rest)
        return (rest[: end.start()] if end else rest).strip(), True
    # Fallback: longest comma-dense block before any nutrition heading
    head = re.split(r"nutrition", text, maxsplit=1, flags=re.I)[0]
    blocks = [b for b in re.split(r"\n\s*\n", head) if b.count(",") >= 2]
    return (max(blocks, key=lambda b: b.count(",")) if blocks else "").strip(), False


def extract_allergen_statements(text: str) -> dict:
    flat = text.replace("\n", " ")
    contains, may = [], []
    for m in MAY_CONTAIN_RE.finditer(flat):
        may += _split_statement(m.group(1))
    for m in CONTAINS_RE.finditer(flat):
        pre = flat[max(0, m.start() - 4): m.start()].lower()
        if "may" in pre:
            continue
        contains += _split_statement(m.group(1))
    return {"contains": contains, "may_contain": may}


def _column_index(text: str) -> tuple[int, str]:
    """If the panel has both per-100g and per-serving columns, pick the per-serving column."""
    low = text.lower()
    p100 = re.search(r"per\s*100\s*(g|ml)", low)
    pserv = re.search(r"per\s*(serv(e|ing)|pack|portion|piece)[^\n]*?(\(\s*\d+\s*(g|ml)\s*\))?", low)
    if p100 and pserv:
        return (1 if p100.start() < pserv.start() else 0), "per serving"
    if pserv:
        return 0, "per serving"
    if p100:
        return 0, "per 100 g"
    return 0, "unspecified"


def _cross_check(key, nums, idx, serving_g, notes):
    """Two-column panels: per-serving should be per-100g x serving/100. Recover lost decimals, flag the rest."""
    if idx != 1 or not serving_g or len(nums) < 1:
        return None
    per100 = nums[0][0]
    expected = per100 * serving_g / 100.0
    if len(nums) < 2:  # can't tell which column survived OCR -> keep it, ask the user
        notes.append(key)
        return nums[0][0], None
    got = nums[1][0]
    tol = max(0.15 * expected, 0.3)
    if abs(got - expected) <= tol:
        return got, None
    if abs(got / 10 - expected) <= tol:
        return round(got / 10, 2), "decimal"
    notes.append(key)
    return got, None


def extract_nutrition(text: str) -> dict:
    idx, basis = _column_index(text)
    serving = re.search(r"serv(?:ing|e)\s*size\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(g|ml)", text, re.I) or \
              re.search(r"per\s*serv(?:ing|e)\s*\(\s*(\d+(?:\.\d+)?)\s*(g|ml)\s*\)", text, re.I)
    out: dict = {}
    mismatched: list[str] = []
    adjusted: list[str] = []
    serving_g = float(serving.group(1)) if serving and serving.group(2).lower() == "g" else None
    for line in text.split("\n"):
        label_part = re.split(r"\d", line, maxsplit=1)[0]
        for key, rx in NUTRIENTS.items():
            if key in out or not rx.search(label_part):
                continue
            if key == "sugar" and NUTRIENTS["added_sugar"].search(label_part):
                continue
            if key == "fat" and (NUTRIENTS["saturated_fat"].search(label_part) or NUTRIENTS["trans_fat"].search(label_part)):
                continue
            lu = re.search(r"\(\s*(mg|g|kcal|kj)\s*\)", label_part, re.I)
            label_unit = lu.group(1).lower() if lu else ""
            nums = [(float(n.replace(",", ".")), (u or label_unit).lower()) for n, u in NUM_RE.findall(line[len(label_part):])]
            if key == "calories":
                kcal = [v for v, u in nums if u == "kcal"]
                if kcal:
                    nums = [(v, "kcal") for v in kcal]
                elif nums and all(u == "kj" for _, u in nums):
                    nums = [(round(v / 4.184), "kcal") for v, _ in nums]
                else:
                    nums = [(v, u) for v, u in nums if u != "kj"]
            if not nums:
                continue
            val, unit = nums[idx] if len(nums) > idx else nums[0]
            if key in ("protein", "carbohydrates", "sugar", "fiber", "fat", "sodium", "calories", "potassium"):
                chk = _cross_check(key, nums, idx, serving_g, mismatched)
                if chk:
                    val = chk[0]
                    if chk[1]:
                        adjusted.append(key)
            if key in ("sodium", "potassium"):
                if unit == "g":
                    val = val * 1000
            elif unit == "mg":
                val = val / 1000
            out[key] = round(val, 2)
            break
    if "sodium" not in out and "salt" in out:
        out["sodium"] = round(out["salt"] * 393.4)  # 1 g salt ~ 393 mg sodium
        out["sodium_from_salt"] = True
    out.pop("salt", None)
    out["basis"] = basis
    if adjusted:
        out["adjusted"] = adjusted
    if mismatched:
        out["mismatched"] = mismatched
    if serving:
        out["serving_size"] = f"{serving.group(1)} {serving.group(2)}"
    return out


def parse_label(raw_text: str) -> dict:
    text = clean_text(raw_text or "")
    ing_text, heading = extract_ingredient_section(text)
    ingredients = split_ingredients(ing_text)
    statements = extract_allergen_statements(text)
    nut_start = re.search(r"nutrition", text, re.I)
    nutrition = extract_nutrition(text[nut_start.start():] if nut_start else text)
    warnings = []
    if not heading:
        warnings.append("The 'Ingredients' heading wasn't found; the list was guessed. Please review it.")
    if not ingredients:
        warnings.append("No ingredient list was detected.")
    found = [k for k in ("calories", "protein", "carbohydrates", "sugar", "fat", "sodium") if k in nutrition]
    if len(found) < 3:
        warnings.append("Some nutrition values may not have been detected.")
    if nutrition.get("adjusted"):
        warnings.append("Some nutrition values were recalculated from the per-100 g column: " + ", ".join(nutrition["adjusted"]) + ". Please confirm them.")
    if nutrition.get("mismatched"):
        warnings.append("Please verify these nutrition values (the two columns couldn't be cross-checked): " + ", ".join(nutrition["mismatched"]) + ".")
    if nutrition.get("basis") == "per 100 g":
        warnings.append("Nutrition values appear to be per 100 g. Adjust them if you ate a different amount.")
    return {"clean_text": text, "ingredients": ingredients, "allergen_statements": statements,
            "nutrition": nutrition, "ingredient_heading_found": heading, "warnings": warnings}
