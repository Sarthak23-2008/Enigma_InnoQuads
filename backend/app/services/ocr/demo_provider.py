"""Demo OCR fallback: recognises the bundled sample label images by content hash, so the
hackathon demo works even on hosts without Tesseract. Clearly separated from production OCR."""
from __future__ import annotations

import hashlib
import json
import os

from app.services.ocr.base import OCRError, OCRProvider, OCRResult

SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "sample_labels.json")


class DemoOCR(OCRProvider):
    name = "demo"

    def __init__(self):
        try:
            with open(SAMPLES, encoding="utf-8") as f:
                self.samples = json.load(f)
        except FileNotFoundError:
            self.samples = {}

    def extract_text(self, image_bytes: bytes, lang: str = "eng") -> OCRResult:
        h = hashlib.sha256(image_bytes).hexdigest()
        s = self.samples.get(h)
        if not s:
            raise OCRError("Demo OCR only recognises the bundled sample labels. Enter the ingredients manually or enable Tesseract.")
        return OCRResult(text=s["text"], confidence=0.9, provider="demo",
                         warnings=["Demo OCR: text comes from the bundled sample label."])
