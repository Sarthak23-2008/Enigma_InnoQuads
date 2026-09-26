# SafeBite

Team Name : InnoQuads

Team Members : Aayush Prajapati , Sarthak Khadapkar , Vedant Sakpal , Aryan Dhumal

**Know what's in your food. Know what it means for you.**

SafeBite is a personalized food-safety and dietary-pattern assistant built for **ENIGMA 5.0, HealthTech PS3: Personalized Hidden-Ingredient & Dietary-Risk Alert System**.
Scan a packaged-food label (or search a dish, type a home-cooked meal, or pick a restaurant dish). SafeBite reads the ingredients, resolves hidden names (arachis → peanut, casein → milk, maltodextrin → hidden sugar, compounded hing → possible wheat), and checks them against *your* allergies, intolerances, diet and optional health considerations. It returns **LOW / CAUTION / HIGH** with a plain-language reason. Foods you actually eat ("I Ate This") feed 15- and 30-day pattern trends with alerts, goals and "Try instead" suggestions.

> SafeBite gives dietary information, not medical advice. It never says a food is "100% safe" and never diagnoses.

## Two engines

| Engine | Purpose | File |
|---|---|---|
| 1. Food Safety / Ingredient Risk | Per-food check: allergy → HIGH (incl. listed traces), "may contain" / intolerance / diet / declared health consideration → CAUTION, else LOW with honest uncertainty warnings | `backend/app/engines/risk_engine.py` |
| 2. Diet Pattern | Rolling 15/30-day aggregation of logged foods: sugar, sodium, fiber, fruit & veg, processed share, protein, diversity; alerts, goal progress, suggestions, Pattern Attention Level | `backend/app/engines/diet_pattern_engine.py` |

Both are deterministic, explainable rules; no LLM decides safety.

## Quick start (local)

Prerequisites: Python 3.11+, Node 18+, and [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) (`sudo apt install tesseract-ocr`, `brew install tesseract`, or the Windows installer). Without Tesseract, the three bundled sample labels still work through the demo OCR fallback.

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # SQLite by default; nothing else required locally
uvicorn app.main:app --reload                          # http://localhost:8000  (API docs: /docs)

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                                            # http://localhost:5173  (proxies /api to :8000)
```

Tables, reference data and the demo account are created automatically on first start.

**Demo login:** click **Use the demo account** on the login page, or `demo@safebite.app` / `SafeBiteDemo1`.

## Demo flow (hackathon script)

1. Log in as the demo user (Aryan Demo: peanut allergy, lactose intolerance, vegetarian, goal *Reduce sodium*).
2. **Check Food → Scan Food Label → "ChocoCrunch biscuits"** sample label.
3. Review screen shows OCR output: Wheat flour, Milk solids, Sugar, Cocoa, Peanut traces, Soy lecithin (editable).
4. **Analyze Food** → **HIGH**: "Peanut traces were detected and match your peanut allergy profile." plus CAUTION "Milk solids may conflict with your lactose intolerance."
5. **Try instead**: Roasted Makhana, Roasted Chana, Sunflower Seed Butter, each re-screened against the profile.
6. **I Ate This** → toast "Added to your diet history."
7. **History** → entry appears (filters, search, detail with full analysis).
8. **Trends** → 15 / 30 days, Generalized / Detailed: "Your recent food logs show a repeated high-sodium pattern.", low fiber, goal progress "Your sodium intake trend has decreased compared with the previous period.", Pattern Attention Level, charts.
9. Tap a **Try instead** chip → opens a pre-filled search.

## Tests

```bash
cd backend && pytest -q        # 49 tests: normalizer, risk engine, diet engine, OCR parsing, auth, logging, trends, API
cd frontend && npm run build   # production build
```

## Project layout

```
backend/    FastAPI API, engines, OCR services, models, seed, tests, Dockerfile
frontend/   React + Vite + Tailwind SPA
database/   schema.sql (PostgreSQL reference) and seed notes
docs/       API.md, DEPLOYMENT.md, ARCHITECTURE.md
render.yaml Render blueprint (API + Postgres + report cron)
```

See `docs/ARCHITECTURE.md` for the file-by-file breakdown, `docs/API.md` for endpoints and `docs/DEPLOYMENT.md` for Vercel + Render/Supabase deployment.
