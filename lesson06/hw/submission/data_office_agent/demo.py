"""Демонстрация работы Data Office Analytics Agent"""

from __future__ import annotations

from .db import init_database
from .fake_llm import fake_llm
from .homework import TOOL_SCHEMA
from .real_llm import LLMUnavailableError, call_llm_for_tool, is_configured
from .runtime import run_tool


def run_agent(user_request: str) -> dict:
    """Запускает агента для обработки запроса пользователя.

    Если в .env настроен доступ к Anthropic API - решение о вызове
    инструмента принимает реальная LLM (function calling). Иначе
    используется fake_llm.py, чтобы демо оставалось воспроизводимым
    без секретов/сети.
    """
    if is_configured():
        try:
            decision = call_llm_for_tool(user_request, TOOL_SCHEMA)
            print("   [LLM: реальный вызов Anthropic API]")
        except LLMUnavailableError as exc:
            print(f"   [LLM: реальный вызов не удался ({exc}), fallback на эмулятор]")
            decision = fake_llm(user_request)
    else:
        print("   [LLM: .env не настроен, используется эмулятор fake_llm]")
        decision = fake_llm(user_request)

    # Проверяем корректность решения
    if decision.get("type") != "tool_call":
        return {
            "status": "ERROR",
            "error_type": "invalid_llm_output",
            "message": "Ожидался вызов инструмента",
        }

    # Выполняем инструмент
    tool_name = decision.get("tool")
    tool_args = decision.get("arguments", {})
    result = run_tool(tool_name, tool_args)

    return {
        "status": "OK",
        "user_request": user_request,
        "tool_call": decision,
        "tool_result": result,
    }


def main():
    """Демонстрация работы агента"""
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("="*80)
    print("Data Office Analytics Agent - Демонстрация")
    print("="*80)

    # Инициализируем БД
    print("\nИнициализация базы данных...")
    init_database()

    # Тестовые запросы
    test_requests = [
        "получить ЧП за текущий год по каналу продаж Digital",
        "показать топ-5 клиентов по позициям",
        "комиссии за 2025 год по сегменту VIP",
        "выручка по месяцам в 2026 году",
    ]

    for i, request in enumerate(test_requests, 1):
        print("\n" + "="*80)
        print(f"ТЕСТОВЫЙ ЗАПРОС #{i}")
        print("="*80)
        print(f"Запрос: {request}")
        print()

        # Обрабатываем запрос
        result = run_agent(request)

        if result["status"] != "OK":
            print(f"[ОШИБКА] [{result['error_type']}] {result['message']}")
            continue

        tool_result = result["tool_result"]

        if tool_result["status"] != "OK":
            print(f"[ОШИБКА] [{tool_result['error_type']}] {tool_result['message']}")
            continue

        print("[OK] Запрос обработан успешно!")
        print()
        print("Параметры инструмента:")
        for key, value in result["tool_call"]["arguments"].items():
            print(f"   - {key}: {value}")

        print()
        print("SQL Запрос (параметризованный, значения подставляются через params):")
        print("-" * 80)
        print(tool_result["sql"])
        print(f"params: {tool_result['params']}")
        print("-" * 80)

        print()
        print("Дашборд для детального анализа:")
        dashboard = tool_result["dashboard"]
        print(f"   Название: {dashboard['name']}")
        print(f"   URL: {dashboard['url']}")
        print(f"   Описание: {dashboard['description']}")

        print()
        print(f"Превью результатов (найдено записей: {tool_result['total_rows']}):")
        if tool_result["preview"]:
            for j, row in enumerate(tool_result["preview"], 1):
                print(f"\n   Запись {j}:")
                for key, value in row.items():
                    print(f"      - {key}: {value}")
        else:
            print("   (нет данных)")

    print("\n" + "="*80)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*80)


if __name__ == "__main__":
    main()
