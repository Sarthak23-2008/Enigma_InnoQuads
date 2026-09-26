from __future__ import annotations

import re
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models import Food, User
from app.services.common import food_out

router = APIRouter(prefix="/foods", tags=["foods"])

# Small in-process cache of the (read-mostly) foods table; refreshed every 10 minutes.
_cache: dict = {"at": 0.0, "rows": []}
_lock = threading.Lock()
TTL = 600


def _rows(db: Session) -> list[dict]:
    with _lock:
        if time.monotonic() - _cache["at"] > TTL or not _cache["rows"]:
            _cache["rows"] = [{**food_out(f), "_key": f.name.lower(), "_cat": (f.category or "").lower()}
                              for f in db.query(Food).order_by(Food.name).all()]
            _cache["at"] = time.monotonic()
        return _cache["rows"]


def clear_food_cache():
    _cache["at"] = 0.0


def _score(row: dict, q: str, words: list[str]) -> int:
    k = row["_key"]
    if k == q:
        return 100
    if k.startswith(q):
        return 80
    if re.search(r"\b" + re.escape(q), k):
        return 60
    if all(w in k for w in words):
        return 40
    if q in row["_cat"]:
        return 20
    return 0


@router.get("/search")
def search(q: str = Query("", max_length=80), category: str | None = Query(None, max_length=40),
           limit: int = Query(20, ge=1, le=50), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = _rows(db)
    qn = re.sub(r"\s+", " ", q.strip().lower())
    if category:
        rows = [r for r in rows if r["_cat"] == category.lower()]
    if not qn:
        picks = rows[:limit]
    else:
        words = qn.split()
        scored = [(s, r) for r in rows if (s := _score(r, qn, words))]
        # tolerate simple plurals / typos: try singular form
        if not scored and qn.endswith("s"):
            scored = [(s, r) for r in rows if (s := _score(r, qn[:-1], [w.rstrip("s") for w in words]))]
        scored.sort(key=lambda t: (-t[0], t[1]["_key"]))
        picks = [r for _, r in scored[:limit]]
    return {"query": q, "results": [{k: v for k, v in r.items() if not k.startswith("_")} for r in picks]}


@router.get("/categories")
def categories(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return sorted({r["category"] for r in _rows(db) if r["category"]})


@router.get("/{food_id}")
def get_food(food_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    f = db.get(Food, food_id)
    if not f:
        raise HTTPException(404, "Food not found.")
    return food_out(f, full=True)
