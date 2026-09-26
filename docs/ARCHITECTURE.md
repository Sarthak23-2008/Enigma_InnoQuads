# Architecture

```
React SPA (Vite) ──HTTPS/JSON + JWT──▶ FastAPI ──SQLAlchemy──▶ PostgreSQL (SQLite locally)
      │                                  │
      │ label photo (multipart)          ├─ OCR service (Tesseract | Gemini | demo) → label parser
      │                                  ├─ Engine 1: Ingredient Normalizer + Risk Engine
      │                                  ├─ Engine 2: Diet Pattern Engine
      │                                  └─ Alternatives, reports (mock | Resend), household (separate dictionary)
```

**Flow:** Check Food → (scan → OCR → *user reviews/edits* | search | manual | eating out) → `POST /analysis/analyze` (Engine 1, result stored) → `/result/:id` → **I Ate This** (`POST /logs`) → History → Trends (Engine 2 over the last 15/30 days).
Checking a food never logs it; only "I Ate This" (or the opt-in auto-log setting) does, so trends reflect what was actually eaten.

## Tech stack by layer
| Layer | Technology |
|---|---|
| Frontend | React 18, Vite 5, Tailwind CSS 3.4, React Router 6, Recharts, lucide-react, Web Speech API, self-hosted Archivo variable font |
| API | Python 3.12, FastAPI, Pydantic v2 (validation), Uvicorn |
| Data | SQLAlchemy 2 ORM; PostgreSQL in production, SQLite in development; JSON columns for ingredient/nutrition data |
| Auth | Own JWT (PyJWT, HS256) with server-side revocation (`token_version`), bcrypt hashing, login throttling |
| OCR | Tesseract 5 via pytesseract, Pillow/NumPy preprocessing (deskew, contrast, table-line removal); provider interface allows Gemini or demo |
| Engines | Pure-Python deterministic rules; ingredient dictionary stored in the `ingredient_mapping` table |
| Ops | Docker (with Tesseract), Render blueprint + cron, Vercel SPA rewrites, structured JSON logs with request IDs |
| Tests | pytest + FastAPI TestClient (49 tests); Playwright used for end-to-end verification |

## Backend (`backend/app`)
| Path | Responsibility |
|---|---|
| `main.py` | App factory: CORS, gzip, security headers, request-ID + JSON logging, error handlers, startup table creation and seeding |
| `config.py` | Environment settings (`.env`) |
| `auth/security.py`, `auth/deps.py` | Password hashing, JWT create/verify, `get_current_user`, timezone header |
| `api/auth.py` | register/signup, login, demo login, logout, me |
| `api/profile.py` | Dietary profile + options (syncs goals) |
| `api/ocr.py` | Secure upload → OCR → label parsing → review payload |
| `api/analysis.py` | Analyze (all four input methods), get result, recent, preview, eating-out dishes |
| `api/foods.py` | Cached food search and details |
| `api/logs.py` | I Ate This, history (filters, pagination), detail, edit, delete, CSV/JSON export, clear |
| `api/insights.py` | 15/30-day insights, trends, dashboard |
| `api/goals.py`, `api/settings.py`, `api/account.py`, `api/symptoms.py`, `api/misc.py` | Goals; settings + reports; account update/export/delete; symptom check-ins; consult, household, demo reset, health |
| `engines/ingredient_normalizer.py` | Cleaning, splitting, trace/negation detection, alias → standard name, OCR-typo and fuzzy matching |
| `engines/risk_engine.py` | Engine 1 rules, explanations, confidence and warnings |
| `engines/diet_pattern_engine.py` | Engine 2 metrics, sufficiency rules, alerts, goals, suggestions, health insight, attention level |
| `services/ocr/*` | `base.py` interface, `tesseract_provider.py`, `gemini_provider.py`, `demo_provider.py`, `preprocess.py`, `label_parser.py`, `factory.py` |
| `services/analysis.py` | Orchestrates a check for each input method and stores a `ScanResult` |
| `services/alternatives.py` | "Try instead", with every candidate re-screened by the Risk Engine |
| `services/reports.py`, `services/notifications/*` | Scheduled reports; mock and Resend providers |
| `services/household.py` | Future-scope household label check (separate dictionary) |
| `services/common.py` | Serializers and shared queries |
| `models/__init__.py` | 13 tables: users, dietary_profiles, foods, ingredient_mapping, scan_results, food_logs, diet_insights, symptom_logs, goals, notification_settings, user_settings, notification_outbox, consultation_providers |
| `schemas/__init__.py` | Request validation |
| `database/*` | Engine/session, `init_db`, `seed` (reference data + demo user) |
| `data/*` | Dataset CSV, ingredient mappings, extra foods, substitutions, suggestions, restaurant dishes, sample labels |
| `jobs/send_reports.py` | Cron entry point |
| `utils/uploads.py`, `utils/logging_setup.py` | Upload validation (magic bytes, size, Pillow verify); JSON logging |

## Frontend (`frontend/src`)
| Path | Responsibility |
|---|---|
| `App.jsx`, `main.jsx` | Routes (lazy-loaded pages), providers |
| `services/api.js` | Fetch client (JWT, timezone header, friendly errors) |
| `context/` | `AuthContext`, `PrefsContext` (accessibility and input preferences applied app-wide), `ToastContext` |
| `hooks/` | `useAsync` (loading/error/retry), `useSpeech` (speech synthesis and recognition) |
| `layouts/AppLayout.jsx` | Sticky desktop nav, mobile bottom nav, demo banner, page transitions |
| `pages/` | Landing, Login, Signup, Onboarding, Dashboard, CheckHub, Scan (upload → reading → review), Search, Manual, EatingOut, Result, History, HistoryDetail, Trends, Consult, Household, Privacy, NotFound, `settings/*` (profile, notifications, diet history, input preferences, accessibility, account) |
| `components/` | Navbar, MobileBottomNav, CheckFoodButton, RiskBadge, RiskResultCard, IngredientList, NutritionCard, OCRUploader, OCRReview, ConfidenceIndicator, AlertCard, GoalCard, AlternativeFoodCard, HistoryItem, FoodCard, MealPicker, RiskMeter, SymptomPrompt, VoiceButton, DemoBanner, Modal, ProfileEditor, SettingsSection, States (loading/error/empty), PageHeader, ProtectedRoute, Logo |
| `charts/` | TrendChart (daily bars with threshold lines and gaps for unlogged days), CategoryChart |
