from __future__ import annotations

import re
import shutil

from app.config import get_settings
from app.services.ocr.base import OCRError, OCRProvider, OCRResult
from app.services.ocr.preprocess import prepare


class TesseractOCR(OCRProvider):
    name = "tesseract"

    def __init__(self):
        import pytesseract
        self.pt = pytesseract
        cmd = get_settings().TESSERACT_CMD
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd

    def available(self) -> bool:
        return bool(get_settings().TESSERACT_CMD or shutil.which("tesseract"))

    def extract_text(self, image_bytes: bytes, lang: str = "eng") -> OCRResult:
        if not self.available():
            raise OCRError("The OCR engine isn't installed on the server.")
        try:
            img = prepare(image_bytes)
        except Exception as e:
            raise OCRError("This image couldn't be processed. Try another photo.") from e
        try:
            text, conf = self._read(img, lang, psm=6)
            # second pass for sparse table layouts (nutrition panels) if the first pass looks thin
            if len(re.findall(r"\d+(?:\.\d+)?", text.split("NUTRITION")[-1] if "NUTRITION" in text.upper() else text)) < 6:
                text2, conf2 = self._read(img, lang, psm=4)
                if len(re.findall(r"\d", text2)) > len(re.findall(r"\d", text)):
                    text, conf = text2, conf2
        except self.pt.TesseractError as e:
            raise OCRError("We couldn't read this label clearly. Try another photo or enter the ingredients manually.") from e
        warnings = []
        if len(text.strip()) < 20:
            raise OCRError("We couldn't read this label clearly. Try another photo or enter the ingredients manually.")
        if conf < 0.6:
            warnings.append("Please review the extracted ingredients carefully.")
        return OCRResult(text=text, confidence=round(conf, 2), provider=self.name, warnings=warnings)

    def _read(self, img, lang, psm):
        data = self.pt.image_to_data(img, lang=lang, config=f"--oem 3 --psm {psm}", output_type=self.pt.Output.DICT)
        # rebuild text line by line from the word boxes
        lines: dict[tuple, list[str]] = {}
        confs = []
        for i, word in enumerate(data["text"]):
            if not word.strip():
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append(word)
            try:
                c = float(data["conf"][i])
            except (TypeError, ValueError):
                c = -1
            if c >= 0:
                confs.append(c)
        text = "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
        conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
        return text, conf
