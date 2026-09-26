"""Builds the demo food catalog from dietary_risk_dataset.csv (+ typical ingredient lists).

The CSV has unquoted commas inside some names/notes (e.g. "Spinach (Cooked, 100g)"),
so it is parsed with a tolerant, column-count-aware parser instead of csv.reader.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "dietary_risk_dataset.csv")
N_COLS = 21
FIXED_AFTER_NAME = 18  # category .. pcos_risk


def _balanced(s: str) -> bool:
    return s.count("(") == s.count(")")


def parse_dataset(path: str = CSV_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    header = lines[0].split(",")
    assert len(header) == N_COLS, "Unexpected dataset header"
    rows = []
    for ln in lines[1:]:
        parts = ln.split(",")
        food_id = parts[0]
        i, name = 1, parts[1]
        while not _balanced(name):  # re-join names that contain commas inside parentheses
            i += 1
            name += "," + parts[i]
        fixed = parts[i + 1:i + 1 + FIXED_AFTER_NAME]
        notes = ",".join(parts[i + 1 + FIXED_AFTER_NAME:])
        values = [food_id, name.strip()] + fixed + [notes.strip()]
        if len(values) != N_COLS:
            raise ValueError(f"Could not parse dataset row: {ln}")
        rows.append(dict(zip(header, values)))
    return rows


# Typical-recipe ingredient lists for dataset foods (recipes vary; shown as estimates).
DATASET_INGREDIENTS = {
 "F001": ["whole wheat flour (atta)", "water"],
 "F002": ["white rice", "water"],
 "F003": ["brown rice", "water"],
 "F004": ["toor dal", "onion", "tomato", "garlic", "ghee", "cumin", "turmeric", "red chilli", "asafoetida (hing)", "salt"],
 "F005": ["kidney beans (rajma)", "onion", "tomato", "ginger", "garlic", "vegetable oil", "spices", "salt"],
 "F006": ["paneer", "butter", "cream", "tomato", "cashew paste", "onion", "ginger", "garlic", "spices", "sugar", "salt"],
 "F007": ["spinach (palak)", "paneer", "onion", "tomato", "garlic", "ginger", "cream", "spices", "vegetable oil", "salt"],
 "F008": ["potato", "cauliflower", "onion", "tomato", "vegetable oil", "turmeric", "spices", "salt"],
 "F009": ["toor dal", "mixed vegetables", "tamarind", "sambar masala", "asafoetida (hing)", "mustard seeds", "curry leaves", "vegetable oil", "salt"],
 "F010": ["milk", "curd culture"],
 "F011": ["full cream milk"],
 "F012": ["toned milk"],
 "F013": ["refined wheat flour (maida)", "potato", "green peas", "vegetable oil", "spices", "salt"],
 "F014": ["gram flour (besan)", "mixed vegetables", "onion", "refined wheat flour (maida)", "vegetable oil", "spices", "salt"],
 "F015": ["gram flour (besan)", "edible vegetable oil (palm)", "peanuts", "refined wheat flour", "rice flakes", "salt", "spices", "sugar", "citric acid"],
 "F016": ["whole wheat flour", "refined wheat flour", "edible vegetable oil (palm)", "sugar", "wheat bran", "invert syrup", "raising agents (500(ii), 503(ii))", "salt", "malt extract", "emulsifier (soy lecithin)"],
 "F017": ["refined wheat flour (maida)", "sugar", "edible vegetable oil (palm)", "invert syrup", "milk solids", "cocoa solids", "raising agent (500(ii))", "salt", "emulsifier (soy lecithin)", "artificial flavour (vanilla)"],
 "F018": ["potato", "edible vegetable oil (palmolein)", "iodised salt"],
 "F019": ["fox nuts (makhana)", "rice bran oil", "rock salt", "black pepper"],
 "F020": ["roasted chickpea (chana)"],
 "F021": ["water", "mixed fruit concentrate", "sugar", "acidity regulator (330)", "stabilizer (440)", "preservative (211)"],
 "F022": ["buttermilk", "salt", "cumin", "coriander"],
 "F023": ["carbonated water", "sugar", "caramel colour (150d)", "acidity regulator (338)", "caffeine", "natural flavours"],
 "F024": ["coconut water"],
 "F025": ["tea leaves", "milk", "sugar", "ginger", "cardamom", "water"],
 "F026": ["idli rice", "urad dal", "salt", "water"],
 "F027": ["rice", "urad dal", "potato", "onion", "mustard seeds", "curry leaves", "vegetable oil", "spices", "salt"],
 "F028": ["flattened rice (poha)", "peanuts", "onion", "potato", "mustard seeds", "curry leaves", "turmeric", "vegetable oil", "sugar", "lemon juice", "salt"],
 "F029": ["semolina (rava)", "onion", "mustard seeds", "urad dal", "curry leaves", "green chilli", "vegetable oil", "salt"],
 "F030": ["whole wheat flour (atta)", "potato", "ghee", "onion", "spices", "salt"],
 "F031": ["egg"],
 "F032": ["chicken", "onion", "tomato", "ginger", "garlic", "vegetable oil", "spices", "salt"],
 "F033": ["fish", "coconut", "onion", "tomato", "tamarind", "spices", "vegetable oil", "salt"],
 "F034": ["mutton", "onion", "tomato", "ginger", "garlic", "vegetable oil", "spices", "salt"],
 "F035": ["banana"], "F036": ["apple"], "F037": ["mango"], "F038": ["orange"], "F039": ["watermelon"],
 "F040": ["spinach"],
 "F041": ["bottle gourd (lauki)", "cumin", "turmeric", "vegetable oil"],
 "F042": ["okra (bhindi)", "onion", "vegetable oil", "spices"],
 "F043": ["potato"], "F044": ["tomato"],
 "F045": ["roasted peanuts", "salt"],
 "F046": ["cashew nuts"], "F047": ["almonds"],
 "F048": ["khoya", "refined wheat flour (maida)", "sugar", "ghee", "cardamom", "rose water"],
 "F049": ["chenna", "sugar", "water", "cardamom"],
 "F050": ["refined wheat flour (maida)", "sugar", "vegetable oil", "saffron", "citric acid"],
 "F051": ["cocoa mass", "sugar", "cocoa butter", "emulsifier (sunflower lecithin)", "vanilla"],
 "F052": ["refined wheat flour (maida)", "palm oil", "iodised salt", "wheat gluten", "thickener (508)", "acidity regulator (501(i))", "mixed spices", "onion powder", "garlic powder", "sugar", "flavour enhancer (627, 631)", "turmeric"],
 "F053": ["green peas", "carrot", "sweet corn", "french beans"],
 "F054": ["tomato paste", "sugar", "salt", "acidity regulator (260)", "onion powder", "garlic powder", "spices", "preservative (211)"],
 "F055": ["water", "soybeans", "wheat", "salt", "preservative (211)"],
 "F056": ["urad dal flour", "salt", "black pepper", "asafoetida (hing)", "sodium bicarbonate", "vegetable oil"],
 "F057": ["ghee"], "F058": ["mustard oil"], "F059": ["green tea leaves"],
 "F060": ["rolled oats", "water"],
}

ALLERGEN_MAP = {"gluten": "gluten", "peanut": "peanut", "dairy": "milk", "tree nut": "tree_nut",
                "egg": "egg", "fish": "fish", "soy": "soy"}


def _num(v: str):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def dataset_foods() -> list[dict]:
    foods = []
    for r in parse_dataset():
        declared, may_contain = [], []
        for a in [x.strip() for x in r["common_allergens"].split(";") if x.strip() and x.strip() != "None"]:
            base = a.lower().replace(" trace", "").strip()
            key = ALLERGEN_MAP.get(base, base)
            (may_contain if a.lower().endswith("trace") else declared).append(key)
        ftype = r["food_type"]
        cat = r["category"]
        foods.append({
            "external_id": r["food_id"],
            "name": r["food_name"],
            "category": cat,
            "ingredients": DATASET_INGREDIENTS.get(r["food_id"], []),
            "nutrition_data": {
                "calories": _num(r["calories_kcal"]), "protein": _num(r["protein_g"]),
                "carbohydrates": _num(r["carbs_g"]), "sugar": _num(r["sugar_g"]),
                "fiber": _num(r["fiber_g"]), "fat": _num(r["fat_g"]),
                "sodium": _num(r["sodium_mg"]), "potassium": _num(r["potassium_mg"]),
            },
            "source": r["source_basis"],
            "is_packaged": "Packaged" in ftype,
            "meta": {
                "food_type": ftype,
                "serving_size_g": _num(r["serving_size_g"]),
                "glycemic_load": r["glycemic_load_category"],
                "declared_allergens": declared,
                "may_contain": may_contain,
                "condition_ratings": {"diabetes": r["diabetes_risk"], "ckd": r["ckd_risk"],
                                       "hypertension": r["hypertension_risk"], "pcos": r["pcos_risk"]},
                "notes": r["notes"],
                "ingredients_basis": "typical recipe (estimate)",
                "dataset": "dietary_risk_dataset.csv",
            },
        })
    return foods


def extra_foods() -> list[dict]:
    with open(os.path.join(HERE, "foods_extra.json"), encoding="utf-8") as f:
        return json.load(f)


def all_foods() -> list[dict]:
    return dataset_foods() + extra_foods()


if __name__ == "__main__":
    fs = all_foods()
    print(len(fs), "foods")
    for f in fs[38:42]:
        print(f["external_id"], f["name"], f["meta"].get("notes"))
