import json
import os
import shutil

import pytest

from app.services.ocr.demo_provider import DemoOCR
from app.services.ocr.label_parser import extract_allergen_statements, extract_nutrition, parse_label

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "data")
SAMPLES = json.load(open(os.path.join(DATA, "sample_labels.json")))


def _sample(file):
    return next(s for s in SAMPLES.values() if s["file"] == file)


def test_parse_demo_label_text():
    p = parse_label(_sample("chococrunch_biscuits.jpg")["text"])
    assert p["ingredients"] == ["Wheat flour", "Milk solids", "Sugar", "Cocoa", "Peanut traces", "Soy lecithin"]
    assert p["allergen_statements"]["may_contain"] == ["tree nuts"]
    n = p["nutrition"]
    assert n["calories"] == 144 and n["sodium"] == 120 and n["basis"] == "per serving"


def test_parse_tolerates_messy_ocr():
    raw = "lNGREDIENTS : Wheat flour,\nmilk  solids ,sugar;\ncocoa , arachis traces\nNutrition Facts\nEnergy 450 kcal\nSodium 300 mg\nProtein 5 g"
    p = parse_label(raw)
    assert len(p["ingredients"]) >= 4
    assert p["nutrition"]["sodium"] == 300


def test_salt_converted_to_sodium():
    n = extract_nutrition("Nutrition\nSalt (g) 1.0")
    assert round(n["sodium"]) == 394 or round(n["sodium"]) == 393  # salt g / 2.54 * 1000


def test_facility_statement_is_precautionary():
    s = extract_allergen_statements("Made in a facility that also processes milk and peanuts.")
    assert "milk" in " ".join(s["may_contain"]).lower()


def test_missing_heading_warns():
    p = parse_label("wheat flour, sugar, salt")
    assert any("heading" in w for w in p["warnings"])


def test_demo_provider_recognises_sample_images():
    with open(os.path.join(DATA, "sample_labels", "chococrunch_biscuits.jpg"), "rb") as f:
        r = DemoOCR().extract_text(f.read())
    assert "Peanut traces" in r.text


@pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract not installed")
def test_tesseract_reads_sample_label():
    from app.services.ocr.tesseract_provider import TesseractOCR
    with open(os.path.join(DATA, "sample_labels", "chococrunch_biscuits.jpg"), "rb") as f:
        r = TesseractOCR().extract_text(f.read())
    p = parse_label(r.text)
    assert [i.lower() for i in p["ingredients"]] == ["wheat flour", "milk solids", "sugar", "cocoa", "peanut traces", "soy lecithin"]
