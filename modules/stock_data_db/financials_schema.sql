CREATE TABLE IF NOT EXISTS financial_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,
    statement_type TEXT NOT NULL,

    data_json TEXT NOT NULL,

    period TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_fin_ticker
ON financial_statements (ticker);