import sqlite3
import json
from datetime import datetime

from modules.path_resolver import (
    get_stock_db_path,
    get_financial_db_path,
    get_ingestion_db_path,
    get_webull_db_path,
    get_watchlist_db_path
)

# =========================================================
# DATABASE PATHS
# =========================================================

STOCK_DB_PATH = get_stock_db_path()
FIN_DB_PATH = get_financial_db_path()
LOG_DB_PATH = get_ingestion_db_path()
WATCHLIST_DB_PATH = get_watchlist_db_path()
WEBULL_DB_PATH = get_webull_db_path()


# =========================================================
# STOCK DATA REPOSITORY
# =========================================================

class StockDataRepository:

    def __init__(self):
        self.conn = sqlite3.connect(STOCK_DB_PATH)
        self.cursor = self.conn.cursor()

        self.log_conn = sqlite3.connect(LOG_DB_PATH)
        self.log_cursor = self.log_conn.cursor()

    def insert_ohlcv_df(self, ticker, timeframe, df):

        created_at = datetime.utcnow().isoformat()

        for _, row in df.iterrows():

            timestamp = (
                row.get("datetime")
                or row.get("date")
                or created_at
            )

            self.cursor.execute("""
                INSERT INTO ohlcv_data (
                    ticker,
                    timeframe,
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    adj_close,
                    volume,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                timeframe,
                str(timestamp),
                row.get("open"),
                row.get("high"),
                row.get("low"),
                row.get("close"),
                row.get("adj_close"),
                row.get("volume"),
                created_at
            ))

        self.conn.commit()

    def log_ingestion(self, ticker, timeframe, rows_added, status):

        self.log_cursor.execute("""
            INSERT INTO ingestion_log (
                ticker,
                timeframe,
                action,
                rows_added,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            timeframe,
            "ohlcv_update",
            rows_added,
            status,
            datetime.utcnow().isoformat()
        ))

        self.log_conn.commit()

    def close(self):
        self.conn.close()
        self.log_conn.close()


# =========================================================
# FINANCIAL REPOSITORY
# =========================================================

class FinancialRepository:

    def __init__(self):
        self.conn = sqlite3.connect(FIN_DB_PATH)
        self.cursor = self.conn.cursor()

    def insert_statement(self, ticker, statement_type, df):

        if df is None or df.empty:
            return

        self.cursor.execute("""
            INSERT INTO financial_statements (
                ticker,
                statement_type,
                data_json,
                period,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            ticker,
            statement_type,
            json.dumps(df.to_dict()),
            "latest",
            datetime.utcnow().isoformat()
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()


# =========================================================
# WATCHLIST REPOSITORY
# =========================================================

class WatchlistRepository:

    def __init__(self):
        self.conn = sqlite3.connect(WATCHLIST_DB_PATH)
        self.cursor = self.conn.cursor()

    def init_table(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE
        )
        """)

        self.conn.commit()

    def add_ticker(self, ticker):

        self.cursor.execute("""
        INSERT OR IGNORE INTO watchlist (ticker)
        VALUES (?)
        """, (ticker.upper(),))

        self.conn.commit()

    def add_tickers(self, tickers):

        rows = [
            (str(t).upper(),)
            for t in tickers
            if t
        ]

        self.cursor.executemany("""
        INSERT OR IGNORE INTO watchlist (ticker)
        VALUES (?)
        """, rows)

        self.conn.commit()

    def get_all(self):

        self.cursor.execute("""
        SELECT ticker
        FROM watchlist
        ORDER BY ticker
        """)

        return [row[0] for row in self.cursor.fetchall()]

    def clear(self):

        self.cursor.execute("DELETE FROM watchlist")
        self.conn.commit()

    def close(self):
        self.conn.close()


# =========================================================
# WEBULL ORDERS REPOSITORY
# =========================================================

class WebullOrdersRepository:

    def __init__(self):
        self.conn = sqlite3.connect(WEBULL_DB_PATH)
        self.cursor = self.conn.cursor()

    def init_table(self):

        self.cursor.execute("""
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

        self.conn.commit()

    def replace_all(self, df):

        if df is None or df.empty:
            return

        self.cursor.execute("DELETE FROM webull_orders")

        for _, row in df.iterrows():

            self.cursor.execute("""
                INSERT INTO webull_orders (
                    Name,
                    Symbol,
                    Side,
                    Status,
                    Filled,
                    total_qty,
                    Price,
                    avg_price,
                    time_in_force,
                    placed_time,
                    filled_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("Name"),
                row.get("Symbol"),
                row.get("Side"),
                row.get("Status"),
                row.get("Filled"),
                row.get("Total Qty"),
                row.get("Price"),
                row.get("Avg Price"),
                row.get("Time-in-Force"),
                row.get("Placed Time"),
                row.get("Filled Time")
            ))

        self.conn.commit()

    def get_all(self):

        self.cursor.execute("""
        SELECT *
        FROM webull_orders
        """)

        return self.cursor.fetchall()

    def close(self):
        self.conn.close()