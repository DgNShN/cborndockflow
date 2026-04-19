"""Basit kural motoru: anahtar kelime / regex ile etiket."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Rule:
    name: str
    pattern: re.Pattern[str]
    tag: str


def default_rules() -> list[Rule]:
    """Örnek kurallar — kendi ihtiyacına göre genişletilir."""
    return [
        Rule(
            name="fatura",
            pattern=re.compile(r"fatura|invoice|vat|kdv", re.IGNORECASE),
            tag="fatura",
        ),
        Rule(
            name="sözleşme",
            pattern=re.compile(r"sözleşme|contract", re.IGNORECASE),
            tag="sozlesme",
        ),
    ]


def match_tags(text: str, rules: list[Rule]) -> list[str]:
    tags: list[str] = []
    for r in rules:
        if r.pattern.search(text):
            tags.append(r.tag)
    return tags
