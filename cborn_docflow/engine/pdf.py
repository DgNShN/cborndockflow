"""PDF sayfalarını görüntüye çevirme (PyMuPDF)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


def page_count(path: Path) -> int:
    doc = fitz.open(path)
    try:
        return len(doc)
    finally:
        doc.close()


def iter_pages_as_images(path: Path, dpi: int = 300) -> Iterator[tuple[int, Image.Image]]:
    """Sayfa indeksi (0 tabanlı) ve RGB PIL görüntüsü üretir."""
    doc = fitz.open(path)
    try:
        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            mode = "RGBA" if pix.alpha else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            if img.mode != "RGB":
                img = img.convert("RGB")
            yield i, img
    finally:
        doc.close()
