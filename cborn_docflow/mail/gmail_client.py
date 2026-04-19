"""Gmail API: OAuth2 + ek indirme (readonly)."""

from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any

from cborn_docflow.mail.storage import GMAIL_TOKEN_PATH, ensure_data_dir

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# OCR ile uyumlu uzantılar
_ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def _safe_filename(name: str, fallback: str) -> str:
    name = name.strip() or fallback
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name[:200] if len(name) > 200 else name


def _collect_attachments(part: dict[str, Any], out: list[tuple[str, str]]) -> None:
    if part.get("parts"):
        for sub in part["parts"]:
            _collect_attachments(sub, out)
        return
    aid = part.get("body", {}).get("attachmentId")
    fn = part.get("filename") or ""
    if aid and fn and Path(fn).suffix.lower() in _ALLOWED_EXT:
        out.append((aid, fn))


def authenticate(credentials_json: Path, token_path: Path | None = None) -> Any:
    """Tarayıcı ile OAuth; token diske yazılır."""
    ensure_data_dir()
    token_path = token_path or GMAIL_TOKEN_PATH

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as e:
        msg = "Gmail için: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        raise RuntimeError(msg) from e

    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not credentials_json.is_file():
            msg = f"credentials.json bulunamadı: {credentials_json}"
            raise FileNotFoundError(msg)
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_json), SCOPES)
        creds = flow.run_local_server(port=0, prompt="consent")
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def download_attachments(
    credentials_json: Path,
    dest_dir: Path,
    max_messages: int = 20,
    token_path: Path | None = None,
) -> list[Path]:
    """
    Son mesajlardan (ek olan) uygun uzantılı ekleri indirir.
    Dönen: kaydedilen dosya yolları.
    """
    try:
        from googleapiclient.discovery import build
    except ImportError as e:
        msg = "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        raise RuntimeError(msg) from e

    creds = authenticate(credentials_json, token_path)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    dest_dir.mkdir(parents=True, exist_ok=True)

    lst = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_messages, q="has:attachment")
        .execute()
    )
    mids = [m["id"] for m in lst.get("messages", [])]
    saved: list[Path] = []
    used_names: dict[str, int] = {}

    for mid in mids:
        msg = service.users().messages().get(userId="me", id=mid, format="full").execute()
        payload = msg.get("payload", {})
        parts_list: list[tuple[str, str]] = []
        if payload.get("parts"):
            for sub in payload["parts"]:
                _collect_attachments(sub, parts_list)
        else:
            _collect_attachments(payload, parts_list)

        for att_id, filename in parts_list:
            att = (
                service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=mid, id=att_id)
                .execute()
            )
            raw = att.get("data")
            if not raw:
                continue
            data = base64.urlsafe_b64decode(raw.encode("ascii"))
            safe = _safe_filename(filename, "ek")
            if safe in used_names:
                used_names[safe] += 1
                stem = Path(safe).stem
                suf = Path(safe).suffix
                safe = f"{stem}_{used_names[safe]}{suf}"
            else:
                used_names[safe] = 0
            out_path = dest_dir / safe
            out_path.write_bytes(data)
            saved.append(out_path)

    return saved


def logout(token_path: Path | None = None) -> None:
    p = token_path or GMAIL_TOKEN_PATH
    if p.is_file():
        p.unlink()
