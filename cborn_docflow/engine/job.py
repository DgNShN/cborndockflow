"""Tek dosya OCR işi — UI thread ve kuyruk tarafından ortak kullanılır."""

from __future__ import annotations

from pathlib import Path

from cborn_docflow.engine.cleanup import cleanup_ocr_text
from cborn_docflow.engine.ocr import OcrResult, image_to_text, pil_to_text
from cborn_docflow.engine.pdf import iter_pages_as_images, page_count

PDF_MAX_PAGES = 100


def _with_cleanup(r: OcrResult) -> OcrResult:
    return OcrResult(text=cleanup_ocr_text(r.text), confidence=r.confidence)


def run_ocr(path: Path, pdf_mode: str | None = None) -> OcrResult:
    """
    pdf_mode: None = görüntü dosyası; \"first\" | \"all\" = PDF.
    """
    if pdf_mode is None:
        return _with_cleanup(image_to_text(path))

    n = page_count(path)
    if n == 0:
        msg = "PDF boş."
        raise ValueError(msg)

    if pdf_mode == "first":
        for _i, img in iter_pages_as_images(path):
            return _with_cleanup(pil_to_text(img))
        msg = "Sayfa okunamadı."
        raise RuntimeError(msg)

    parts: list[str] = []
    confs: list[float] = []
    for idx, (i, img) in enumerate(iter_pages_as_images(path)):
        if idx >= PDF_MAX_PAGES:
            parts.append(f"--- (İlk {PDF_MAX_PAGES} sayfa işlendi; devamı atlandı) ---")
            break
        result = pil_to_text(img)
        parts.append(f"--- Sayfa {i + 1} ---\n\n{result.text}")
        if result.confidence is not None:
            confs.append(result.confidence)
    text = "\n\n".join(parts)
    avg_conf = sum(confs) / len(confs) if confs else None
    return _with_cleanup(OcrResult(text=text.strip(), confidence=avg_conf))
