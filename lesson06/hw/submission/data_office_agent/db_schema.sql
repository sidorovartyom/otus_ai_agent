-- Data Office - Схема БД для аналитики
-- Создание таблиц витрин и справочников

-- Справочник: Каналы продаж
CREATE TABLE IF NOT EXISTS dim_sales_channels (
    channel_id INTEGER PRIMARY KEY,
    channel_name TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL CHECK(channel_type IN ('Online', 'Offline', 'Hybrid')),
    is_active INTEGER DEFAULT 1
);

-- Справочник: Сегментация клиентов
CREATE TABLE IF NOT EXISTS dim_client_segments (
    segment_id INTEGER PRIMARY KEY,
    segment_name TEXT NOT NULL UNIQUE,
    segment_description TEXT,
    min_revenue REAL,
    max_revenue REAL
);

-- Справочник: Клиенты
CREATE TABLE IF NOT EXISTS dim_clients (
    client_id INTEGER PRIMARY KEY,
    client_name TEXT NOT NULL,
    segment_id INTEGER,
    registration_date DATE,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (segment_id) REFERENCES dim_client_segments(segment_id)
);

-- Справочник: Договора
CREATE TABLE IF NOT EXISTS dim_contracts (
    contract_id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    contract_number TEXT NOT NULL UNIQUE,
    channel_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    contract_status TEXT CHECK(contract_status IN ('Active', 'Closed', 'Suspended')),
    FOREIGN KEY (client_id) REFERENCES dim_clients(client_id),
    FOREIGN KEY (channel_id) REFERENCES dim_sales_channels(channel_id)
);

-- Витрина: Позиции (продажи/транзакции)
CREATE TABLE IF NOT EXISTS fact_positions (
    position_id INTEGER PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    position_date DATE NOT NULL,
    product_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_price REAL NOT NULL,
    total_amount REAL NOT NULL,
    cost_amount REAL NOT NULL,
    FOREIGN KEY (contract_id) REFERENCES dim_contracts(contract_id)
);

-- Витрина: ЧП (Чистая прибыль / Cash Flow)
CREATE TABLE IF NOT EXISTS fact_cashflow (
    cashflow_id INTEGER PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    period_date DATE NOT NULL,
    revenue REAL NOT NULL,
    costs REAL NOT NULL,
    net_profit REAL NOT NULL,
    period_type TEXT CHECK(period_type IN ('Daily', 'Monthly', 'Yearly')),
    FOREIGN KEY (contract_id) REFERENCES dim_contracts(contract_id)
);

-- Витрина: Комиссии
CREATE TABLE IF NOT EXISTS fact_commissions (
    commission_id INTEGER PRIMARY KEY,
    contract_id INTEGER NOT NULL,
    commission_date DATE NOT NULL,
    commission_type TEXT NOT NULL,
    base_amount REAL NOT NULL,
    commission_rate REAL NOT NULL,
    commission_amount REAL NOT NULL,
    FOREIGN KEY (contract_id) REFERENCES dim_contracts(contract_id)
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_positions_date ON fact_positions(position_date);
CREATE INDEX IF NOT EXISTS idx_positions_contract ON fact_positions(contract_id);
CREATE INDEX IF NOT EXISTS idx_cashflow_date ON fact_cashflow(period_date);
CREATE INDEX IF NOT EXISTS idx_cashflow_contract ON fact_cashflow(contract_id);
CREATE INDEX IF NOT EXISTS idx_commissions_date ON fact_commissions(commission_date);
CREATE INDEX IF NOT EXISTS idx_commissions_contract ON fact_commissions(contract_id);
CREATE INDEX IF NOT EXISTS idx_contracts_channel ON dim_contracts(channel_id);
CREATE INDEX IF NOT EXISTS idx_clients_segment ON dim_clients(segment_id);
