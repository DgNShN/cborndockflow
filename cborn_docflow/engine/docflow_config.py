"""docflow.json: kurallar + isteğe bağlı çıktı klasörü."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from cborn_docflow.engine.config_paths import CONFIG_PATH
from cborn_docflow.engine.rules import Rule, default_rules

_DEFAULT_JSON = """{
  "rules": [
    {
      "name": "fatura",
      "pattern": "fatura|invoice|vat|kdv",
      "tag": "fatura",
      "ignore_case": true
    },
    {
      "name": "sözleşme",
      "pattern": "sözleşme|contract",
      "tag": "sozlesme",
      "ignore_case": true
    }
  ],
  "output": {
    "enabled": false,
    "directory": "",
    "by_tag_subfolders": true,
    "unmatched_subfolder": "_diger"
  }
}
"""


@dataclass
class OutputSettings:
    enabled: bool
    directory: str
    by_tag_subfolders: bool
    unmatched_subfolder: str


def _parse_rules(data: object) -> list[Rule]:
    if not isinstance(data, list):
        return default_rules()
    rules: list[Rule] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            name = str(item["name"])
            pattern_s = str(item["pattern"])
            tag = str(item["tag"])
            ign = bool(item.get("ignore_case", True))
            flags = re.IGNORECASE if ign else 0
            rules.append(
                Rule(name=name, pattern=re.compile(pattern_s, flags), tag=tag)
            )
        except (KeyError, re.error):
            continue
    return rules if rules else default_rules()


def _parse_output(obj: object) -> OutputSettings:
    if not isinstance(obj, dict):
        return OutputSettings(False, "", True, "_diger")
    return OutputSettings(
        enabled=bool(obj.get("enabled", False)),
        directory=str(obj.get("directory", "") or "").strip(),
        by_tag_subfolders=bool(obj.get("by_tag_subfolders", True)),
        unmatched_subfolder=str(obj.get("unmatched_subfolder", "_diger") or "_diger"),
    )


def ensure_default_config() -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.is_file():
        CONFIG_PATH.write_text(_DEFAULT_JSON, encoding="utf-8")


def load_docflow() -> tuple[list[Rule], OutputSettings]:
    ensure_default_config()
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_rules(), OutputSettings(False, "", True, "_diger")
    if not isinstance(raw, dict):
        return default_rules(), OutputSettings(False, "", True, "_diger")
    rules = _parse_rules(raw.get("rules"))
    output = _parse_output(raw.get("output"))
    return rules, output


def load_docflow_raw() -> tuple[list[dict], OutputSettings]:
    """Ayar penceresi için ham kural listesi (dict) + çıktı ayarı."""
    ensure_default_config()
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = json.loads(_DEFAULT_JSON)
    if not isinstance(raw, dict):
        raw = json.loads(_DEFAULT_JSON)
    rules = raw.get("rules")
    if not isinstance(rules, list):
        rules = []
    out: list[dict] = []
    for item in rules:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": str(item.get("name", "")),
                "pattern": str(item.get("pattern", "")),
                "tag": str(item.get("tag", "")),
                "ignore_case": bool(item.get("ignore_case", True)),
            }
        )
    return out, _parse_output(raw.get("output"))


def save_docflow_raw(rules: list[dict], output: OutputSettings) -> None:
    """docflow.json dosyasını yazar; kurallar regex olarak doğrulanır."""
    for r in rules:
        pat = r.get("pattern", "")
        if not isinstance(pat, str) or not pat.strip():
            msg = f"Boş pattern: {r.get('name', '?')}"
            raise ValueError(msg)
        try:
            re.compile(pat)
        except re.error as e:
            msg = f"Geçersiz regex ({r.get('name', '?')}): {e}"
            raise ValueError(msg) from e
    data = {
        "rules": rules,
        "output": {
            "enabled": output.enabled,
            "directory": output.directory,
            "by_tag_subfolders": output.by_tag_subfolders,
            "unmatched_subfolder": output.unmatched_subfolder,
        },
    }
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def copy_to_output_if_enabled(
    source: Path,
    tags: list[str],
    output: OutputSettings | None = None,
) -> str | None:
    """
    Ayar açıksa dosyayı hedef klasöre kopyalar. Başarılıysa hedef yol, yoksa None.
    Hata mesajı üretmez; sessizce None döner (log üst katmanda).
    """
    if output is None:
        _, output = load_docflow()
    if not output.enabled or not output.directory:
        return None
    base = Path(output.directory).expanduser().resolve()
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    if not source.is_file():
        return None

    if output.by_tag_subfolders:
        if tags:
            sub = tags[0]
            for ch in '<>:"/\\|?*':
                sub = sub.replace(ch, "_")
            dest_dir = base / sub
        else:
            dest_dir = base / output.unmatched_subfolder
    else:
        dest_dir = base

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / source.name
        if dest.resolve() == source.resolve():
            return None
        shutil.copy2(source, dest)
        return str(dest)
    except OSError:
        return None
