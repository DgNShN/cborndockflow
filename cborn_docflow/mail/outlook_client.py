"""Microsoft Graph: Outlook gelen kutusu ekleri (delegated OAuth)."""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

import urllib.request

from cborn_docflow.mail.storage import OUTLOOK_MSAL_CACHE, ensure_data_dir

_ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}

GRAPH = "https://graph.microsoft.com/v1.0"
# Azure'da kayıtlı uygulama (public client); yeniden yönlendirme: http://localhost
SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/User.Read",
    "offline_access",
]


def _safe_filename(name: str, fallback: str) -> str:
    name = name.strip() or fallback
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:200] if len(name) > 200 else name


def _graph_get(token: str, url: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def authenticate_interactive(client_id: str, tenant: str = "common") -> dict[str, Any]:
    """
    MSAL ile etkileşimli giriş. Azure'da kayıtlı uygulama (public client) gerekir.
    tenant: 'common' | 'organizations' | 'consumers' veya kiracı GUID
    """
    ensure_data_dir()
    try:
        import msal
    except ImportError as e:
        msg = "pip install msal"
        raise RuntimeError(msg) from e

    authority = f"https://login.microsoftonline.com/{tenant}"
    cache = msal.SerializableTokenCache()
    if OUTLOOK_MSAL_CACHE.is_file():
        cache.deserialize(OUTLOOK_MSAL_CACHE.read_text(encoding="utf-8"))

    app = msal.PublicClientApplication(
        client_id,
        authority=authority,
        token_cache=cache,
    )

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        result = app.acquire_token_interactive(scopes=SCOPES)

    if OUTLOOK_MSAL_CACHE.parent:
        OUTLOOK_MSAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if cache.has_state_changed:
        OUTLOOK_MSAL_CACHE.write_text(cache.serialize(), encoding="utf-8")

    if "access_token" not in result:
        err = result.get("error_description") or result.get("error") or str(result)
        msg = f"Outlook oturumu başarısız: {err}"
        raise RuntimeError(msg)
    return result


def get_token_from_cache(client_id: str, tenant: str = "common") -> str | None:
    try:
        import msal
    except ImportError:
        return None
    if not OUTLOOK_MSAL_CACHE.is_file():
        return None
    authority = f"https://login.microsoftonline.com/{tenant}"
    cache = msal.SerializableTokenCache()
    cache.deserialize(OUTLOOK_MSAL_CACHE.read_text(encoding="utf-8"))
    app = msal.PublicClientApplication(client_id, authority=authority, token_cache=cache)
    accounts = app.get_accounts()
    if not accounts:
        return None
    result = app.acquire_token_silent(SCOPES, account=accounts[0])
    if result and "access_token" in result:
        if cache.has_state_changed and OUTLOOK_MSAL_CACHE.parent:
            OUTLOOK_MSAL_CACHE.write_text(cache.serialize(), encoding="utf-8")
        return result["access_token"]
    return None


def download_attachments(
    client_id: str,
    dest_dir: Path,
    max_messages: int = 20,
    tenant: str = "common",
) -> list[Path]:
    """Gelen kutusunda ek olan son mesajlardan dosya indirir."""
    token = get_token_from_cache(client_id, tenant)
    if not token:
        result = authenticate_interactive(client_id, tenant)
        token = result["access_token"]

    dest_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    used_names: dict[str, int] = {}

    url = (
        f"{GRAPH}/me/mailFolders/inbox/messages"
        f"?$top={max_messages}&$orderby=receivedDateTime desc"
        f"&$select=id,subject,hasAttachments"
    )
    data = _graph_get(token, url)
    for item in data.get("value", []):
        if not item.get("hasAttachments"):
            continue
        mid = item["id"]
        att_url = f"{GRAPH}/me/messages/{mid}/attachments"
        atdata = _graph_get(token, att_url)
        for att in atdata.get("value", []):
            if att.get("@odata.type") != "#microsoft.graph.fileAttachment":
                continue
            fn = att.get("name") or "ek"
            if Path(fn).suffix.lower() not in _ALLOWED_EXT:
                continue
            b64 = att.get("contentBytes")
            if not b64:
                continue
            raw = base64.b64decode(b64)
            safe = _safe_filename(fn, "ek")
            if safe in used_names:
                used_names[safe] += 1
                stem = Path(safe).stem
                suf = Path(safe).suffix
                safe = f"{stem}_{used_names[safe]}{suf}"
            else:
                used_names[safe] = 0
            out_path = dest_dir / safe
            out_path.write_bytes(raw)
            saved.append(out_path)

    return saved


def logout() -> None:
    if OUTLOOK_MSAL_CACHE.is_file():
        OUTLOOK_MSAL_CACHE.unlink()
