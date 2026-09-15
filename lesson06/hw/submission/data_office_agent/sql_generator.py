"""Генератор SQL запросов для аналитики"""

from __future__ import annotations

from typing import Any

MAX_LIMIT = 1000

# Для каждой метрики: JOIN-цепочка, поле даты, колонки для детальной
# выборки (group_by="none") и агрегаты, используемые при группировке.
_METRIC_CONFIG: dict[str, dict[str, str]] = {
    "net_profit": {
        "from": """FROM fact_cashflow cf
JOIN dim_contracts c ON cf.contract_id = c.contract_id
JOIN dim_clients cl ON c.client_id = cl.client_id
JOIN dim_sales_channels sc ON c.channel_id = sc.channel_id
JOIN dim_client_segments seg ON cl.segment_id = seg.segment_id""",
        "date_field": "cf.period_date",
        "detail_select": "cf.period_date, c.contract_number, cl.client_name, "
                          "sc.channel_name, seg.segment_name, cf.revenue, cf.costs, cf.net_profit",
        "detail_order_by": "cf.net_profit DESC",
        "aggregates": "SUM(cf.revenue) as revenue, SUM(cf.costs) as costs, SUM(cf.net_profit) as net_profit",
        "aggregate_order_by": "net_profit DESC",
    },
    "revenue": {
        "from": """FROM fact_cashflow cf
JOIN dim_contracts c ON cf.contract_id = c.contract_id
JOIN dim_clients cl ON c.client_id = cl.client_id
JOIN dim_sales_channels sc ON c.channel_id = sc.channel_id
JOIN dim_client_segments seg ON cl.segment_id = seg.segment_id""",
        "date_field": "cf.period_date",
        "detail_select": "cf.period_date, c.contract_number, cl.client_name, "
                          "sc.channel_name, seg.segment_name, cf.revenue",
        "detail_order_by": "cf.revenue DESC",
        "aggregates": "SUM(cf.revenue) as revenue",
        "aggregate_order_by": "revenue DESC",
    },
    "positions": {
        "from": """FROM fact_positions p
JOIN dim_contracts c ON p.contract_id = c.contract_id
JOIN dim_clients cl ON c.client_id = cl.client_id
JOIN dim_sales_channels sc ON c.channel_id = sc.channel_id
JOIN dim_client_segments seg ON cl.segment_id = seg.segment_id""",
        "date_field": "p.position_date",
        "detail_select": "p.position_date, c.contract_number, cl.client_name, sc.channel_name, "
                          "seg.segment_name, p.product_name, p.quantity, p.unit_price, "
                          "p.total_amount, (p.total_amount - p.cost_amount) as profit",
        "detail_order_by": "p.total_amount DESC",
        "aggregates": "COUNT(*) as position_count, SUM(p.total_amount) as total_amount, "
                       "SUM(p.total_amount - p.cost_amount) as profit",
        "aggregate_order_by": "total_amount DESC",
    },
    "commissions": {
        "from": """FROM fact_commissions com
JOIN dim_contracts c ON com.contract_id = c.contract_id
JOIN dim_clients cl ON c.client_id = cl.client_id
JOIN dim_sales_channels sc ON c.channel_id = sc.channel_id
JOIN dim_client_segments seg ON cl.segment_id = seg.segment_id""",
        "date_field": "com.commission_date",
        "detail_select": "com.commission_date, c.contract_number, cl.client_name, sc.channel_name, "
                          "seg.segment_name, com.commission_type, com.base_amount, "
                          "com.commission_rate, com.commission_amount",
        "detail_order_by": "com.commission_amount DESC",
        "aggregates": "COUNT(*) as commission_count, SUM(com.base_amount) as base_amount, "
                       "SUM(com.commission_amount) as commission_amount",
        "aggregate_order_by": "commission_amount DESC",
    },
}

# group_by -> (колонка для GROUP BY/SELECT, алиас в результате)
_GROUP_BY_COLUMNS: dict[str, tuple[str, str]] = {
    "channel": ("sc.channel_name", "channel_name"),
    "segment": ("seg.segment_name", "segment_name"),
    "client": ("cl.client_name", "client_name"),
}


def generate_sql_query(
    metric: str,
    period: str,
    sales_channel: str | None = None,
    client_segment: str | None = None,
    group_by: str = "none",
    limit: int = 10,
) -> dict[str, Any]:
    """Генерирует параметризованный SQL запрос на основе параметров.

    Все значения, пришедшие извне (period, sales_channel, client_segment,
    limit), передаются как `?`-плейсхолдеры в `params`, а не подставляются
    в текст запроса — это единственный правильный способ защититься от
    SQL-инъекций. Вызывающий код обязан выполнить `conn.execute(sql, params)`.
    """
    try:
        limit = max(1, min(int(limit), MAX_LIMIT))
        params: list[Any] = []

        if metric == "clients":
            sql = """SELECT cl.client_id, cl.client_name, seg.segment_name,
    cl.registration_date, COUNT(DISTINCT c.contract_id) as contracts_count
FROM dim_clients cl
JOIN dim_client_segments seg ON cl.segment_id = seg.segment_id
LEFT JOIN dim_contracts c ON cl.client_id = c.client_id
WHERE cl.is_active = 1"""
            if client_segment:
                sql += "\nAND seg.segment_name = ?"
                params.append(client_segment)
            sql += "\nGROUP BY cl.client_id, cl.client_name, seg.segment_name, cl.registration_date"
            sql += "\nORDER BY cl.client_name"
            sql += "\nLIMIT ?"
            params.append(limit)
            return {"status": "OK", "sql": sql, "params": params}

        config = _METRIC_CONFIG.get(metric)
        if config is None:
            return {
                "status": "ERROR",
                "error_type": "unknown_metric",
                "message": f"Неизвестная метрика: {metric}",
            }

        date_field = config["date_field"]
        period_fmt = "%Y" if len(period) == 4 else "%Y-%m"  # формат периода уже провалидирован до вызова

        if group_by in _GROUP_BY_COLUMNS:
            group_col, group_label = _GROUP_BY_COLUMNS[group_by]
            select = f"{group_col} as {group_label}, {config['aggregates']}"
            order_by = config["aggregate_order_by"]
        elif group_by == "month":
            group_col = f"strftime('%Y-%m', {date_field})"
            select = f"{group_col} as month, {config['aggregates']}"
            order_by = "month"
        else:
            group_col = None
            select = config["detail_select"]
            order_by = config["detail_order_by"]

        sql = f"SELECT {select}\n{config['from']}\nWHERE strftime('{period_fmt}', {date_field}) = ?"
        params.append(period)

        if sales_channel:
            sql += "\nAND sc.channel_name = ?"
            params.append(sales_channel)
        if client_segment:
            sql += "\nAND seg.segment_name = ?"
            params.append(client_segment)

        if group_col is not None:
            sql += f"\nGROUP BY {group_col}"

        sql += f"\nORDER BY {order_by}"
        sql += "\nLIMIT ?"
        params.append(limit)

        return {"status": "OK", "sql": sql, "params": params}

    except Exception as exc:
        return {
            "status": "ERROR",
            "error_type": "sql_error",
            "message": f"Ошибка формирования SQL: {str(exc)}",
        }