"""ENGINE 2 — Diet Pattern Engine.

Aggregates logged foods ("I Ate This") over a rolling 15- or 30-day window and reports
dietary-pattern observations. It never diagnoses or predicts disease.

Data sufficiency (never fabricate trends):
  < 3 logs                                 -> "insufficient"   (no metrics)
  logged days < half the window            -> "early_snapshot" (metrics shown, no pattern alerts)
  otherwise                                -> "trend"
Values are averages per *logged* day, because SafeBite only sees what the user logs.
"""
from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# (low_upper, high_lower). value < low_upper -> LOW ; value > high_lower -> HIGH ; else MODERATE
METRICS = {
    "added_sugar": {"label": "Added Sugar", "unit": "g/day", "bounds": (15, 30), "bad": "HIGH"},
    "sodium": {"label": "Sodium", "unit": "mg/day", "bounds": (1200, 2000), "bad": "HIGH"},
    "fiber": {"label": "Fiber", "unit": "g/day", "bounds": (15, 25), "bad": "LOW"},
    "fruit_veg": {"label": "Fruit & Vegetables", "unit": "servings/day", "bounds": (2, 4.5), "bad": "LOW"},
    "processed": {"label": "Processed Foods", "unit": "% of logs", "bounds": (20, 40), "bad": "HIGH"},
    "protein": {"label": "Protein", "unit": "g/day", "bounds": (35, 60), "bad": "LOW"},
    "diversity": {"label": "Food Diversity", "unit": "distinct foods", "bounds": (6, 12), "bad": "LOW"},
}
DAILY_THRESHOLDS = {"sodium": ("gt", 2000), "added_sugar": ("gt", 30), "fiber": ("lt", 15), "protein": ("lt", 35)}
GOAL_METRIC = {"reduce_sodium": "sodium", "reduce_sugar": "added_sugar", "increase_fiber": "fiber",
               "increase_protein": "protein", "improve_diversity": "diversity"}
GOAL_WANTS = {"reduce_sodium": "down", "reduce_sugar": "down", "increase_fiber": "up",
              "increase_protein": "up", "improve_diversity": "up"}
ALERTS = {
    "sodium": ("Your recent food logs show a repeated high-sodium pattern.",
               "Consider reducing frequently consumed high-sodium foods and including more minimally processed foods."),
    "added_sugar": ("Your recent food logs show a repeated high added-sugar pattern.",
                    "Consider swapping some sweetened drinks, sweets or packaged snacks for whole fruit or unsweetened options."),
    "fiber": ("Your recent food logs show consistently low fiber intake.",
              "Consider adding whole grains, legumes, fruits or vegetables to more meals."),
    "processed": ("Processed foods make up a large share of your recent logs.",
                  "Consider choosing home-cooked or minimally processed options more often."),
    "fruit_veg": ("Fruits and vegetables appear in few of your recent logs.",
                  "Consider adding a fruit or vegetable to more of your meals."),
    "protein": ("Your recent logs suggest protein intake is on the lower side.",
                "Consider including dal, legumes, paneer, curd or other protein sources you eat."),
    "diversity": ("Your recent logs show limited food variety.",
                  "Consider rotating different grains, legumes and vegetables through the week."),
}
SUGGESTION_KEY = {"fiber": "fiber_low", "protein": "protein_low", "fruit_veg": "fruit_veg_low",
                  "sodium": "sodium_high", "added_sugar": "sugar_high", "processed": "processed_high",
                  "diversity": "diversity_low"}
HEALTH_INSIGHT = {
    "added_sugar": "Your logged pattern is associated with dietary patterns that are commonly linked to blood-sugar concerns.",
    "sodium": "Your logged pattern is associated with dietary patterns that are commonly linked to blood-pressure concerns.",
}


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def classify(metric: str, value: float) -> str:
    lo, hi = METRICS[metric]["bounds"]
    if value < lo:
        return "LOW"
    if value > hi:
        return "HIGH"
    return "MODERATE"


def food_flags(ingredient_details: list[dict], category: str | None, is_packaged: bool | None,
               input_method: str) -> dict:
    """Derive pattern flags stored on each food log."""
    tags = [t for i in ingredient_details or [] for t in (i.get("dietary_tags") or [])]
    cat = (category or "").lower()
    processed_markers = sum(1 for t in tags if t in ("processed_marker", "palm_oil", "trans_fat_risk"))
    is_processed = bool(processed_markers >= 1 or cat in ("packaged meal", "fast food", "bakery", "street food")
                        or (is_packaged and cat in ("snack", "sweet", "beverage", "condiment")))
    names = [i.get("name") for i in ingredient_details or [] if i.get("name")]
    fv_first = bool(ingredient_details) and "fruit_veg" in (ingredient_details[0].get("dietary_tags") or [])
    is_fruit_veg = cat in ("fruit", "vegetable", "salad") or (fv_first and len(names) <= 4)
    added_sugar = any(t in ("added_sugar", "hidden_sugar") for t in tags) or cat in ("sweet",) or \
        (cat == "beverage" and any(t == "added_sugar" for t in tags))
    return {"is_processed": is_processed, "is_fruit_veg": is_fruit_veg, "added_sugar_likely": added_sugar,
            "is_unpackaged": input_method in ("search", "manual", "eating_out") and not is_packaged}


class DietPatternEngine:
    def __init__(self, tz=timezone.utc):
        self.tz = tz
        self.suggestions = _load("nutrient_suggestions.json")

    # logs: list of dicts with consumed_at (aware datetime), food_name, category, nutrition keys & flags
    def analyze(self, logs: list[dict], *, window: int, now: datetime | None = None,
                goals: list[str] | None = None, previous_logs: list[dict] | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        today = now.astimezone(self.tz).date()
        start = today - timedelta(days=window - 1)
        cur = [l for l in logs if start <= self._d(l) <= today]
        goals = [g for g in (goals or []) if g in GOAL_METRIC]

        base = {"window": window, "start_date": start.isoformat(), "end_date": today.isoformat(),
                "log_count": len(cur), "logged_days": len({self._d(l) for l in cur}), "goals": goals}
        if len(cur) < 3:
            return {**base, "status": "insufficient", "metrics": [], "alerts": [], "suggestions": [],
                    "daily": self._daily(cur, start, today), "category_breakdown": [], "goal_progress": [],
                    "summary": "Keep logging your meals. More data will help SafeBite identify meaningful dietary patterns.",
                    "health_insight": None, "attention": self._attention(cur, [])}

        status = "trend" if base["logged_days"] >= math.ceil(window / 2) else "early_snapshot"
        values = self._values(cur)
        prev_values = None
        if previous_logs is not None:
            p_start = start - timedelta(days=window)
            prev = [l for l in previous_logs if p_start <= self._d(l) < start]
            if len(prev) >= 3 and len({self._d(l) for l in prev}) >= max(3, math.ceil(window / 4)):
                prev_values = self._values(prev)
        daily = self._daily(cur, start, today)

        metrics = []
        for key, cfg in METRICS.items():
            v = values[key]
            cls = classify(key, v)
            attention = cls == cfg["bad"]
            trend = None
            if prev_values is not None:
                pv = prev_values[key]
                change = ((v - pv) / pv * 100) if pv else (100.0 if v else 0.0)
                direction = "stable" if abs(change) < 10 else ("up" if change > 0 else "down")
                trend = {"direction": direction, "change_pct": round(change, 1), "previous_value": round(pv, 1)}
            metrics.append({
                "key": key, "label": cfg["label"], "value": round(v, 1), "unit": cfg["unit"],
                "classification": cls, "attention": attention, "trend": trend,
                "explanation": self._explain(key, v, cls, cfg),
                "top_contributors": self._contributors(cur, key) if attention and key in ("sodium", "added_sugar", "processed") else [],
                "days_over_threshold": self._days_over(daily, key),
            })
        goal_metrics = [GOAL_METRIC[g] for g in goals]
        metrics.sort(key=lambda m: (0 if m["key"] in goal_metrics else 1))

        alerts = []
        if status == "trend":
            for m in metrics:
                if not m["attention"]:
                    continue
                repeated = m["key"] not in DAILY_THRESHOLDS or m["days_over_threshold"] >= 3
                if repeated:
                    msg, action = ALERTS[m["key"]]
                    alerts.append({"metric": m["key"], "severity": "attention", "message": msg, "action": action,
                                   "contributors": m["top_contributors"]})

        suggestions = []
        for m in metrics:
            if m["attention"] and m["key"] in SUGGESTION_KEY:
                s = self.suggestions[SUGGESTION_KEY[m["key"]]]
                suggestions.append({"metric": m["key"], **s})

        return {
            **base, "status": status, "metrics": metrics, "alerts": alerts, "suggestions": suggestions,
            "daily": daily, "category_breakdown": self._categories(cur),
            "goal_progress": self._goal_progress(goals, metrics, prev_values is not None),
            "summary": self._summary(metrics, status),
            "health_insight": self._health_insight(cur, start, window, status, base["logged_days"]),
            "attention": self._attention(cur, metrics),
            "previous_period_available": prev_values is not None,
        }

    # ------------------------------------------------------------------ internals
    def _d(self, log) -> date:
        dt = log["consumed_at"]
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(self.tz).date()

    @staticmethod
    def _n(log, k):
        v = log.get(k)
        return float(v) if v is not None else 0.0

    def _values(self, logs) -> dict:
        days = max(1, len({self._d(l) for l in logs}))
        n = len(logs)
        return {
            "added_sugar": sum(self._n(l, "sugar") for l in logs if l.get("added_sugar_likely")) / days,
            "sodium": sum(self._n(l, "sodium") for l in logs) / days,
            "fiber": sum(self._n(l, "fiber") for l in logs) / days,
            "protein": sum(self._n(l, "protein") for l in logs) / days,
            "fruit_veg": sum((l.get("quantity") or 1) for l in logs if l.get("is_fruit_veg")) / days,
            "processed": 100.0 * sum(1 for l in logs if l.get("is_processed")) / n if n else 0.0,
            "diversity": float(len({(l.get("food_name") or "").strip().lower() for l in logs})),
        }

    def _daily(self, logs, start: date, end: date) -> list[dict]:
        by = defaultdict(list)
        for l in logs:
            by[self._d(l)].append(l)
        out, d = [], start
        while d <= end:
            ls = by.get(d, [])
            if ls:
                out.append({"date": d.isoformat(), "logs": len(ls),
                            "calories": round(sum(self._n(l, "calories") for l in ls)),
                            "sodium": round(sum(self._n(l, "sodium") for l in ls)),
                            "added_sugar": round(sum(self._n(l, "sugar") for l in ls if l.get("added_sugar_likely")), 1),
                            "fiber": round(sum(self._n(l, "fiber") for l in ls), 1),
                            "protein": round(sum(self._n(l, "protein") for l in ls), 1),
                            "fruit_veg": sum((l.get("quantity") or 1) for l in ls if l.get("is_fruit_veg")),
                            "processed": sum(1 for l in ls if l.get("is_processed"))})
            else:  # gaps stay empty; never invent values for days without logs
                out.append({"date": d.isoformat(), "logs": 0, "calories": None, "sodium": None, "added_sugar": None,
                            "fiber": None, "protein": None, "fruit_veg": None, "processed": None})
            d += timedelta(days=1)
        return out

    @staticmethod
    def _days_over(daily, key) -> int:
        if key not in DAILY_THRESHOLDS:
            return 0
        op, th = DAILY_THRESHOLDS[key]
        vals = [d[key] for d in daily if d["logs"]]
        return sum(1 for v in vals if (v > th if op == "gt" else v < th))

    def _contributors(self, logs, key) -> list[str]:
        c = Counter()
        for l in logs:
            name = l.get("food_name") or "Unknown"
            if key == "sodium":
                c[name] += self._n(l, "sodium")
            elif key == "added_sugar" and l.get("added_sugar_likely"):
                c[name] += self._n(l, "sugar")
            elif key == "processed" and l.get("is_processed"):
                c[name] += 1
        return [n for n, v in c.most_common(3) if v > 0]

    @staticmethod
    def _categories(logs) -> list[dict]:
        c = Counter((l.get("category") or "Other") for l in logs)
        return [{"category": k, "count": v} for k, v in c.most_common()]

    @staticmethod
    def _explain(key, v, cls, cfg) -> str:
        unit = cfg["unit"]
        val = f"{round(v)} {unit}" if v >= 10 else f"{round(v, 1)} {unit}"
        return {
            "added_sugar": f"About {val} of sugar from sweetened or packaged foods per logged day.",
            "sodium": f"About {val} of sodium per logged day.",
            "fiber": f"About {val} of fiber per logged day.",
            "fruit_veg": f"About {val} of fruits or vegetables per logged day.",
            "processed": f"{round(v)}% of logged foods were processed or packaged.",
            "protein": f"About {val} of protein per logged day.",
            "diversity": f"{int(v)} different foods logged in this period.",
        }[key]

    @staticmethod
    def _summary(metrics, status) -> str:
        high = [m["label"].lower() for m in metrics if m["attention"] and METRICS[m["key"]]["bad"] == "HIGH"]
        low = [m["label"].lower() for m in metrics if m["attention"] and METRICS[m["key"]]["bad"] == "LOW"]
        prefix = "Early snapshot: " if status == "early_snapshot" else ""

        def join(xs):
            return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
        if not high and not low:
            return prefix + "Your recent logs don't show any pattern that needs attention. Keep logging to keep this picture accurate."
        s = prefix + "Your recent logs show"
        if high:
            s += f" higher {join(high)} intake"
        if high and low:
            s += f", while {join(low)} intake appears lower."
        elif low:
            s += f" lower {join(low)} intake."
        else:
            s += "."
        return s

    @staticmethod
    def _goal_progress(goals, metrics, has_prev) -> list[dict]:
        by = {m["key"]: m for m in metrics}
        out = []
        for g in goals:
            m = by[GOAL_METRIC[g]]
            label = m["label"].lower()
            if not has_prev or not m["trend"]:
                statement, on_track = f"Not enough data from the previous period to compare your {label} yet.", None
            else:
                d = m["trend"]["direction"]
                noun = f"{label} intake" if g != "improve_diversity" else "food variety"
                if d == "stable":
                    statement, on_track = f"Your {noun} has stayed about the same compared with the previous period.", False
                else:
                    word = "decreased" if d == "down" else "increased"
                    statement = f"Your {noun} trend has {word} compared with the previous period."
                    on_track = d == GOAL_WANTS[g]
            out.append({"goal": g, "metric": m["key"], "label": m["label"], "statement": statement,
                        "on_track": on_track, "current": m["value"], "unit": m["unit"],
                        "classification": m["classification"], "trend": m["trend"]})
        return out

    def _health_insight(self, logs, start, window, status, logged_days):
        """Phase 3 — only after sufficient, sustained 30-day data. Educational, never a diagnosis."""
        if window < 30 or status != "trend" or logged_days < 20:
            return None
        mid = start + timedelta(days=window // 2)
        first = [l for l in logs if self._d(l) < mid]
        second = [l for l in logs if self._d(l) >= mid]
        if len(first) < 3 or len(second) < 3:
            return None
        v1, v2 = self._values(first), self._values(second)
        for key in ("added_sugar", "sodium"):
            if classify(key, v1[key]) == "HIGH" and classify(key, v2[key]) == "HIGH":
                return {"metric": key, "message": HEALTH_INSIGHT[key],
                        "action": "Consider discussing your dietary pattern with a qualified healthcare professional.",
                        "disclaimer": "This is a pattern-based educational insight, not a diagnosis."}
        return None

    @staticmethod
    def _attention(logs, metrics) -> dict:
        """Phase 3 'Pattern Attention Level' — an educational indicator, not a medical risk score."""
        high = sum(1 for l in logs if l.get("risk_level") == "HIGH")
        caution = sum(1 for l in logs if l.get("risk_level") == "CAUTION")
        check_part = min(40, 8 * high + 3 * caution)
        weights = {"sodium": 12, "added_sugar": 12, "fiber": 10, "processed": 10, "fruit_veg": 6, "protein": 5, "diversity": 5}
        pattern_part = min(60, sum(weights[m["key"]] for m in metrics if m["attention"]))
        score = check_part + pattern_part
        level = "Low" if score < 35 else ("Moderate" if score < 60 else "Elevated")
        return {"score": score, "level": level, "high_checks": high, "caution_checks": caution,
                "suggest_consult": score >= 60,
                "message": ("Your recent dietary pattern suggests that speaking with a professional may be useful."
                            if score >= 60 else None)}
