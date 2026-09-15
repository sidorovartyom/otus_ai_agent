"""Модуль для работы с базой данных Data Office"""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "data_office.db"
SCHEMA_PATH = Path(__file__).parent / "db_schema.sql"
DATA_PATH = Path(__file__).parent / "db_test_data.sql"


def init_database() -> None:
    """Инициализирует БД схемой и тестовыми данными"""
    # Удаляем старую БД если есть
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    # Загружаем схему
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)

    # Загружаем тестовые данные
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data_sql = f.read()
    conn.executescript(data_sql)

    conn.commit()
    conn.close()
    print(f"✅ База данных инициализирована: {DB_PATH}")


def get_db_connection() -> sqlite3.Connection:
    """Возвращает подключение к БД"""
    if not DB_PATH.exists():
        init_database()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
