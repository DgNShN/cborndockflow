"""Proje kökü ve config dosya yolları."""

from __future__ import annotations

import sys
from pathlib import Path

# cborn_docflow/engine/config_paths.py -> parents[2] = cborn-docflow proje kökü
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
CONFIG_PATH = CONFIG_DIR / "docflow.json"
# Yayıncı bir kez Google OAuth (masaüstü) JSON indirip bu ada koyar; son kullanıcı seçmez.
GMAIL_CLIENT_SECRET_PATH = CONFIG_DIR / "gmail_client_secret.json"


def resolve_gmail_client_secret_path(user_override: str | None) -> Path | None:
    """
    Gmail OAuth istemci dosyası: isteğe bağlı kullanıcı yolu, yoksa paketlenmiş varsayılan.

    Dağıtımda (PyInstaller vb.) dosya çoğu zaman .exe ile aynı klasörde olur.
    """
    u = (user_override or "").strip()
    if u:
        p = Path(u)
        return p if p.is_file() else None
    if GMAIL_CLIENT_SECRET_PATH.is_file():
        return GMAIL_CLIENT_SECRET_PATH
    if getattr(sys, "frozen", False):
        p = Path(sys.executable).resolve().parent / "gmail_client_secret.json"
        if p.is_file():
            return p
    return None
