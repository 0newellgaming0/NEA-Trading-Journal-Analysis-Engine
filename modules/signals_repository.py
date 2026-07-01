import sqlite3
import json
from datetime import datetime


class SignalsRepository:

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.init_table()

    def init_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ticker TEXT,
            timeframe TEXT,
            module TEXT,

            detected INTEGER,
            detected_date TEXT,
            direction TEXT,
            event_type TEXT,
            status TEXT,
            resolved_date TEXT,
            bars_active INTEGER,
            high REAL,
            low REAL,
            trade_type TEXT,

            entry REAL,
            stop REAL,
            wick_stop REAL,
            target1 REAL,
            target2 REAL,
            failure_condition TEXT,

            state TEXT,
            regime TEXT,

            timestamp TEXT,
            created_at TEXT
        )
        """)

        self.conn.commit()

    def insert_signal(
        self,
        ticker,
        timeframe,
        module,

        detected,
        detected_date,
        direction,
        event_type,
        status,
        resolved_date,
        bars_active,
        high,
        low,
        trade_type,

        entry,
        stop,
        wick_stop,
        target1,
        target2,
        failure_condition,

        state,
        regime,

        timestamp
    ):

        created_at = datetime.utcnow().isoformat()

        self.cursor.execute("""
        INSERT INTO signals (
            ticker,
            timeframe,
            module,

            detected,
            detected_date,
            direction,
            event_type,
            status,
            resolved_date,
            bars_active,
            high,
            low,
            trade_type,

            entry,
            stop,
            wick_stop,
            target1,
            target2,
            failure_condition,

            state,
            regime,

            timestamp,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timeframe,
            module,

            detected,
            detected_date,
            direction,
            event_type,
            status,
            resolved_date,
            bars_active,
            high,
            low,
            trade_type,

            entry,
            stop,
            wick_stop,
            target1,
            target2,
            failure_condition,

            state,
            regime,

            timestamp,
            created_at
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()