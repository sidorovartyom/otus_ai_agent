"""Инструменты, которые пайплайн вызывает на шаге маршрутизации.

search_knowledge_base - поиск по локальной базе знаний (файл).
lookup_invoice - имитация вызова внешнего биллингового API (мок).
"""

from __future__ import annotations

import re
from pathlib import Path

_KB_PATH = Path(__file__).parent / "knowledge_base.md"

_MOCK_INVOICES: dict[str, dict] = {
    "client_1": {"invoice_id": "INV-2026-001", "amount": 4990, "currency": "RUB", "status": "paid"},
    "client_2": {"invoice_id": "INV-2026-002", "amount": 990, "currency": "RUB", "status": "overdue"},
}


def search_knowledge_base(query: str) -> str | None:
    """Возвращает наиболее подходящий раздел базы знаний, либо None, если совпадений нет."""
    text = _KB_PATH.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=## )", text)
    query_words = {w for w in re.findall(r"\w+", query.lower()) if len(w) > 3}

    best_section, best_score = None, 0
    for section in sections:
        section_words = set(re.findall(r"\w+", section.lower()))
        score = len(query_words & section_words)
        if score > best_score:
            best_section, best_score = section, score

    return best_section.strip() if best_score > 0 else None


def lookup_invoice(client_id: str) -> dict | None:
    """Имитация вызова биллингового API: возвращает счёт клиента или None, если не найден."""
    return _MOCK_INVOICES.get(client_id)
