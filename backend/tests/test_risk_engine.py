from app.engines.ingredient_normalizer import IngredientDictionary
from app.engines.risk_engine import LOW_MESSAGE, RiskEngine

E = RiskEngine(IngredientDictionary.from_file())
DEMO = {"allergies": ["Peanut"], "intolerances": ["Lactose"], "dietary_preferences": ["Vegetarian"]}
LABEL = ["Wheat flour", "Milk solids", "Sugar", "Cocoa", "Peanut traces", "Soy lecithin"]


def test_demo_label_is_high_with_exact_explanations():
    r = E.analyze(profile=DEMO, raw_ingredients=LABEL)
    assert r.risk_level == "HIGH"
    reasons = [c["reason"] for c in r.detected_conflicts]
    assert "Peanut traces were detected and match your peanut allergy profile." in reasons
    assert "Milk solids may conflict with your lactose intolerance." in reasons
    assert r.explanation.startswith("Peanut traces were detected")


def test_direct_allergy_high():
    r = E.analyze(profile={"allergies": ["Peanut"]}, raw_ingredients=["roasted groundnuts", "salt"])
    assert r.risk_level == "HIGH"
    assert r.detected_conflicts[0]["profile_match"] == "peanut allergy"


def test_may_contain_is_caution():
    r = E.analyze(profile={"allergies": ["Peanut"]}, raw_ingredients=["rice flour", "salt"],
                  allergen_statements={"contains": [], "may_contain": ["peanuts"]})
    assert r.risk_level == "CAUTION"
    assert any("may contain" in w.lower() for w in r.warnings)


def test_intolerance_caution():
    r = E.analyze(profile={"intolerances": ["Lactose"]}, raw_ingredients=["milk powder", "sugar"])
    assert r.risk_level == "CAUTION" and r.detected_conflicts[0]["type"] == "intolerance"


def test_vegetarian_preference_conflict():
    r = E.analyze(profile={"dietary_preferences": ["Vegetarian"]}, raw_ingredients=["chicken", "onion"])
    assert r.risk_level == "CAUTION"
    assert "vegetarian" in r.detected_conflicts[0]["reason"].lower()


def test_vegan_flags_honey_or_dairy():
    r = E.analyze(profile={"dietary_preferences": ["Vegan"]}, raw_ingredients=["ghee", "wheat flour"])
    assert r.risk_level == "CAUTION"


def test_low_result_wording_never_claims_safety():
    r = E.analyze(profile=DEMO, raw_ingredients=["rice", "moong dal", "salt"])
    assert r.risk_level == "LOW" and r.explanation == LOW_MESSAGE
    text = (r.explanation + " ".join(r.warnings)).lower()
    assert "100% safe" not in text and "safe to eat" not in text


def test_no_ingredients_warns_and_low_confidence():
    r = E.analyze(profile=DEMO, raw_ingredients=[])
    assert r.confidence <= 0.3
    assert any("No ingredient information" in w for w in r.warnings)


def test_hidden_sugar_for_declared_diabetes():
    r = E.analyze(profile={"health_conditions": ["diabetes"]}, raw_ingredients=["maida", "liquid glucose", "maltodextrin"])
    assert r.risk_level == "CAUTION"
    assert any("hidden sugars" in c["reason"].lower() for c in r.detected_conflicts)
    assert all("you have" not in c["reason"].lower() for c in r.detected_conflicts)


def test_hing_may_contain_wheat():
    r = E.analyze(profile={"allergies": ["Wheat"]}, raw_ingredients=["asafoetida", "salt"])
    assert r.risk_level == "CAUTION"


def test_low_ocr_confidence_warning():
    r = E.analyze(profile=DEMO, raw_ingredients=["rice"], ocr_confidence=0.4)
    assert any("low confidence" in w for w in r.warnings)
