import sqlite3
from modules.path_resolver import get_candlestick_analysis_db_path

DB_PATH = get_candlestick_analysis_db_path()


def init_candlestick_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # =====================================================
    # PATTERN EVENTS
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pattern_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        timestamp TEXT,

        pattern TEXT,
        direction TEXT,

        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,

        pattern_state TEXT,
        pattern_score REAL,

        created_at TEXT
    )
    """)

    # =====================================================
    # TRADE SETUPS
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trade_setups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        timestamp TEXT,

        pattern TEXT,
        bias TEXT,

        entry TEXT,
        stop TEXT,
        target TEXT,

        entry_price REAL,
        stop_price REAL,
        target_price REAL,

        context TEXT,
        created_at TEXT
    )
    """)

    # =====================================================
    # PATTERN RESULTS
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pattern_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        timestamp TEXT,

        pattern TEXT,
        state TEXT,
        score REAL,
        direction TEXT,

        confirmed INTEGER,
        failed INTEGER,

        next_close REAL,
        follow_through REAL,

        created_at TEXT
    )
    """)

    # =====================================================
    # MTF ALIGNMENT
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mtf_alignment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timestamp TEXT,
        alignment TEXT,

        tf_15m_pattern TEXT,
        tf_1h_pattern TEXT,
        tf_daily_pattern TEXT,

        tf_15m_score REAL,
        tf_1h_score REAL,
        tf_daily_score REAL,

        created_at TEXT
    )
    """)

    # =====================================================
    # STOP EVALUATIONS
    # =====================================================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stop_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        timeframe TEXT,
        timestamp TEXT,

        pattern TEXT,
        direction TEXT,

        stop_price REAL,
        status TEXT,
        breached INTEGER,

        breach_index INTEGER,
        reason TEXT,

        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def init_all():
    init_candlestick_db()