from app.engines.ingredient_normalizer import IngredientDictionary, normalize_list, split_ingredients

D = IngredientDictionary.from_file()


def names(items):
    return [i.name for i in normalize_list(items, D)]


def test_spec_example_normalizes():
    raw = "Milk solids, whey protein, sugar, cocoa,\narachis traces, soy lecithin"
    out = normalize_list(split_ingredients(raw), D)
    assert [i.name for i in out] == ["Milk", "Whey", "Sugar", "Cocoa", "Peanut", "Soy"]
    peanut = next(i for i in out if i.name == "Peanut")
    assert peanut.is_trace and peanut.trace_type == "listed"


def test_synonyms_resolve():
    assert names(["groundnut oil"]) == ["Peanut"] or "Peanut" in names(["groundnut"])
    assert "Peanut" in names(["arachis"])
    assert "Milk" in names(["skim milk powder"]) and "Milk" in names(["dairy solids"])
    assert "Casein" in names(["sodium caseinate"])
    assert "Egg" in names(["albumin"]) and "Egg" in names(["egg yolk"])
    assert "Wheat" in names(["atta"]) and "Wheat" in names(["wheat starch"])
    assert "Soy" in names(["soya"])
    assert "Almond" in names(["almond flour"])
    assert "Whey" in names(["whey concentrate"])


def test_ocr_noise_and_case_tolerated():
    got = names(["  MILK  SOLIDS. ", "Peanvt", "SUGAR (12%)"])
    assert "Milk" in got and "Sugar" in got and "Peanut" in got


def test_negations_ignored():
    got = normalize_list(["gluten-free", "no added sugar"], D)
    assert all(i.name is None or i.name not in ("Sugar", "Gluten") for i in got)


def test_may_contain_is_precautionary():
    out = normalize_list(["may contain peanuts"], D)
    assert out[0].name == "Peanut" and out[0].trace_type == "may_contain"


def test_split_keeps_parentheses():
    parts = split_ingredients("Edible vegetable oil (palm, sunflower), salt and pepper")
    assert parts[0].startswith("Edible vegetable oil") and "salt" in [p.lower() for p in parts]


def test_unrecognized_kept_for_warning():
    out = normalize_list(["zqxv compound"], D)
    assert out[0].name is None
