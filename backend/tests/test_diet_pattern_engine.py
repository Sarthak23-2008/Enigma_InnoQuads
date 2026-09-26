from datetime import datetime, timedelta, timezone

from app.engines.diet_pattern_engine import DietPatternEngine, classify

NOW = datetime(2026, 9, 26, 12, tzinfo=timezone.utc)


def mk(days_ago, sodium=800, fiber=4, protein=12, sugar=3, name="Dal", processed=False, fv=False, added=False, risk="LOW"):
    return {"consumed_at": NOW - timedelta(days=days_ago, hours=1), "food_name": name, "category": "Curry",
            "sodium": sodium, "fiber": fiber, "protein": protein, "sugar": sugar, "calories": 300, "quantity": 1,
            "is_processed": processed, "is_fruit_veg": fv, "added_sugar_likely": added, "risk_level": risk}


def test_insufficient_under_three_logs():
    r = DietPatternEngine().analyze([mk(0), mk(1)], window=15, now=NOW)
    assert r["status"] == "insufficient" and r["metrics"] == [] and r["alerts"] == []


def test_early_snapshot_has_no_alerts():
    logs = [mk(d, sodium=3000) for d in range(3)] * 2
    r = DietPatternEngine().analyze(logs, window=15, now=NOW)
    assert r["status"] == "early_snapshot" and r["alerts"] == []
    assert next(m for m in r["metrics"] if m["key"] == "sodium")["classification"] == "HIGH"


def test_15_day_high_sodium_alert():
    logs = [mk(d, sodium=1300) for d in range(15)] + [mk(d, sodium=1200, name=f"Snack{d%4}") for d in range(15)]
    r = DietPatternEngine().analyze(logs, window=15, now=NOW)
    assert r["status"] == "trend"
    sodium = next(m for m in r["metrics"] if m["key"] == "sodium")
    assert sodium["classification"] == "HIGH" and sodium["value"] == 2500
    assert "Your recent food logs show a repeated high-sodium pattern." in [a["message"] for a in r["alerts"]]


def test_30_day_window_excludes_older_logs():
    logs = [mk(d) for d in range(40)]
    r = DietPatternEngine().analyze(logs, window=30, now=NOW)
    assert r["log_count"] == 30 and r["logged_days"] == 30


def test_low_fiber_and_suggestions():
    logs = [mk(d, fiber=2) for d in range(15)] * 2
    r = DietPatternEngine().analyze(logs, window=15, now=NOW)
    fiber = next(m for m in r["metrics"] if m["key"] == "fiber")
    assert fiber["classification"] == "LOW"
    assert any(s["metric"] == "fiber" for s in r["suggestions"])


def test_goal_progress_only_when_supported():
    prev = [mk(d, sodium=3000) for d in range(15, 30)]
    cur = [mk(d, sodium=1500) for d in range(15)]
    r = DietPatternEngine().analyze(cur + prev, window=15, now=NOW, goals=["reduce_sodium"], previous_logs=cur + prev)
    gp = r["goal_progress"][0]
    assert gp["statement"] == "Your sodium intake trend has decreased compared with the previous period."
    assert gp["on_track"] is True
    assert r["metrics"][0]["key"] == "sodium"  # goal metric prioritised
    r2 = DietPatternEngine().analyze(cur, window=15, now=NOW, goals=["reduce_sodium"], previous_logs=cur)
    assert r2["goal_progress"][0]["on_track"] is None
    assert "Not enough data" in r2["goal_progress"][0]["statement"]


def test_daily_series_has_gaps_not_invented_values():
    logs = [mk(0), mk(0), mk(0), mk(5)]
    r = DietPatternEngine().analyze(logs, window=15, now=NOW)
    empty = [d for d in r["daily"] if d["logs"] == 0]
    assert empty and all(d["sodium"] is None for d in empty)


def test_health_insight_is_non_diagnostic_and_needs_30_days():
    logs = [mk(d, sugar=40, added=True) for d in range(30)]
    r15 = DietPatternEngine().analyze(logs, window=15, now=NOW)
    assert r15["health_insight"] is None
    r30 = DietPatternEngine().analyze(logs, window=30, now=NOW)
    hi = r30["health_insight"]
    assert hi and hi["message"].startswith("Your logged pattern is associated with")
    assert "diabetes" not in hi["message"].lower()


def test_attention_level_is_educational():
    logs = [mk(d, sodium=3000, fiber=1, risk="HIGH") for d in range(20)]
    r = DietPatternEngine().analyze(logs, window=30, now=NOW)
    assert r["attention"]["suggest_consult"] is True
    assert "professional" in r["attention"]["message"]


def test_classify_bounds():
    assert classify("sodium", 2100) == "HIGH" and classify("sodium", 1500) == "MODERATE" and classify("sodium", 900) == "LOW"
