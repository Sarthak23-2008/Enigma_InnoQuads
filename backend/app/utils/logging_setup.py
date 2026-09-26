"""Structured JSON logging (one JSON object per line) — easy to search on Render/Railway."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

_STD = set(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, r: logging.LogRecord) -> str:
        out = {"ts": datetime.fromtimestamp(r.created, timezone.utc).isoformat(), "level": r.levelname,
               "logger": r.name, "msg": r.getMessage()}
        out.update({k: v for k, v in r.__dict__.items() if k not in _STD and not k.startswith("_")})
        if r.exc_info:
            out["exc"] = self.formatException(r.exc_info)
        return json.dumps(out, default=str)


def setup_logging(level: str = "INFO") -> None:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [h]
    root.setLevel(level.upper())
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)
