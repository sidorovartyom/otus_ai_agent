"""Маппинг метрик на дашборды"""

from __future__ import annotations

DASHBOARDS = {
    "net_profit": {
        "name": "Дашборд ЧП (cashflow)",
        "url": "https://bi.company.com/dashboards/cashflow",
        "description": "Детальный анализ ЧП (cashflow) по периодам, каналам и сегментам"
    },
    "positions": {
        "name": "Дашборд Позиции",
        "url": "https://bi.company.com/dashboards/positions",
        "description": "Анализ позиций/транзакций с разбивкой по продуктам и клиентам"
    },
    "commissions": {
        "name": "Дашборд Комиссии",
        "url": "https://bi.company.com/dashboards/commissions",
        "description": "Анализ комиссионных выплат по типам и каналам"
    },
    "revenue": {
        "name": "Дашборд ЧП (cashflow)",
        "url": "https://bi.company.com/dashboards/cashflow",
        "description": "Детальный анализ выручки (входит в дашборд ЧП)"
    },
    "clients": {
        "name": "Дашборд Клиенты",
        "url": "https://bi.company.com/dashboards/clients",
        "description": "Анализ клиентской базы и сегментации"
    }
}


def get_dashboard(metric: str) -> dict[str, str]:
    """Возвращает информацию о дашборде для метрики"""
    return DASHBOARDS.get(metric, {
        "name": "Общий дашборд",
        "url": "https://bi.company.com/dashboards/overview",
        "description": "Общий обзор аналитики"
    })
