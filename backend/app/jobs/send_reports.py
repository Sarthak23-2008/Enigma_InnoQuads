"""Cron entry point for scheduled reports.  Usage:  python -m app.jobs.send_reports
Schedule daily (e.g. Render Cron Job: `python -m app.jobs.send_reports`)."""
from app.database.init_db import init_db
from app.database.session import SessionLocal
from app.services.reports import run_due_reports

if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        print(f"Reports sent: {run_due_reports(db)}")
