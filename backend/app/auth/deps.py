from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.database.session import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)
UNAUTH = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to continue.",
                       headers={"WWW-Authenticate": "Bearer"})


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not creds or creds.scheme.lower() != "bearer":
        raise UNAUTH
    try:
        payload = decode_token(creds.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise UNAUTH
    user = db.get(User, user_id)
    if not user or payload.get("tv") != user.token_version:
        raise UNAUTH
    return user


def get_tz(x_timezone: str | None = Header(default=None)):
    """Client sends its IANA timezone (e.g. Asia/Kolkata) so 'today' and daily trends use local days."""
    from datetime import timezone
    if x_timezone:
        name = TZ_ALIASES.get(x_timezone, x_timezone)
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return timezone.utc


# Browsers still report some legacy IANA names that minimal tz databases may lack.
TZ_ALIASES = {"Asia/Calcutta": "Asia/Kolkata", "Asia/Katmandu": "Asia/Kathmandu", "Asia/Saigon": "Asia/Ho_Chi_Minh",
              "Asia/Rangoon": "Asia/Yangon", "Europe/Kiev": "Europe/Kyiv", "America/Buenos_Aires": "America/Argentina/Buenos_Aires"}
