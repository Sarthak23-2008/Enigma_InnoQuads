# Deploying SafeBite

Recommended free-tier setup: **Frontend on Vercel**, **backend on Render (Docker, includes Tesseract)**, **PostgreSQL on Render or Supabase**.

## 1. Push to GitHub
```bash
cd safebite
git init && git add . && git commit -m "SafeBite: ENIGMA 5.0 PS3"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

## 2. Database
Either let `render.yaml` create a Render Postgres (`safebite-db`), or create a Supabase project and copy its connection string (Project Settings → Database → Connection string, URI). Both `postgres://` and `postgresql://` URLs work; the app converts them. Tables are created automatically on first start (`database/schema/schema.sql` is the reference DDL).

## 3. Backend on Render
- **Blueprint:** New → Blueprint → select the repo → Render reads `render.yaml` (API, database and a daily report cron).
- **Or manually:** New → Web Service → repo → Root directory `backend`, Runtime **Docker**. Health check path `/api/health`.

Environment variables (`backend/.env.example` documents all of them):

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `DATABASE_URL` | Postgres URL |
| `JWT_SECRET` | long random string (`python -c "import secrets;print(secrets.token_urlsafe(48))"`); required in production |
| `FRONTEND_URL` | your Vercel URL, e.g. `https://safebite.vercel.app` (CORS) |
| `OCR_PROVIDER` | `tesseract` (bundled in the image) or `gemini` with `OCR_API_KEY` |
| `DEMO_MODE` | `true` for the hackathon demo account, `false` otherwise |
| `NOTIFICATION_PROVIDER` | `mock` (reports stored in-app) or `resend` + `RESEND_API_KEY` |

Check `https://<api>.onrender.com/api/health` → `"status":"ok","ocr_available":true`.
Free Render instances sleep; the first request after idle takes ~30–60 s.

## 4. Frontend on Vercel
New Project → import repo → **Root directory `frontend`**, framework **Vite** (build `npm run build`, output `dist`).
Environment variable: `VITE_API_BASE_URL = https://<api>.onrender.com/api`.
`frontend/vercel.json` rewrites all routes to `index.html`, so deep links like `/trends` work (Netlify uses `public/_redirects`).
Then set `FRONTEND_URL` on the backend to the Vercel URL and redeploy the backend.

## 5. Scheduled reports
The `safebite-reports` cron in `render.yaml` runs `python -m app.jobs.send_reports` daily; it sends weekly / bi-weekly / monthly reports that are due. Any scheduler (GitHub Actions, cron) can run the same command.

## Other hosts
- **Railway / Fly.io:** deploy `backend/Dockerfile`, set the same variables (`PORT` is honoured).
- **Without Docker:** install Tesseract on the host, `pip install -r requirements.txt`, start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

## Production checklist
- `APP_ENV=production` (hides `/docs` and internal error details) and a strong `JWT_SECRET`
- `FRONTEND_URL` set to the exact frontend origin
- Postgres, not SQLite (Render's disk is ephemeral)
- `STORE_UPLOADS=false` unless you have persistent storage and a retention policy
- Logs are structured JSON on stdout with request IDs (`X-Request-ID`)
