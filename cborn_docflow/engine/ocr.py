"""Tesseract OCR — CPU; NVIDIA gerekmez."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

_tesseract_configured = False


def _ensure_tesseract_path() -> None:
    """Windows'ta PATH'e eklenmemişse varsayılan kurulum yolunu kullan."""
    global _tesseract_configured
    if _tesseract_configured:
        return
    import pytesseract

    if sys.platform == "win32":
        default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if default.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(default)
    _tesseract_configured = True


@dataclass
class OcrResult:
    text: str
    confidence: float | None  # Tesseract ortalama güven; yoksa None


# OEM 3 = LSTM; PSM 6 = tek metin bloğu (fatura benzeri sayfalar için uygun)
DEFAULT_TESS_CONFIG = "--oem 3 --psm 6"


def pil_to_text(
    image: Image.Image,
    lang: str = "tur+eng",
    *,
    tess_config: str = DEFAULT_TESS_CONFIG,
) -> OcrResult:
    """PIL görüntüsünden metin çıkarır (PDF render vb. için)."""
    _ensure_tesseract_path()
    import pytesseract

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    text = pytesseract.image_to_string(image, lang=lang, config=tess_config)
    try:
        from pytesseract import Output

        data = pytesseract.image_to_data(
            image, lang=lang, output_type=Output.DICT, config=tess_config
        )
        confs = [int(c) for c in data["conf"] if str(c).isdigit() and int(c) >= 0]
        avg = sum(confs) / len(confs) / 100.0 if confs else None
    except Exception:  # noqa: BLE001 — OCR yardımcı; güven opsiyonel
        avg = None
    return OcrResult(text=text.strip(), confidence=avg)


def image_to_text(path: Path, lang: str = "tur+eng") -> OcrResult:
    """Görüntü dosyasından metin çıkarır."""
    img = Image.open(path)
    return pil_to_text(img, lang=lang)
