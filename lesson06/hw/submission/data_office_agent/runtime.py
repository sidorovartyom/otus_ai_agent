"""Регистрация и выполнение инструментов с валидацией"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, Literal, TypedDict

from .analytics_tools import generate_analytics_query


class SchemaProperty(TypedDict, total=False):
    type: Literal["string", "integer"]
    enum: list[str]
    description: str


class ToolSchema(TypedDict):
    required: list[str]
    properties: dict[str, SchemaProperty]


class ToolDefinition(TypedDict):
    description: str
    schema: ToolSchema
    executor: Callable[..., dict[str, Any]]


# JSON Schema для инструмента
analytics_schema: ToolSchema = {
    "required": ["metric", "period"],
    "properties": {
        "metric": {
            "type": "string",
            "description": "Запрашиваемая метрика",
            "enum": ["net_profit", "positions", "commissions", "revenue", "clients"]
        },
        "period": {
            "type": "string",
            "description": "Период анализа (формат YYYY или YYYY-MM)",
        },
        "sales_channel": {
            "type": "string",
            "description": "Канал продаж для фильтрации (опционально)",
            "enum": ["Digital", "Retail", "Corporate", "Partner", "Mobile App"],
        },
        "client_segment": {
            "type": "string",
            "description": "Сегмент клиентов для фильтрации (опционально)",
            "enum": ["VIP", "Premium", "Standard", "Small"],
        },
        "group_by": {
            "type": "string",
            "description": "Группировка результатов",
            "enum": ["channel", "segment", "client", "month", "none"]
        },
        "limit": {
            "type": "integer",
            "description": "Лимит записей в результате (по умолчанию 10, максимум 1000)",
        }
    },
}

MAX_LIMIT = 1000

# Регистрация инструментов
TOOLS: dict[str, ToolDefinition] = {
    "generate_analytics_query": {
        "description": "Генерирует SQL запрос для получения аналитических данных из Data Office (ЧП-cashflow, позиции, комиссии) и возвращает ссылку на соответствующий дашборд",
        "schema": analytics_schema,
        "executor": generate_analytics_query,
    }
}


def error(error_type: str, message: str) -> dict[str, Any]:
    """Формирует сообщение об ошибке"""
    return {
        "status": "ERROR",
        "error_type": error_type,
        "message": message,
    }


def validate(schema: ToolSchema, args: dict[str, Any]) -> dict[str, Any]:
    """Валидирует параметры по JSON схеме"""
    # Проверка обязательных полей
    for field in schema.get("required", []):
        if field not in args or not args[field]:
            return error("validation_error", f"Отсутствует обязательный параметр: {field}")

    # Проверка типов и enum
    for field, value in args.items():
        if field not in schema["properties"]:
            continue

        prop = schema["properties"][field]

        # Проверка enum
        if "enum" in prop and value not in prop["enum"]:
            return error("validation_error", f"Некорректное значение для {field}. Допустимые: {', '.join(prop['enum'])}")

        # Проверка типа
        if prop["type"] == "string" and not isinstance(value, str):
            return error("validation_error", f"{field} должен быть строкой")

        if prop["type"] == "integer" and not isinstance(value, int):
            return error("validation_error", f"{field} должен быть целым числом")

    # Валидация диапазона limit (защита от чрезмерно тяжёлых выборок)
    if "limit" in args:
        limit_value = args["limit"]
        if not isinstance(limit_value, int) or not (1 <= limit_value <= MAX_LIMIT):
            return error("validation_error", f"limit должен быть целым числом от 1 до {MAX_LIMIT}")

    # Валидация формата периода
    period = args.get("period", "")
    if period:
        if not (len(period) == 4 or len(period) == 7):
            return error("validation_error", "Период должен быть в формате YYYY или YYYY-MM")

        try:
            if len(period) == 4:
                year = int(period)
                if year < 2000 or year > 2100:
                    raise ValueError()
            else:
                datetime.strptime(period, "%Y-%m")
        except (ValueError, Exception):
            return error("validation_error", f"Некорректный формат периода: {period}")

    return {"status": "OK"}


def run_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Выполняет инструмент с валидацией"""
    if name not in TOOLS:
        return error("unknown_tool", f"Неизвестный инструмент: {name}")

    tool = TOOLS[name]

    # Валидация параметров
    validation = validate(tool["schema"], args)
    if validation["status"] != "OK":
        return validation

    # Выполнение инструмента
    try:
        return tool["executor"](**args)
    except Exception as exc:
        return error("tool_error", f"Ошибка выполнения: {str(exc)}")
