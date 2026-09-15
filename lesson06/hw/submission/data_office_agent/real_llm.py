"""Реальный вызов инструмента через LLM (Anthropic tool use).

Использует тот же паттерн подключения, что и lesson04/01-single-tool-single-turn.py:
креды и корпоративный сертификат берутся из .env в корне репозитория.
Если .env не настроен или LLM недоступен - вызывающий код (demo.py) должен
откатиться на fake_llm.py, чтобы демонстрация оставалась воспроизводимой
без доступа к реальному API.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    _ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(_ENV_PATH, override=True)
except ImportError:
    pass  # python-dotenv не установлен - полагаемся на переменные окружения, если они уже заданы


class LLMUnavailableError(RuntimeError):
    """Не удалось получить настройки или ответ от LLM."""


def is_configured() -> bool:
    """Есть ли в .env всё необходимое для реального вызова LLM."""
    return bool(
        os.getenv("ANTHROPIC_AUTH_TOKEN")
        and os.getenv("ANTHROPIC_BASE_URL")
        and os.getenv("CERT_PATH")
    )


def call_llm_for_tool(user_request: str, tool_schema: dict[str, Any]) -> dict[str, Any]:
    """Отправляет запрос пользователя в LLM с описанием инструмента.

    Возвращает результат в том же формате, что и fake_llm.fake_llm():
    {"type": "tool_call", "tool": name, "arguments": {...}}
    или {"type": "text", "text": "..."}, если модель не вызвала инструмент.
    """
    if not is_configured():
        raise LLMUnavailableError("В .env не заданы ANTHROPIC_AUTH_TOKEN/ANTHROPIC_BASE_URL/CERT_PATH")

    try:
        import anthropic
        try:
            import httpx2 as httpx  # SDK антропик в этом окружении требует httpx2, а не httpx
        except ImportError:
            import httpx
    except ImportError as exc:
        raise LLMUnavailableError(f"Не установлены зависимости для вызова LLM: {exc}") from exc

    try:
        http_client = httpx.Client(verify=os.environ["CERT_PATH"])
        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
            base_url=os.environ["ANTHROPIC_BASE_URL"],
            http_client=http_client,
        )

        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
            max_tokens=1024,
            tools=[tool_schema],
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=[{"role": "user", "content": user_request}],
        )
    except Exception as exc:
        raise LLMUnavailableError(f"Ошибка вызова Anthropic API: {exc}") from exc

    tool_use = next((block for block in response.content if block.type == "tool_use"), None)
    if tool_use is not None:
        return {"type": "tool_call", "tool": tool_use.name, "arguments": dict(tool_use.input)}

    text_block = next((block for block in response.content if block.type == "text"), None)
    return {"type": "text", "text": text_block.text if text_block else ""}
