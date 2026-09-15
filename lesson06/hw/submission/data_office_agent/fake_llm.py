"""Эмулятор LLM для тестирования без реального API"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def fake_llm(user_request: str) -> dict[str, Any]:
    """Эмулятор LLM - определяет параметры на основе запроса пользователя

    В реальном приложении здесь был бы вызов Anthropic API
    """
    request_lower = user_request.lower()

    # Определяем метрику
    metric = "net_profit"  # По умолчанию

    # Сначала проверяем ЧП (приоритет выше)
    if "чп" in request_lower or "cashflow" in request_lower or "прибыл" in request_lower:
        metric = "net_profit"
    # Потом остальные метрики
    elif "позиц" in request_lower or "транзакц" in request_lower:
        metric = "positions"
    elif "комисс" in request_lower:
        metric = "commissions"
    elif "выручк" in request_lower or "доход" in request_lower:
        metric = "revenue"
    elif "клиент" in request_lower:
        metric = "clients"

    # Определяем период
    period = "2026"
    if "2024" in request_lower:
        period = "2024"
    elif "2025" in request_lower:
        period = "2025"
    elif "2026" in request_lower:
        period = "2026"
    elif "текущ" in request_lower or "этот год" in request_lower:
        period = str(datetime.now().year)

    # Определяем канал продаж
    sales_channel = None
    if "digital" in request_lower or "диджитал" in request_lower:
        sales_channel = "Digital"
    elif "retail" in request_lower or "ритейл" in request_lower or "розниц" in request_lower:
        sales_channel = "Retail"
    elif "corporate" in request_lower or "корпоратив" in request_lower:
        sales_channel = "Corporate"
    elif "partner" in request_lower or "партнер" in request_lower:
        sales_channel = "Partner"

    # Определяем сегмент
    client_segment = None
    if "vip" in request_lower:
        client_segment = "VIP"
    elif "premium" in request_lower or "премиум" in request_lower:
        client_segment = "Premium"
    elif "standard" in request_lower or "стандарт" in request_lower:
        client_segment = "Standard"
    elif "small" in request_lower or "малы" in request_lower:
        client_segment = "Small"

    # Определяем группировку
    group_by = "none"
    if "по канал" in request_lower or ("группировк" in request_lower and "канал" in request_lower):
        group_by = "channel"
    elif "по сегмент" in request_lower or ("группировк" in request_lower and "сегмент" in request_lower):
        group_by = "segment"
    elif "по клиент" in request_lower or ("группировк" in request_lower and "клиент" in request_lower) or (
        "топ" in request_lower and "клиент" in request_lower and metric != "clients"
    ):
        group_by = "client"
    elif "по месяц" in request_lower or ("группировк" in request_lower and "месяц" in request_lower):
        group_by = "month"

    # Определяем лимит: "топ-5", "топ 5", "топ5" и т.п.
    limit = 10
    top_match = re.search(r"топ[\s-]*(\d+)", request_lower)
    if top_match:
        limit = int(top_match.group(1))

    arguments = {
        "metric": metric,
        "period": period,
    }

    if sales_channel:
        arguments["sales_channel"] = sales_channel
    if client_segment:
        arguments["client_segment"] = client_segment
    if group_by != "none":
        arguments["group_by"] = group_by
    if limit != 10:
        arguments["limit"] = limit

    return {
        "type": "tool_call",
        "tool": "generate_analytics_query",
        "arguments": arguments,
    }
