import sqlite3
import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "trading.db"
)


class BrokerImporter:

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()

    # =====================================================
    # MAIN ENTRY POINT (CALL THIS FROM BUTTON)
    # =====================================================
    def import_webull_csv(self, root=None):

        # -----------------------------
        # CONFIRMATION POPUP
        # -----------------------------
        confirm = messagebox.askyesno(
            "Import Webull Trades",
            "Import Webull executed trades CSV?\n\nThis will deduplicate and sync broker_trades."
        )

        if not confirm:
            return

        file_path = filedialog.askopenfilename(
            title="Select Webull Trades CSV",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not file_path:
            return

        df = pd.read_csv(file_path)

        inserted_count = 0
        linked_count = 0

        for _, row in df.iterrows():

            symbol = str(row["Symbol"]).strip()
            placed_time = str(row["Placed Time"]).strip()
            filled_time = str(row["Filled Time"]).strip()

            # =====================================================
            # 1. DEDUPLICATION CHECK
            # =====================================================
            self.cur.execute("""
                SELECT id FROM broker_trades
                WHERE symbol = ?
                AND placed_time = ?
                AND filled_time = ?
                LIMIT 1
            """, (symbol, placed_time, filled_time))

            exists = self.cur.fetchone()

            if exists:
                continue

            # =====================================================
            # 2. INSERT BROKER TRADE
            # =====================================================
            self.cur.execute("""
                INSERT INTO broker_trades (
                    name, symbol, side, status,
                    filled_qty, total_qty,
                    price, avg_price,
                    time_in_force,
                    placed_time, filled_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["Name"],
                symbol,
                row["Side"],
                row["Status"],
                row["Filled"],
                row["Total Qty"],
                self._clean_price(row["Price"]),
                self._clean_price(row["Avg Price"]),
                row["Time-in-Force"],
                placed_time,
                filled_time
            ))

            broker_id = self.cur.lastrowid
            inserted_count += 1

            # =====================================================
            # 3. AUTO-LINK TO STRATEGY TRADES
            # =====================================================
            self.cur.execute("""
                SELECT id FROM trades
                WHERE ticker = ?
                ORDER BY id DESC
                LIMIT 1
            """, (symbol,))

            trade = self.cur.fetchone()

            if trade:
                trade_id = trade[0]

                self.cur.execute("""
                    UPDATE trades
                    SET broker_trade_id = ?
                    WHERE id = ?
                """, (broker_id, trade_id))

                linked_count += 1

        self.conn.commit()

        messagebox.showinfo(
            "Import Complete",
            f"Inserted: {inserted_count} broker trades\nLinked: {linked_count} strategy trades"
        )

    # =====================================================
    # CLEAN PRICE (handles @ symbols)
    # =====================================================
    def _clean_price(self, value):
        if pd.isna(value):
            return None
        return float(str(value).replace("@", "").strip())