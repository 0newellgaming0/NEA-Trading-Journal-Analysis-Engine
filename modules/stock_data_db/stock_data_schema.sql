CREATE TABLE IF NOT EXISTS ohlcv_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,

    timestamp TEXT NOT NULL,

    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume REAL,

    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_stock_lookup
ON ohlcv_data (ticker, timeframe, timestamp);