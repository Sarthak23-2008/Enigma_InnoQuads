from __future__ import annotations

import hashlib
import logging
import os
import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.auth.deps import get_current_user
from app.config import get_settings
from app.models import User
from app.services.analysis import preview_ingredients
from app.services.ocr.base import OCRError
from app.services.ocr.factory import run_ocr
from app.services.ocr.label_parser import parse_label
from app.utils.uploads import UploadError, validate_image

router = APIRouter(prefix="/ocr", tags=["ocr"])
log = logging.getLogger("safebite.ocr")

UNREADABLE = "We couldn't read this label clearly. Try another photo or enter the ingredients manually."
INCOMPLETE = "Some information may not have been detected. Please review the extracted ingredients."


def confidence_level(c: float) -> str:
    return "high" if c >= 0.8 else ("medium" if c >= 0.6 else "low")


def guess_name(text: str) -> str:
    for line in text.splitlines():
        l = line.strip()
        if not l or re.match(r"(?i)^(ingredients?|nutrition|allergen|contains|net|mrp|best|mfd|energy)", l):
            if re.match(r"(?i)^ingredients?", l):
                break
            continue
        l = re.sub(r"(?i)^sample\s+label\s*[-:–]\s*", "", l).strip(" -:")
        if 2 < len(l) <= 60 and sum(ch.isalpha() for ch in l) >= 3:
            return l.title()
        break
    return "Scanned food"


@router.post("/extract")
async def extract(image: UploadFile = File(...), lang: str = "eng", user: User = Depends(get_current_user)):
    s = get_settings()
    data = await image.read(s.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    try:
        kind = validate_image(data, s.MAX_UPLOAD_MB)
    except UploadError as e:
        raise HTTPException(422, str(e))
    lang = lang if lang in ("eng", "hin", "eng+hin") else "eng"
    digest = hashlib.sha256(data).hexdigest()
    if s.STORE_UPLOADS:  # off by default; never served publicly
        os.makedirs(s.UPLOAD_DIR, exist_ok=True)
        with open(os.path.join(s.UPLOAD_DIR, f"{digest}.{kind}"), "wb") as f:
            f.write(data)
    try:
        ocr = await run_in_threadpool(run_ocr, data, lang)
    except OCRError as e:
        log.info("ocr failed", extra={"user_id": user.user_id, "reason": str(e)})
        raise HTTPException(422, UNREADABLE)
    parsed = parse_label(ocr.text)
    if not parsed["ingredients"] and not any(k in parsed["nutrition"] for k in ("calories", "sodium", "sugar")):
        raise HTTPException(422, UNREADABLE)
    warnings = list(ocr.warnings) + parsed["warnings"]
    level = confidence_level(ocr.confidence)
    if level == "low":
        warnings.insert(0, "Please review the extracted ingredients carefully.")
    incomplete = bool(parsed["warnings"]) or level != "high"
    nutrition = {k: v for k, v in parsed["nutrition"].items()
                 if k in ("calories", "protein", "carbohydrates", "fat", "sugar", "fiber", "sodium", "potassium",
                          "basis", "serving_size")}
    return {
        "scan_token": digest, "provider": ocr.provider, "confidence": round(ocr.confidence, 2),
        "confidence_level": level, "food_name": guess_name(parsed["clean_text"]),
        "raw_text": parsed["clean_text"], "ingredients": parsed["ingredients"],
        "ingredient_preview": preview_ingredients(parsed["ingredients"]),
        "allergen_statements": parsed["allergen_statements"], "nutrition": nutrition,
        "warnings": warnings, "incomplete": incomplete, "incomplete_message": INCOMPLETE if incomplete else None,
    }
