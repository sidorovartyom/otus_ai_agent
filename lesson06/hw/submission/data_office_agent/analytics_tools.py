"""Инструменты для аналитики Data Office"""

from __future__ import annotations

import sqlite3
from typing import Any

from .dashboards import get_dashboard
from .db import get_db_connection
from .sql_generator import generate_sql_query


def generate_analytics_query(
    metric: str,
    period: str,
    sales_channel: str | None = None,
    client_segment: str | None = None,
    group_by: str = "none",
    limit: int = 10
) -> dict[str, Any]:
    """Генерирует SQL запрос и возвращает ссылку на дашборд"""

    # Генерируем SQL
    sql_result = generate_sql_query(
        metric=metric,
        period=period,
        sales_channel=sales_channel,
        client_segment=client_segment,
        group_by=group_by,
        limit=limit
    )

    if sql_result["status"] != "OK":
        return sql_result

    # Получаем информацию о дашборде
    dashboard = get_dashboard(metric)

    # Пробуем выполнить запрос для проверки
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(sql_result["sql"], sql_result["params"])
            rows = cursor.fetchall()

            # Преобразуем результаты в список словарей
            results = []
            for row in rows:
                results.append(dict(row))

    except sqlite3.Error as exc:
        return {
            "status": "ERROR",
            "error_type": "database_error",
            "message": f"Ошибка выполнения запроса: {str(exc)}",
        }

    return {
        "status": "OK",
        "sql": sql_result["sql"],
        "params": sql_result["params"],
        "dashboard": dashboard,
        "preview": results[:3],  # Первые 3 записи для превью
        "total_rows": len(results),
    }
