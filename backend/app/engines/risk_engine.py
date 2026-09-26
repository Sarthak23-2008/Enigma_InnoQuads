"""ENGINE 1 — Food Safety / Ingredient Risk Engine (deterministic, explainable).

Input : user profile + normalized ingredients + allergen statements + nutrition + food metadata
Output: risk_level (LOW | CAUTION | HIGH), detected_conflicts, explanation, confidence, warnings

Rules
 1. Direct allergy match                          -> HIGH
 2. Trace listed in ingredients ("peanut traces")  -> HIGH
    Precautionary "may contain"/shared facility   -> CAUTION
 3. Intolerance match                             -> CAUTION
 4. Dietary preference conflict                   -> CAUTION
 5. Declared health consideration vs nutrients    -> CAUTION (never a diagnosis)
 6. Nothing relevant                              -> LOW ("No potential conflict detected based on the
                                                     available ingredient information.")  Never "100% safe".
AI/LLMs are never the safety authority here; this module is pure rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.engines.ingredient_normalizer import (
    IngredientDictionary, NormalizedIngredient, get_dictionary, normalize_list,
)

LOW, CAUTION, HIGH = "LOW", "CAUTION", "HIGH"
LOW_MESSAGE = "No potential conflict detected based on the available ingredient information."

ALLERGY_GROUPS = {
    "peanut": "peanut", "peanuts": "peanut", "groundnut": "peanut",
    "tree nuts": "tree_nut", "tree nut": "tree_nut", "nuts": "tree_nut",
    "milk": "milk", "dairy": "milk", "egg": "egg", "eggs": "egg",
    "soy": "soy", "soya": "soy", "wheat": "wheat", "fish": "fish",
    "shellfish": "shellfish", "crustacean": "shellfish", "sesame": "sesame", "mustard": "mustard",
    "celery": "celery", "sulphites": "sulphite", "sulfites": "sulphite", "lupin": "lupin",
    "molluscs": "mollusc", "mollusc": "mollusc", "gluten": "wheat",
}
GROUP_LABEL = {"peanut": "peanut", "tree_nut": "tree nut", "milk": "milk", "egg": "egg", "soy": "soy",
               "wheat": "wheat", "fish": "fish", "shellfish": "shellfish", "sesame": "sesame",
               "mustard": "mustard", "celery": "celery", "sulphite": "sulphite", "lupin": "lupin",
               "mollusc": "mollusc"}
INTOLERANCE_KEYS = {"lactose": "lactose", "gluten": "gluten", "fructose": "fructose"}

# per-serving heuristics used for preferences / declared health considerations
SODIUM_HIGH_MG = 400
SUGAR_HIGH_G = 10
POTASSIUM_HIGH_MG = 300

CONDITIONS = {
    "diabetes": "blood-sugar management (diabetes)",
    "hypertension": "blood-pressure management (hypertension)",
    "ckd": "kidney health (CKD)",
    "pcos": "PCOS",
}


@dataclass
class RiskResult:
    risk_level: str
    detected_conflicts: list[dict]
    explanation: str
    confidence: float
    warnings: list[str]
    notes: list[str] = field(default_factory=list)
    ingredients: list[str] = field(default_factory=list)
    ingredient_details: list[dict] = field(default_factory=list)
    unrecognized: list[str] = field(default_factory=list)
    data_certainty: str = "known"
    disclaimer: str = ("SafeBite gives dietary information based on the available ingredient data. "
                       "It is not medical advice. If you have a severe allergy, always read the physical label "
                       "and follow your doctor's guidance.")

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def _key(s: str) -> str:
    return (s or "").strip().lower().replace("-", " ").replace("_", " ")


def _pretty(raw: str, fallback: str) -> str:
    import re
    r = re.sub(r"\(?\s*\d+(?:[.,]\d+)?\s*%\s*\)?", "", raw or "").strip(" .,:;")
    r = re.sub(r"(?i)^(may contain( traces of)?|traces? of)\s+", "", r).strip()
    if not r:
        r = fallback
    return r[:1].upper() + r[1:]


def _verb(subject: str) -> str:
    w = subject.split("(")[0].strip().split()[-1].lower() if subject.strip() else ""
    return "were" if (w.endswith("s") and not w.endswith("ss")) else "was"


class RiskEngine:
    def __init__(self, dictionary: IngredientDictionary | None = None):
        self.d = dictionary or get_dictionary()

    # ------------------------------------------------------------------ public
    def analyze(self, *, profile: dict, ingredients: list[NormalizedIngredient] | None = None,
                raw_ingredients: list[str] | None = None, allergen_statements: dict | None = None,
                nutrition: dict | None = None, food_meta: dict | None = None,
                data_certainty: str = "known", ocr_confidence: float | None = None) -> RiskResult:
        if ingredients is None:
            ingredients = normalize_list(raw_ingredients or [], self.d)
        statements = allergen_statements or {}
        declared = normalize_list(statements.get("contains", []), self.d)
        precautionary = normalize_list(statements.get("may_contain", []), self.d, force_trace=True)
        nutrition = {k: v for k, v in (nutrition or {}).items() if v is not None}
        meta = food_meta or {}

        conflicts: list[dict] = []
        notes: list[str] = []
        warnings: list[str] = []

        allergies = [a for a in profile.get("allergies", []) if a]
        intolerances = [i for i in profile.get("intolerances", []) if i]
        prefs = [_key(p) for p in profile.get("dietary_preferences", []) if p]
        conditions = [_key(c) for c in profile.get("health_conditions", []) if c]

        recognized = [i for i in ingredients if i.name]
        unrecognized = [i.raw for i in ingredients if not i.name]

        # ---------- 1/2. allergies ----------
        for allergy in allergies:
            label = allergy.strip()
            group = ALLERGY_GROUPS.get(_key(label))
            custom_names = self._custom_names(label) if not group else set()
            for ing in recognized:
                if self._matches_allergy(ing, group, custom_names, label):
                    disp = _pretty(ing.raw, ing.name)
                    if ing.trace_type == "may_contain":
                        conflicts.append(self._c(ing, disp, f"{label.lower()} allergy", "may_contain", "caution",
                                                 f"The label says it may contain {disp.lower()}, which matches your {label.lower()} allergy profile (possible cross-contact).",
                                                 group or _key(label)))
                    elif ing.trace_type == "listed":
                        conflicts.append(self._c(ing, disp, f"{label.lower()} allergy", "trace", "high",
                                                 f"{disp} {_verb(disp)} detected and match your {label.lower()} allergy profile.",
                                                 group or _key(label)))
                    else:
                        conflicts.append(self._c(ing, disp, f"{label.lower()} allergy", "allergy", "high",
                                                 f"{disp} {_verb(disp)} detected and matches your {label.lower()} allergy profile.",
                                                 group or _key(label)))
                elif group == "soy" and "possible_soy" in ing.dietary_tags:
                    conflicts.append(self._c(ing, _pretty(ing.raw, ing.name), "soy allergy", "possible", "caution",
                                             "Lecithin is listed without its source. It is often made from soy, so check with the manufacturer.",
                                             "soy"))
                elif group == "wheat" and "may_contain_gluten" in ing.dietary_tags:
                    conflicts.append(self._c(ing, _pretty(ing.raw, ing.name), "wheat allergy", "possible", "caution",
                                             self._maybe_gluten_reason(ing), "wheat"))
            for ing in declared:
                if ing.name and self._matches_allergy(ing, group, custom_names, label):
                    disp = _pretty(ing.raw, ing.name)
                    conflicts.append(self._c(ing, disp, f"{label.lower()} allergy", "allergy", "high",
                                             f"The label's allergen statement lists {disp.lower()}, which matches your {label.lower()} allergy profile.",
                                             group or _key(label)))
            for ing in precautionary:
                if ing.name and self._matches_allergy(ing, group, custom_names, label):
                    disp = _pretty(ing.raw, ing.name)
                    conflicts.append(self._c(ing, disp, f"{label.lower()} allergy", "may_contain", "caution",
                                             f"The label says it may contain {disp.lower()} (possible cross-contact). This matches your {label.lower()} allergy profile.",
                                             group or _key(label)))
            for g in meta.get("declared_allergens", []) or []:
                if group and (g == group or (g == "gluten" and group == "wheat")):
                    conflicts.append({"ingredient": GROUP_LABEL.get(group, g), "standard_name": None,
                                      "profile_match": f"{label.lower()} allergy", "type": "allergy", "severity": "high",
                                      "reason": f"This food is commonly prepared with {GROUP_LABEL.get(group, g)}, which matches your {label.lower()} allergy profile.",
                                      "conflict_group": group})
            for g in meta.get("may_contain", []) or []:
                if group and (g == group or (g == "gluten" and group == "wheat")):
                    conflicts.append({"ingredient": GROUP_LABEL.get(group, g), "standard_name": None,
                                      "profile_match": f"{label.lower()} allergy", "type": "may_contain", "severity": "caution",
                                      "reason": f"This food may contain traces of {GROUP_LABEL.get(group, g)} (possible cross-contact).",
                                      "conflict_group": group})

        # ---------- 3. intolerances ----------
        for intol in intolerances:
            label = intol.strip()
            key = INTOLERANCE_KEYS.get(_key(label))
            custom = self._custom_names(label) if not key else set()
            for ing in recognized + declared:
                hit = (key and key in ing.intolerance_groups) or (not key and self._name_hit(ing, custom, label))
                if hit:
                    disp = _pretty(ing.raw, ing.name)
                    extra = " (listed as a trace)" if ing.is_trace else ""
                    conflicts.append(self._c(ing, disp, f"{label.lower()} intolerance", "intolerance", "caution",
                                             f"{disp}{extra} may conflict with your {label.lower()} intolerance.", key or _key(label)))
                elif key == "gluten" and "may_contain_gluten" in ing.dietary_tags:
                    conflicts.append(self._c(ing, _pretty(ing.raw, ing.name), "gluten intolerance", "possible", "caution",
                                             self._maybe_gluten_reason(ing), "gluten"))
            if key == "gluten":
                for g in (meta.get("declared_allergens") or []) + (meta.get("may_contain") or []):
                    if g == "gluten" and not any(c["conflict_group"] == "gluten" for c in conflicts):
                        conflicts.append({"ingredient": "gluten", "standard_name": None, "profile_match": "gluten intolerance",
                                          "type": "intolerance", "severity": "caution",
                                          "reason": "This food may contain gluten, which may conflict with your gluten intolerance.",
                                          "conflict_group": "gluten"})
            if key == "lactose":
                for g in meta.get("declared_allergens") or []:
                    if g == "milk" and not any(c["conflict_group"] == "lactose" for c in conflicts):
                        conflicts.append({"ingredient": "dairy", "standard_name": None, "profile_match": "lactose intolerance",
                                          "type": "intolerance", "severity": "caution",
                                          "reason": "This food is commonly made with dairy, which may conflict with your lactose intolerance.",
                                          "conflict_group": "lactose"})

        # ---------- 4. dietary preferences ----------
        conflicts += self._preference_conflicts(prefs, recognized, nutrition, notes)

        # ---------- 5. declared health considerations ----------
        conflicts += self._condition_conflicts(conditions, recognized, nutrition, meta, notes)

        conflicts = self._dedupe(conflicts)
        level = HIGH if any(c["severity"] == "high" for c in conflicts) else (CAUTION if conflicts else LOW)

        # ---------- warnings / uncertainty (never hidden) ----------
        if not ingredients:
            warnings.append("No ingredient information is available, so SafeBite cannot rule out allergens or other conflicts.")
        if unrecognized:
            shown = ", ".join(unrecognized[:5]) + ("…" if len(unrecognized) > 5 else "")
            warnings.append(f"{len(unrecognized)} ingredient(s) weren't recognized and couldn't be checked: {shown}.")
        if data_certainty == "estimated":
            warnings.append("Ingredients are estimated from a typical recipe. Actual recipes vary, so ask how it was prepared.")
        if ocr_confidence is not None and ocr_confidence < 0.6:
            warnings.append("The label was read with low confidence. Double-check the ingredients against the pack.")
        mc = [i.raw for i in precautionary if i.name]
        if mc:
            warnings.append("The label carries a precautionary statement: may contain " + ", ".join(mc) + ".")
        if not any(k in nutrition for k in ("calories", "sugar", "sodium")):
            warnings.append("Nutrition information is incomplete.")
        warnings.append("Ingredient information may be incomplete. Always check the physical label if you have a severe allergy.")

        explanation = self._explain(level, conflicts)
        confidence = self._confidence(data_certainty, ocr_confidence, len(recognized), len(ingredients))

        return RiskResult(
            risk_level=level, detected_conflicts=conflicts, explanation=explanation, confidence=confidence,
            warnings=warnings, notes=notes, ingredients=[i.name for i in recognized],
            ingredient_details=[i.to_dict() for i in ingredients], unrecognized=unrecognized,
            data_certainty=data_certainty,
        )

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _c(ing, disp, match, typ, sev, reason, group) -> dict:
        return {"ingredient": disp, "standard_name": ing.name, "profile_match": match, "type": typ,
                "severity": sev, "reason": reason, "conflict_group": group}

    @staticmethod
    def _maybe_gluten_reason(ing) -> str:
        if ing.name and "hing" in ing.name.lower():
            return "Compounded hing (asafoetida) is often blended with wheat flour. Check the pack or use a gluten-free hing."
        return f"{ing.name} can carry gluten through cross-contact unless labelled gluten-free."

    def _custom_names(self, term: str) -> set[str]:
        m = self.d.lookup(term)
        names = {term.strip().lower()}
        if m:
            names.add(m.standard_name.lower())
        return names

    @staticmethod
    def _name_hit(ing: NormalizedIngredient, names: set[str], label: str) -> bool:
        if not ing.name:
            return False
        n = ing.name.lower()
        raw = (ing.raw or "").lower()
        t = label.strip().lower()
        return n in names or (len(t) >= 3 and (t in raw.split() or t in n.split() or t == (ing.matched_alias or "")))

    def _matches_allergy(self, ing, group, custom_names, label) -> bool:
        if group:
            return group in ing.allergen_groups
        return self._name_hit(ing, custom_names, label)

    def _preference_conflicts(self, prefs, ings, nutrition, notes) -> list[dict]:
        out = []

        def tagged(*tags):
            return [i for i in ings if any(t in i.dietary_tags for t in tags)]

        def add(i, pref, reason, group):
            out.append(self._c(i, _pretty(i.raw, i.name), pref, "preference", "caution", reason, group))

        for p in prefs:
            if p == "vegetarian":
                for i in tagged("non_veg", "meat", "fish", "seafood"):
                    add(i, "vegetarian diet", f"{_pretty(i.raw, i.name)} is not vegetarian and conflicts with your vegetarian preference.", "non_veg")
                for i in tagged("egg"):
                    add(i, "vegetarian diet", f"{_pretty(i.raw, i.name)} contains egg. Many vegetarian diets exclude egg.", "egg")
            elif p == "vegan":
                for i in tagged("animal_derived"):
                    add(i, "vegan diet", f"{_pretty(i.raw, i.name)} is animal-derived and conflicts with your vegan preference.",
                        "milk" if "dairy" in i.dietary_tags else ("egg" if "egg" in i.dietary_tags else "non_veg"))
                for i in tagged("possible_animal"):
                    out.append(self._c(i, _pretty(i.raw, i.name), "vegan diet", "possible", "caution",
                                       f"{_pretty(i.raw, i.name)} can be plant- or animal-derived; the label doesn't say which.", "non_veg"))
            elif p == "jain":
                for i in tagged("non_veg", "egg", "honey"):
                    add(i, "Jain diet", f"{_pretty(i.raw, i.name)} is not part of a Jain diet.", "non_veg")
                for i in tagged("root_vegetable", "onion_garlic"):
                    add(i, "Jain diet", f"{_pretty(i.raw, i.name)} is a root vegetable or onion/garlic, which a Jain diet avoids.", "jain")
            elif p in ("gluten free", "glutenfree"):
                for i in tagged("gluten"):
                    add(i, "gluten-free diet", f"{_pretty(i.raw, i.name)} contains gluten, which conflicts with your gluten-free preference.", "gluten")
                for i in tagged("may_contain_gluten"):
                    out.append(self._c(i, _pretty(i.raw, i.name), "gluten-free diet", "possible", "caution",
                                       self._maybe_gluten_reason(i), "gluten"))
            elif p in ("dairy free", "dairyfree"):
                for i in tagged("dairy"):
                    add(i, "dairy-free diet", f"{_pretty(i.raw, i.name)} is a dairy ingredient, which conflicts with your dairy-free preference.", "milk")
            elif p == "low sodium":
                na = nutrition.get("sodium")
                if na is not None and na >= SODIUM_HIGH_MG:
                    out.append({"ingredient": "sodium", "standard_name": None, "profile_match": "low-sodium diet", "type": "preference",
                                "severity": "caution", "reason": f"About {round(na)} mg sodium per serving is high for a low-sodium preference.",
                                "conflict_group": "high_sodium"})
                elif na is None:
                    salty = [i.name for i in tagged("high_sodium")]
                    if salty:
                        notes.append("Sodium content isn't known; salty ingredients listed: " + ", ".join(salty) + ".")
            elif p == "low sugar":
                sg = nutrition.get("sugar")
                hidden = tagged("hidden_sugar")
                if sg is not None and sg >= SUGAR_HIGH_G:
                    out.append({"ingredient": "sugar", "standard_name": None, "profile_match": "low-sugar diet", "type": "preference",
                                "severity": "caution", "reason": f"About {sg:g} g sugar per serving is high for a low-sugar preference.",
                                "conflict_group": "high_sugar"})
                if hidden:
                    names = ", ".join(_pretty(i.raw, i.name) for i in hidden)
                    out.append({"ingredient": names, "standard_name": None, "profile_match": "low-sugar diet", "type": "preference",
                                "severity": "caution", "reason": f"{names} {'are' if len(hidden) > 1 else 'is a'} hidden form{'s' if len(hidden) > 1 else ''} of sugar.",
                                "conflict_group": "high_sugar"})
            elif p == "high protein":
                pr = nutrition.get("protein")
                if pr is not None:
                    notes.append(f"Provides about {pr:g} g protein per serving" + (" — a good fit for your high-protein preference." if pr >= 10 else "."))
        return out

    def _condition_conflicts(self, conditions, ings, nutrition, meta, notes) -> list[dict]:
        out = []
        na, sg, k = nutrition.get("sodium"), nutrition.get("sugar"), nutrition.get("potassium")
        hidden = [i for i in ings if "hidden_sugar" in i.dietary_tags]
        refined = [i for i in ings if "refined_flour" in i.dietary_tags]
        ratings = meta.get("condition_ratings") or {}

        def c(cond, reason, group):
            out.append({"ingredient": "", "standard_name": None, "profile_match": CONDITIONS[cond], "type": "condition",
                        "severity": "caution", "reason": reason, "conflict_group": group})

        for cond in conditions:
            cond = cond.replace(" ", "")
            if cond not in CONDITIONS:
                continue
            flagged = False
            if cond in ("diabetes", "pcos"):
                if sg is not None and sg >= SUGAR_HIGH_G:
                    c(cond, f"About {sg:g} g sugar per serving. This may not fit the sugar limits commonly advised for {CONDITIONS[cond]}.", "high_sugar"); flagged = True
                if hidden:
                    c(cond, "Contains hidden sugars (" + ", ".join(i.name for i in hidden) + ") that can raise the effective sugar content.", "high_sugar"); flagged = True
                if refined:
                    c(cond, "Made with refined flour (" + ", ".join(i.name for i in refined) + "), which is digested quickly.", "refined_flour"); flagged = True
            if cond in ("hypertension", "ckd"):
                if na is not None and na >= SODIUM_HIGH_MG:
                    c(cond, f"About {round(na)} mg sodium per serving is high for {CONDITIONS[cond]}.", "high_sodium"); flagged = True
            if cond == "ckd" and k is not None and k >= POTASSIUM_HIGH_MG:
                c(cond, f"About {round(k)} mg potassium per serving. Potassium is often limited for {CONDITIONS[cond]}.", "high_potassium"); flagged = True
            r = (ratings.get(cond) or "").lower()
            if r == "high" and not flagged:
                c(cond, f"This food is rated high-concern for {CONDITIONS[cond]} in SafeBite's reference dataset.",
                  {"diabetes": "high_sugar", "pcos": "high_sugar", "hypertension": "high_sodium", "ckd": "high_potassium"}[cond])
            elif r == "medium":
                notes.append(f"Rated moderate for {CONDITIONS[cond]} in the reference dataset; portion size matters.")
        if out:
            notes.append("Health considerations are pattern-based guidance, not medical advice. Follow your doctor's plan.")
        return out

    @staticmethod
    def _dedupe(conflicts: list[dict]) -> list[dict]:
        seen, out = set(), []
        # high first so explanations lead with the most important issue
        for c in sorted(conflicts, key=lambda c: 0 if c["severity"] == "high" else 1):
            k = (c["profile_match"], c.get("standard_name") or c["ingredient"].lower(), c["type"] if c["type"] == "condition" else c["severity"])
            if c["type"] == "condition":
                k = k + (c["reason"],)
            if k in seen:
                continue
            seen.add(k)
            out.append(c)
        return out

    @staticmethod
    def _explain(level: str, conflicts: list[dict]) -> str:
        if level == LOW:
            return LOW_MESSAGE
        seen, parts = set(), []
        for c in conflicts:
            if c["reason"] not in seen:
                seen.add(c["reason"])
                parts.append(c["reason"])
            if len(parts) == 3:
                break
        return " ".join(parts)

    @staticmethod
    def _confidence(certainty, ocr, n_rec, n_total) -> float:
        base = {"known": 0.95, "estimated": 0.7, "unknown": 0.4}.get(certainty, 0.6)
        ratio = (n_rec / n_total) if n_total else 0.0
        conf = base * (0.6 + 0.4 * ratio)
        if ocr is not None:
            conf *= 0.6 + 0.4 * max(0.0, min(1.0, ocr))
        if n_total == 0:
            conf = min(conf, 0.3)
        return round(conf, 2)
