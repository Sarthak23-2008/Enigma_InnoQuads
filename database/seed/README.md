# Seed data

Seeding is done by code so the same data works on SQLite and PostgreSQL:

```bash
cd backend
python -m app.database.seed                    # idempotent: reference data + demo user if missing
python -m app.database.seed --reset-demo       # rebuild the demo user's 30 days of logs relative to today
python -m app.database.seed --refresh-reference  # reload ingredient mappings and foods from app/data
```

Sources (in `backend/app/data/`):

| File | What it seeds |
|---|---|
| `ingredient_mappings.json` (built by `build_mappings.py`) | 132 standard ingredients, 919 aliases (Indian names, INS codes, hidden sugars) → `ingredient_mapping` |
| `dietary_risk_dataset.csv` + `food_catalog.py` | 60 foods from the provided dataset (IFCT 2017 / Open Food Facts India / USDA FDC) → `foods` |
| `foods_extra.json` | 32 extra foods used as searchable items and alternatives → `foods` |
| `consultation_providers.json` | 5 clearly-marked sample listings → `consultation_providers` |
| `seed.py` | Demo user **Aryan Demo** (`demo@safebite.app` / `SafeBiteDemo1`): peanut allergy, lactose intolerance, vegetarian, goal Reduce Sodium, ~215 demo logs over 30 days, symptom check-ins |

All demo rows are flagged (`users.is_demo`, `food_logs.is_demo`). Demo login re-seeds automatically if the newest demo log is older than 36 hours, so the 15/30-day windows are always populated.
