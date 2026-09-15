"""Агент: подключённый контекст + потоковый (streaming) ответ.

Паттерн подключения к Anthropic API - тот же, что в
lesson04/01-single-tool-single-turn.py: креды и корпоративный сертификат
берутся из .env в корне репозитория.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
import anthropic

try:
    import httpx2 as httpx  # SDK в некоторых окружениях требует httpx2, а не httpx
except ImportError:
    import httpx

from .context_source import get_context

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# lesson09/hw/context_streaming_agent/agent.py -> parents[3] == корень репозитория
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

SYSTEM_PROMPT_TEMPLATE = """Ты - агент поддержки сервиса Otus Cloud.
Отвечай на вопросы пользователя, ОПИРАЯСЬ ТОЛЬКО на контекст ниже.
Если ответа на вопрос в контексте нет - честно скажи, что не знаешь,
и не выдумывай факты (цены, SLA, контакты).

# Контекст (база знаний Otus Cloud)
{context}
"""


def print_delta(text: str) -> None:
    """on_delta по умолчанию: печатает фрагмент ответа сразу, без буферизации."""
    print(text, end="", flush=True)


def stream_reply(messages: list[dict], *, on_delta: Callable[[str], None] = print_delta) -> str:
    """Отправляет messages в LLM вместе с подключённым контекстом и стримит ответ.

    on_delta вызывается для каждого текстового фрагмента по мере его
    получения от API (см. README.md - под капотом это Server-Sent Events).
    Возвращает полный накопленный текст ответа (нужен, чтобы добавить его
    в историю messages как ход ассистента).
    """
    context = get_context()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    full_text = ""
    with _client.messages.stream(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            on_delta(text)
            full_text += text
    return full_text
