from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import get_settings
from app.database.session import get_db
from app.models import DietaryProfile, NotificationSetting, User, UserSetting
from app.schemas import LoginIn, SignupIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_EMAIL = "demo@safebite.app"
_ATTEMPTS: dict[str, deque] = defaultdict(deque)
MAX_ATTEMPTS, WINDOW_S = 8, 300


def _throttle(key: str):
    now = time.monotonic()
    q = _ATTEMPTS[key]
    while q and now - q[0] > WINDOW_S:
        q.popleft()
    if len(q) >= MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many login attempts. Please wait a few minutes and try again.")
    q.append(now)


def _token(user: User) -> dict:
    return {"access_token": create_access_token(user.user_id, user.token_version), "token_type": "bearer",
            "user": UserOut.model_validate(user)}


@router.post("/register", response_model=TokenOut, status_code=201)
@router.post("/signup", response_model=TokenOut, status_code=201, include_in_schema=False)
def register(body: SignupIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists. Try logging in.")
    user = User(name=body.name, email=email, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    db.add_all([DietaryProfile(user_id=user.user_id, allergies=[], intolerances=[], dietary_preferences=[],
                               health_conditions=[], goals=[]),
                UserSetting(user_id=user.user_id), NotificationSetting(user_id=user.user_id, last_sent={})])
    db.commit()
    db.refresh(user)
    return _token(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    email = body.email.lower()
    _throttle(f"{email}|{request.client.host if request.client else ''}")
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect.")
    _ATTEMPTS.pop(f"{email}|{request.client.host if request.client else ''}", None)
    return _token(user)


@router.post("/demo", response_model=TokenOut)
def demo_login(db: Session = Depends(get_db)):
    """One-click login to the clearly-labelled demo account (only when DEMO_MODE is on)."""
    if not get_settings().DEMO_MODE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Demo mode is disabled.")
    from app.database.seed import demo_is_stale, seed_demo_user
    if demo_is_stale(db):  # seeded dates are relative; keep the 30-day window populated
        seed_demo_user(db, reset=True)
    user = db.query(User).filter_by(email=DEMO_EMAIL).first()
    if not user:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Demo data hasn't been seeded yet.")
    return _token(user)


@router.post("/logout", status_code=204)
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Revoke all tokens for this user (server-side logout). The demo account is shared, so only the
    # client discards its token there to avoid logging other demo viewers out.
    if not user.is_demo:
        user.token_version += 1
        db.commit()
    return None


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
