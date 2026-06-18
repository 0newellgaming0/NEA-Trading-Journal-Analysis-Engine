CREATE TABLE IF NOT EXISTS ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT,
    timeframe TEXT,
    action TEXT,

    rows_added INTEGER,
    status TEXT,

    timestamp TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingestion_ticker
ON ingestion_log (ticker);