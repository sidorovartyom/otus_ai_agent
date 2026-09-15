"""Лог выполнения агента (JSONL, по одной строке на запрос)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .metrics import RunRecord

_LOG_PATH = Path(__file__).parent / "runs.jsonl"


def log_run(record: RunRecord) -> None:
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
