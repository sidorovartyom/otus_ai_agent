"""Простая файловая память истории обработанных заявок (JSONL)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_MEMORY_PATH = Path(__file__).parent / "memory.jsonl"


def append_ticket(record: dict[str, Any]) -> None:
    """Дописывает обработанную заявку в конец файла памяти."""
    with _MEMORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_history(client_id: str) -> list[dict[str, Any]]:
    """Возвращает все ранее обработанные заявки этого клиента."""
    if not _MEMORY_PATH.exists():
        return []
    history = []
    with _MEMORY_PATH.open(encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if record.get("client_id") == client_id:
                history.append(record)
    return history
