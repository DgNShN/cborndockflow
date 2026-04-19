"""Token ve veri dizinleri."""

from __future__ import annotations

from pathlib import Path

DATA_DIR = Path.home() / ".cborn-docflow"
GMAIL_TOKEN_PATH = DATA_DIR / "gmail_token.json"
OUTLOOK_MSAL_CACHE = DATA_DIR / "outlook_msal_cache.json"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
