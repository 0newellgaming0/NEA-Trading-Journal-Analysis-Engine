import sqlite3
from modules.path_resolver import (
    get_watchlist_db_path,
    get_webull_db_path,
    get_stock_db_path,
    get_financial_db_path,
    get_ingestion_db_path
)


# =========================================================
# STOCK DATA DB (OHLCV)
# =========================================================

def init_stock_db():
    conn = sqlite3.connect(get_stock_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ohlcv_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        timestamp TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        adj_close REAL,
        volume REAL,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_stock_lookup
    ON ohlcv_data (ticker, timeframe, timestamp)
    """)

    conn.commit()
    conn.close()


# =========================================================
# FINANCIALS DB
# =========================================================

def init_financial_db():
    conn = sqlite3.connect(get_financial_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financial_statements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        statement_type TEXT,
        data_json TEXT,
        period TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================================================
# INGESTION LOG DB
# =========================================================

def init_log_db():
    conn = sqlite3.connect(get_ingestion_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        action TEXT,
        rows_added INTEGER,
        status TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================================================
# WATCHLIST DB
# =========================================================

def init_watchlist_db():
    conn = sqlite3.connect(get_watchlist_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()


# =========================================================
# WEBULL DB
# =========================================================

def init_webull_db():
    conn = sqlite3.connect(get_webull_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webull_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Symbol TEXT,
        Side TEXT,
        Status TEXT,
        Filled TEXT,
        total_qty REAL,
        Price REAL,
        avg_price REAL,
        time_in_force TEXT,
        placed_time TEXT,
        filled_time TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================================================
# MASTER INIT
# =========================================================

def init_all():
    init_stock_db()
    init_financial_db()
    init_log_db()
    init_watchlist_db()
    init_webull_db()