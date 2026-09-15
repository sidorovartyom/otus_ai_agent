"""Пайплайн обработки заявки в поддержку.

5 шагов, одно ветвление с проверкой, инструмент (KB / биллинг) и память
(история обращений в JSONL):

  1. receive_ticket     - принять заявку
  2. classify_ticket     - определить категорию (LLM, форсированный tool-use)
  3. route_and_resolve   - ВЕТВЛЕНИЕ по категории + вызов инструмента + ПРОВЕРКА результата
  4. compose_reply        - сформировать ответ клиенту (LLM)
  5. log_to_memory        - записать заявку и ответ в память (JSONL)

Схема см. README.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import llm, memory, tools


def receive_ticket(client_id: str, text: str) -> dict[str, Any]:
    """Шаг 1: принять заявку и оформить её как структуру с метаданными."""
    return {
        "client_id": client_id,
        "text": text,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }


def route_and_resolve(ticket: dict[str, Any], category: str) -> tuple[Any, bool]:
    """Шаг 3: ветвление по категории, вызов соответствующего инструмента и
    проверка, дал ли он результат. Возвращает (tool_result, escalate)."""
    if category == "billing":
        invoice = tools.lookup_invoice(ticket["client_id"])
        return invoice, invoice is None  # проверка: счёт не найден -> эскалация
    if category == "technical":
        kb_hit = tools.search_knowledge_base(ticket["text"])
        return kb_hit, kb_hit is None  # проверка: статья не найдена -> эскалация
    return None, True  # category == "other" -> сразу эскалация специалисту


def run_pipeline(client_id: str, text: str, *, verbose: bool = True) -> dict[str, Any]:
    def log(msg: str) -> None:
        if verbose:
            print(msg)

    # Шаг 1
    ticket = receive_ticket(client_id, text)
    log(f"[1/5] Заявка принята: client_id={client_id!r}, text={text!r}")

    history = memory.get_history(client_id)
    if history:
        log(f"       В памяти найдено предыдущих обращений этого клиента: {len(history)}")

    # Шаг 2
    category = llm.classify_ticket(text)
    log(f"[2/5] Категория (LLM): {category}")

    # Шаг 3 - ветвление + проверка
    tool_result, escalate = route_and_resolve(ticket, category)
    if escalate:
        log(f"[3/5] Ветвление: категория={category} -> инструмент не дал результата -> ЭСКАЛАЦИЯ")
    else:
        log(f"[3/5] Ветвление: категория={category} -> инструмент нашёл результат: {tool_result}")

    # Шаг 4
    reply = llm.compose_reply(text, category, tool_result, escalate)
    log(f"[4/5] Ответ клиенту:\n{reply}")

    # Шаг 5
    record = {**ticket, "category": category, "escalated": escalate, "reply": reply}
    memory.append_ticket(record)
    log("[5/5] Заявка записана в память (memory.jsonl)")

    return record
