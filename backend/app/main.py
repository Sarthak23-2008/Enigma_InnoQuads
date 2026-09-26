"""SafeBite API — FastAPI application entry point.  Run:  uvicorn app.main:app --reload"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api import account, analysis, auth, foods, goals, insights, logs, misc, ocr, profile, settings as settings_api, symptoms
from app.config import get_settings
from app.utils.logging_setup import setup_logging

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
log = logging.getLogger("safebite.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database.seed import run
    try:
        run(with_demo=settings.DEMO_MODE)  # create tables + seed reference data (idempotent)
    except Exception:
        log.exception("startup seeding failed")
    log.info("SafeBite API started", extra={"env": settings.APP_ENV, "ocr": settings.OCR_PROVIDER})
    yield


app = FastAPI(title="SafeBite API", version="1.0.0", lifespan=lifespan,
              description="Personalized food safety & dietary pattern tracker. Not medical advice.",
              docs_url=None if settings.is_production else "/docs", redoc_url=None)

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                   allow_headers=["Authorization", "Content-Type", "X-Timezone", "X-Request-ID"],
                   expose_headers=["X-Request-ID", "Content-Disposition"], max_age=600)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    log.info("request", extra={"rid": rid, "method": request.method, "path": request.url.path,
                               "status": response.status_code, "ms": round((time.perf_counter() - start) * 1000, 1)})
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(x) for x in e.get("loc", []) if x != "body"),
               "message": e.get("msg", "").replace("Value error, ", "")} for e in exc.errors()]
    first = errors[0] if errors else {"field": "", "message": "Invalid request."}
    msg, field = first["message"], first["field"].split(".")[-1].replace("_", " ")
    custom = msg[:1].isupper() and msg.endswith(".")  # our own validator messages are already user-friendly
    detail = msg if custom or not field else f"{field.capitalize()}: {msg}"
    return JSONResponse(status_code=422, content={"detail": detail, "errors": errors})


@app.exception_handler(HTTPException)
async def http_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=getattr(exc, "headers", None))


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled error", extra={"path": request.url.path})
    detail = "Something went wrong on our side. Please try again." if settings.is_production else f"{type(exc).__name__}: {exc}"
    return JSONResponse(status_code=500, content={"detail": detail})


for r in (auth.router, profile.router, ocr.router, analysis.router, foods.router, logs.router, insights.router,
          goals.router, settings_api.router, account.router, symptoms.router, misc.router):
    app.include_router(r, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    return {"name": "SafeBite API", "docs": None if settings.is_production else "/docs", "health": "/api/health"}
