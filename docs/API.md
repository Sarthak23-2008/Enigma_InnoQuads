# SafeBite API

Base URL: `/api` (local `http://localhost:8000/api`). Interactive docs at `/docs` outside production.
Auth: `Authorization: Bearer <JWT>` on every route except register/login/demo/health.
Send `X-Timezone: <IANA name>` (the frontend does this) so "today" and daily trends use the user's local days.
Errors are JSON: `{"detail": "Human readable message"}`; validation errors add `errors: [{field, message}]` (422).

## Auth
| Method | Path | Body / notes |
|---|---|---|
| POST | `/auth/register` (alias `/auth/signup`) | `{name, email, password, confirm_password}`: password ≥8 chars with a letter and a number. 201 → `{access_token, user}`. 409 if email exists |
| POST | `/auth/login` | `{email, password}` → `{access_token, user}`. 401 wrong credentials, 429 after repeated failures |
| POST | `/auth/demo` | Logs into the demo account (DEMO_MODE only) |
| POST | `/auth/logout` | Revokes all of the user's tokens (204) |
| GET | `/auth/me` | Current user |

## Profile, goals, settings
| Method | Path | Notes |
|---|---|---|
| GET | `/profile/options` | Allergy / intolerance / preference / health-consideration / goal options |
| GET, PUT | `/profile` | `{allergies[], intolerances[], dietary_preferences[], health_conditions[], goals[], complete_onboarding}` |
| GET, POST | `/goals` | POST `{goal_type, target?, active}` (reduce_sodium, reduce_sugar, increase_fiber, increase_protein, improve_diversity) |
| PUT, DELETE | `/goals/{id}` | |
| GET, PUT | `/settings` | `{notifications{weekly_reports, biweekly_reports, monthly_reports, email_enabled, push_enabled}, input_prefs{default_input_method, ocr_language, auto_log}, accessibility{text_size, high_contrast, voice_assistance}}` (partial updates allowed) |
| POST | `/settings/notifications/send-test?period=weekly` | Generates a report through the configured provider |
| GET | `/settings/notifications/outbox` | Last 10 generated reports |

## Food checks
| Method | Path | Notes |
|---|---|---|
| POST | `/ocr/extract` | multipart `image` (JPEG/PNG/WEBP ≤ MAX_UPLOAD_MB), `?lang=eng\|hin\|eng+hin`. → `{scan_token, confidence, confidence_level, food_name, raw_text, ingredients[], ingredient_preview[], allergen_statements{contains, may_contain}, nutrition{}, warnings[], incomplete}`. 422 "We couldn't read this label clearly…" |
| POST | `/analysis/analyze` | `{input_method: scan\|search\|manual\|eating_out, food_name, ingredients[], nutrition{}, allergen_statements{}, food_id? (search), dish_name? (eating_out), meal_type?, ocr_confidence?, ocr_scan_token?, raw_ocr_text?}` → result (below) |
| GET | `/analysis/{scan_id}` | Stored result (own results only, else 404) |
| GET | `/analysis/recent?limit=5` | Recent checks |
| POST | `/analysis/preview` | `{ingredients[]}` → how each line normalises |
| GET | `/foods/search?q=&category=&limit=` | Cached search of the foods table |
| GET | `/foods/{id}`, `/foods/categories` | |
| GET | `/eating-out/dishes` | Restaurant dishes with estimated ingredients and ranges |

Result shape: `{scan_id, food_name, input_method, risk_level: LOW|CAUTION|HIGH, explanation, detected_conflicts[{ingredient, standard_name, profile_match, type, severity, reason, conflict_group}], confidence, data_certainty: known|estimated|unknown, ingredients[], ingredient_details[], unrecognized[], nutrition{}, allergen_statements{}, warnings[], notes[], alternatives[{name, food_id, reason, risk_level}], estimate?, disclaimer, logged_log_id?}`

## Logs and history
| Method | Path | Notes |
|---|---|---|
| POST | `/logs` | "I Ate This": `{scan_id, meal_type: breakfast\|lunch\|snack\|dinner, quantity (servings, 0–10), consumed_at?}` → log + `message: "Added to your diet history."` |
| GET | `/logs`, `/history` | `page, page_size, q, meal, risk, method, date_from, date_to` → `{items, total, page, pages}` |
| GET | `/logs/{id}`, `/history/{id}` | Log + original analysis + symptom check-in + repeated-symptom association |
| PUT | `/logs/{id}` | `{meal_type?, quantity?, consumed_at?}` (nutrition rescaled with quantity) |
| DELETE | `/logs/{id}` | |
| GET | `/logs/export?format=csv\|json` | Download |
| POST | `/logs/clear` | `{confirm_text: "CLEAR"}` |

## Insights
| Method | Path | Notes |
|---|---|---|
| GET | `/insights/15-day`, `/insights/30-day` | Diet Pattern Engine output (stored to `diet_insights`) |
| GET | `/trends?window=15\|30` | Same payload: `{status: insufficient\|early_snapshot\|trend, summary, metrics[], alerts[], suggestions[], goal_progress[], daily[], category_breakdown[], health_insight?, attention{score, level, suggest_consult}}` |
| GET | `/dashboard` | Greeting, today's meals, recent check, 15-day snapshot, pending symptom prompts |
| GET | `/symptoms/pending` | Unpackaged foods eaten 48–96 h ago without a check-in |
| POST | `/symptoms` | `{food_log_id, severity: none\|mild\|moderate\|severe, symptom?, notes?}` |
| GET | `/symptoms` | Check-in history |
| GET | `/consult/providers`, `/consult/attention` | Sample directory; Pattern Attention Level |

## Account and misc
| Method | Path | Notes |
|---|---|---|
| PUT | `/account` | `{name?, email?, current_password?}` (email change needs password) |
| GET | `/account/export` | Everything stored about the user (JSON) |
| POST | `/account/delete` | `{password, confirm_text: "DELETE"}` (demo account protected) |
| POST | `/household/analyze` | `{text}`: future-scope household label check (separate dictionary) |
| POST | `/demo/reset` | Demo account only |
| GET | `/health` | DB + OCR status |
