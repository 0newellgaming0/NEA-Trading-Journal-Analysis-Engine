import sqlite3
from datetime import datetime
import os

DB_PATH = os.path.join("data", "journal.db")


def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        ticker TEXT,
        account REAL,
        risk_dollar REAL,
        stop REAL,

        ladder_1_price REAL,
        ladder_1_shares REAL,
        ladder_1_total REAL,

        ladder_2_price REAL,
        ladder_2_shares REAL,
        ladder_2_total REAL,

        ladder_3_price REAL,
        ladder_4_price REAL,

        buy_now_price REAL,
        buy_now_shares REAL,
        buy_now_total REAL,

        trade_notes TEXT,
        analysis_notes TEXT,
        management_notes TEXT
    )
    """)

    conn.commit()
    conn.close()