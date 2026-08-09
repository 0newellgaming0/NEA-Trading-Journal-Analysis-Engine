import sqlite3
from pathlib import Path


class DatabaseReader:
    def __init__(self, trades_db_path):
        self.trades_db_path = Path(trades_db_path)

    def _connect(self):
        if not self.trades_db_path.exists():
            return None

        try:
            conn = sqlite3.connect(
                str(self.trades_db_path)
            )
            conn.row_factory = sqlite3.Row
            return conn
        except (sqlite3.Error, OSError):
            return None

    def _table_exists(self, conn, table_name):
        try:
            row = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                AND name = ?
                LIMIT 1
                """,
                (table_name,)
            ).fetchone()

            return row is not None

        except sqlite3.Error:
            return False

    def read_trades(self):
        conn = self._connect()

        if not conn:
            return []

        try:
            if not self._table_exists(conn, "trades"):
                return []

            rows = conn.execute(
                """
                SELECT *
                FROM trades
                ORDER BY
                    CASE
                        WHEN score IS NULL THEN 1
                        ELSE 0
                    END,
                    score DESC,
                    id DESC
                """
            ).fetchall()

            return [dict(row) for row in rows]

        except sqlite3.Error:
            return []

        finally:
            conn.close()