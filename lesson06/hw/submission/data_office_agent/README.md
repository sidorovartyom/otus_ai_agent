# Data Office Analytics Agent

Домашнее задание по курсу "Создание ИИ агентов" - Урок 6

## 📋 Задание

Реализовать вызов внешнего инструмента и оформить логику его использования в виде SOP:

- ✅ Определить функцию (SQL)
- ✅ Описать JSON-схему функции
- ✅ Реализовать вызов функции через LLM
- ✅ Оформить SOP для использования инструмента
- ✅ Добавить обработку базовых ошибок

## 🎯 Функционал

Агент помогает получить SQL запросы для анализа данных из Data Office (Confluence) и предоставляет ссылки на соответствующие дашборды.

**Пример запроса:** "получить ЧП (cashflow) за текущий год по каналу продаж Digital"

**Ожидаемый результат:**
- SQL запрос для выборки данных
- Ссылка на дашборд для детального анализа

## 📁 Структура проекта

```
data_office_agent/
├── homework.py          # ⭐ Основной файл для сдачи (JSON-схема + SOP)
├── demo.py             # Демонстрация работы агента (реальный LLM + fallback)
├── runtime.py          # Регистрация инструментов, JSON-схема и валидация
├── analytics_tools.py  # Реализация инструмента generate_analytics_query
├── sql_generator.py    # Генерация параметризованного SQL запроса
├── dashboards.py       # Маппинг метрик на дашборды
├── real_llm.py         # Вызов инструмента через реальный Anthropic API
├── fake_llm.py         # Эмулятор LLM для запуска без .env/сети
├── db.py               # Работа с базой данных
├── db_schema.sql       # DDL схема БД
├── db_test_data.sql    # Тестовые данные
└── README.md           # Этот файл
```

## 🏗️ Архитектура (по аналогии с minimal-agent-workflow-demo)

### 1. **analytics_tools.py** - Agent Skills
Реализация конкретных инструментов (функций):
- `generate_analytics_query()` - генерирует SQL и возвращает дашборд

### 2. **runtime.py** - Регистрация и выполнение
- `TOOLS` - словарь с определениями инструментов
- `validate()` - валидация параметров по JSON Schema
- `run_tool()` - выполнение инструмента с обработкой ошибок

### 3. **demo.py** - Оркестрация
- `run_agent()` - последовательный вызов LLM → validation → tool execution
- `main()` - демонстрация работы на тестовых запросах

## 📊 Структура данных

### Витрины (Facts)
- **fact_cashflow** - ЧП (чистая прибыль/cashflow)
- **fact_positions** - Позиции/транзакции
- **fact_commissions** - Комиссии

### Справочники (Dimensions)
- **dim_clients** - Клиенты
- **dim_contracts** - Договора
- **dim_sales_channels** - Каналы продаж (Digital, Retail, Corporate, Partner, Mobile App)
- **dim_client_segments** - Сегментация клиентов (VIP, Premium, Standard, Small)

## 🚀 Запуск

### Демонстрация работы
```bash
cd lesson06/hw
python -m data_office_agent.demo
```

### Просмотр SOP и схемы
```bash
python -m data_office_agent.homework
```

## 🧪 Тестовые запросы

1. "получить ЧП за текущий год по каналу продаж Digital"
2. "показать топ-5 клиентов по позициям"
3. "комиссии за 2025 год по сегменту VIP"
4. "выручка по месяцам в 2026 году"

## 🔧 Инструмент: generate_analytics_query

### Параметры

**Обязательные:**
- `metric` - метрика (net_profit, positions, commissions, revenue, clients)
- `period` - период (YYYY или YYYY-MM)

**Опциональные:**
- `sales_channel` - канал продаж
- `client_segment` - сегмент клиентов
- `group_by` - группировка (channel, segment, client, month, none)
- `limit` - лимит записей (по умолчанию 10)

### Результат

```json
{
  "status": "OK",
  "sql": "SELECT ... FROM ... WHERE ... = ?",
  "params": ["2026", "Digital", 10],
  "dashboard": {
    "name": "Дашборд ЧП",
    "url": "https://bi.company.com/dashboards/net-profit",
    "description": "Детальный анализ ЧП"
  },
  "preview": [...],
  "total_rows": 25
}
```

## 📚 Дашборды

- **Дашборд "ЧП"** → https://bi.company.com/dashboards/net-profit
- **Дашборд "Позиции"** → https://bi.company.com/dashboards/positions
- **Дашборд "Комиссии"** → https://bi.company.com/dashboards/commissions
- **Дашборд "Клиенты"** → https://bi.company.com/dashboards/clients

## 🛡️ Безопасность

- ✅ Read-only инструмент (только чтение данных)
- ✅ Параметризованные SQL запросы: `sql_generator.py` возвращает SQL с `?`-плейсхолдерами
  и отдельный список `params`; значения выполняются через `conn.execute(sql, params)`,
  а не подставляются в текст запроса (проверено тестом на инъекцию в `sales_channel`)
- ✅ `sales_channel`/`client_segment` ограничены enum'ом в JSON-схеме — недопустимое
  значение отклоняется валидацией ещё до генерации SQL
- ✅ Валидация всех входных параметров (обязательные поля, типы, формат периода, диапазон limit)
- ✅ Жёсткий потолок `limit` (1000) независимо от того, что запросила модель

## 🔄 Интеграция с LLM

Реализовано 2 варианта, `demo.py` выбирает между ними автоматически:

1. **real_llm.py** — реальный вызов Anthropic API (tool use), если в `.env` заданы
   `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_BASE_URL` / `CERT_PATH` (см. `lesson04/01-single-tool-single-turn.py`)
2. **fake_llm.py** — эмулятор LLM (разбор ключевых слов) как fallback, если `.env`
   не настроен, зависимости не установлены или API недоступен

## 📝 Примеры из урока

Решение использует паттерны из:
- **minimal-agent-workflow-demo** - структура Agent Skills
- **lesson04/02-the-agentic-loop.py** - агентный цикл с LLM
- **lesson06/sql_customer_lookup.py** - работа с SQL

## ✅ Критерии оценки

- [x] Реализован вызов инструмента
- [x] Схема функции валидна (JSON Schema)
- [x] Описан SOP использования
- [x] Добавлена обработка ошибок (validation_error, sql_error, database_error)

## 📦 Файлы для сдачи

**Основной файл:** `homework.py` (содержит код + JSON-схему + SOP в одном файле)

Дополнительные модули для полноты решения в директории `data_office_agent/`
