import sqlite3
from modules.path_resolver import (
    get_watchlist_db_path,
    get_webull_db_path,
    get_stock_db_path,
    get_financial_db_path,
    get_ingestion_db_path,
    get_sec_analysis_db_path
)

from modules.stock_data_db.sec_financials_db.init_sec_db import (
    init_sec_db
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
# SEC ANALYSIS DB
# =========================================================

def init_sec_analysis_db():
    conn = sqlite3.connect(get_sec_analysis_db_path())
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_summary (
        ticker TEXT PRIMARY KEY,
        analysis_date TEXT,
        institutional_score REAL,
        growth_asymmetry_score REAL,
        classification TEXT,
        liquidity_score REAL,
        financial_risk TEXT,
        revenue_acceleration TEXT,
        earnings_growth REAL,
        earnings_trend TEXT,
        revenue_cagr_3 REAL,
        revenue_cagr_5 REAL,
        earnings_cagr_3 REAL,
        earnings_cagr_5 REAL,
        growth_quality TEXT,
        growth_quality_score REAL,
        float_category TEXT,
        float_scarcity TEXT,
        dilution_state TEXT,
        float_score REAL,
        share_supply_direction TEXT,
        ownership_trend TEXT,
        dilution_risk TEXT,
        capital_structure TEXT,
        capital_efficiency TEXT,
        allocation_sustainability TEXT,
        capital_allocation_score REAL,
        canslim_classification TEXT,
        canslim_score REAL,
        institutional_sponsorship TEXT,
        json_report TEXT
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_sec_analysis
    ON analysis_summary (ticker)
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
    init_sec_db()
    init_sec_analysis_db() 

    print(
        "NEA28 database initialization complete."
    )