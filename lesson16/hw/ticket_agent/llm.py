"""Подключение к Anthropic API - тот же паттерн, что в lesson04/lesson09:
креды и корпоративный сертификат берутся из .env в корне репозитория.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import anthropic

try:
    import httpx2 as httpx  # SDK в некоторых окружениях требует httpx2, а не httpx
except ImportError:
    import httpx

# lesson16/hw/ticket_agent/llm.py -> parents[3] == корень репозитория
_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_ENV_PATH, override=True)

ANTHROPIC_AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN")
BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
CERT_PATH = os.getenv("CERT_PATH")

if not ANTHROPIC_AUTH_TOKEN:
    raise ValueError("Пожалуйста, установите ANTHROPIC_AUTH_TOKEN в .env файле")
if not BASE_URL:
    raise ValueError("Пожалуйста, установите ANTHROPIC_BASE_URL в .env файле")
if not CERT_PATH:
    raise ValueError("Пожалуйста, установите CERT_PATH в .env файле")

_http_client = httpx.Client(verify=CERT_PATH)
_client = anthropic.Anthropic(api_key=ANTHROPIC_AUTH_TOKEN, base_url=BASE_URL, http_client=_http_client)

_CLASSIFY_TOOL = {
    "name": "classify_ticket",
    "description": "Classify a support ticket into exactly one category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["billing", "technical", "other"]},
        },
        "required": ["category"],
    },
}


def classify_ticket(text: str) -> str:
    """Шаг 2 пайплайна: классификация обращения.

    Вызов tool форсируется (tool_choice={"type": "tool", ...}), чтобы
    гарантированно получить одну из трёх категорий, а не текст в
    произвольном формате, который пришлось бы парсить.
    """
    response = _client.messages.create(
        model=MODEL,
        max_tokens=256,
        tools=[_CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_ticket"},
        messages=[{"role": "user", "content": text}],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    return tool_use.input["category"]


def compose_reply(text: str, category: str, tool_result, escalate: bool) -> str:
    """Шаг 4 пайплайна: формирование ответа клиенту на основе результата инструмента."""
    if escalate:
        context = "Информация не найдена автоматически - обращение эскалировано специалисту поддержки."
    else:
        context = f"Данные из инструмента: {tool_result}"

    prompt = (
        f"Обращение клиента (категория: {category}): {text}\n\n"
        f"{context}\n\n"
        "Составь короткий вежливый ответ клиенту на русском языке."
    )
    response = _client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text_block = next(block for block in response.content if block.type == "text")
    return text_block.text
