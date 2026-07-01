import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
from datetime import datetime
import threading

from modules.candlestick_state_engine import CandlestickInstitutionalStateEngine
from modules.signals_repository import SignalsRepository
from modules.path_resolver import get_signals_db_path
from modules.stock_data_db.repository import StockDataRepository



# =========================================================
# DB ACCESS
# =========================================================

DB_PATH = get_signals_db_path()

def update_signal_field(signal_id, field, value):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = f"UPDATE signals SET {field} = ? WHERE id = ?"
    cur.execute(query, (value, signal_id))

    conn.commit()
    conn.close()
    
def load_signals(filters=None):

    conn = sqlite3.connect(DB_PATH)

    query = "SELECT * FROM signals WHERE 1=1"
    params = []

    if filters:

        ticker = filters.get("ticker")
        if ticker:
            query += " AND ticker LIKE ?"
            params.append(f"%{ticker}%")

        module = filters.get("module")
        if module:
            query += " AND module LIKE ?"
            params.append(f"%{module}%")

        status = filters.get("status")
        if status:
            query += " AND status LIKE ?"
            params.append(f"%{status}%")

        direction = filters.get("direction")
        if direction:
            query += " AND direction LIKE ?"
            params.append(f"%{direction}%")

        date = filters.get("date")
        if date:
            query += " AND detected_date LIKE ?"
            params.append(f"%{date}%")

    query += " ORDER BY timestamp DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def update_signal_field(signal_id, field, value):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = f"UPDATE signals SET {field} = ? WHERE id = ?"
    cur.execute(query, (value, signal_id))

    conn.commit()
    conn.close()


# =========================================================
# POPUP
# =========================================================

class SignalsPopup(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Signals Database Viewer")
        self.geometry("1400x700")

        self.sort_reverse = False
        self.df = None

        self.columns = [
            "id",
            "ticker",
            "timeframe",
            "module",

            "detected",
            "detected_date",
            "direction",
            "event_type",
            "status",
            "resolved_date",
            "bars_active",
            "high",
            "low",
            "trade_type",

            "entry",
            "stop",
            "wick_stop",
            "target1",
            "target2",
            "failure_condition",

            "state",
            "regime",
            "timestamp",
            "created_at"
        ]

        self.build_ui()
        self.refresh()

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        header = tk.Frame(self)
        header.pack(fill="x")

        tk.Label(
            header,
            text="SIGNALS DATABASE (Editable / Sortable)",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        # =====================================================
        # FILTER TOOLBAR (NEW)
        # =====================================================
        self.filter_ticker = tk.StringVar()
        self.filter_module = tk.StringVar()
        self.filter_status = tk.StringVar()
        self.filter_direction = tk.StringVar()
        self.filter_date = tk.StringVar()

        toolbar = tk.Frame(header)
        toolbar.pack(side="left", padx=10)

        # ---- TICKER ----
        tk.Label(toolbar, text="Ticker").grid(row=0, column=0, padx=3)
        tk.Entry(toolbar, textvariable=self.filter_ticker, width=10).grid(row=0, column=1, padx=3)

        # ---- MODULE ----
        tk.Label(toolbar, text="Module").grid(row=0, column=2, padx=3)
        tk.Entry(toolbar, textvariable=self.filter_module, width=12).grid(row=0, column=3, padx=3)

        # ---- STATUS ----
        tk.Label(toolbar, text="Status").grid(row=0, column=4, padx=3)
        tk.Entry(toolbar, textvariable=self.filter_status, width=10).grid(row=0, column=5, padx=3)

        # ---- DIRECTION ----
        tk.Label(toolbar, text="Direction").grid(row=0, column=6, padx=3)
        tk.Entry(toolbar, textvariable=self.filter_direction, width=10).grid(row=0, column=7, padx=3)

        # ---- DATE ----
        tk.Label(toolbar, text="Date").grid(row=0, column=8, padx=3)
        tk.Entry(toolbar, textvariable=self.filter_date, width=12).grid(row=0, column=9, padx=3)

        tk.Button(
            header,
            text="FILTER",
            command=self.refresh
        ).pack(side="left", padx=5)

        tk.Button(
            header,
            text="CLEAR",
            command=self.clear_filters
        ).pack(side="left", padx=5)
        
        tk.Button(
            header,
            text="FULL SYSTEM",
            bg="#1f6feb",
            fg="white",
            command=self.run_full_system_thread
        ).pack(side="right", padx=5)        

        tk.Button(
            header,
            text="REFRESH",
            command=self.refresh
        ).pack(side="right", padx=5)
        
        # =====================================================
        # TREEVIEW (MISSING IN CURRENT CODE)
        # =====================================================
        self.tree = ttk.Treeview(self, columns=self.columns, show="headings")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        for c in self.columns:
            self.tree.heading(
                c,
                text=c.upper(),
                command=lambda _c=c: self.sort_by(_c)
            )
            self.tree.column(c, width=120, anchor="center")

        self.tree.bind("<Double-1>", self.on_edit)        

    # =====================================================
    # LOAD DATA
    # =====================================================

    def refresh(self):

        filters = {
            "ticker": self.filter_ticker.get().strip(),
            "module": self.filter_module.get().strip(),
            "status": self.filter_status.get().strip(),
            "direction": self.filter_direction.get().strip(),
            "date": self.filter_date.get().strip()
        }

        # remove empty + placeholder values
        filters = {
            k: v for k, v in filters.items()
            if v and v not in ["TICKER", "MODULE", "STATUS", "DIR", "DATE"]
        }

        self.df = load_signals(filters)

        self.tree.delete(*self.tree.get_children())

        for _, row in self.df.iterrows():
            values = [row.get(c, "") for c in self.columns]
            self.tree.insert("", "end", values=values)

    # =====================================================
    # SORTING
    # =====================================================

    def sort_by(self, col):

        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]


        def convert(v):
            try:
                return float(v)
            except:
                return v

        items.sort(key=lambda x: convert(x[0]), reverse=self.sort_reverse)

        for i, (_, k) in enumerate(items):
            self.tree.move(k, "", i)

        self.sort_reverse = not self.sort_reverse

    # =====================================================
    # EDITING
    # =====================================================

    def on_edit(self, event):

        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not item or not col:
            return

        col_index = int(col.replace("#", "")) - 1
        field = self.columns[col_index]

        old_value = self.tree.item(item, "values")[col_index]

        x, y, w, h = self.tree.bbox(item, col)

        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, old_value)
        entry.focus()

        def save(event=None):
            new_value = entry.get()
            entry.destroy()

            values = list(self.tree.item(item, "values"))
            values[col_index] = new_value
            self.tree.item(item, values=values)

            signal_id = values[0]  # id column

            try:
                update_signal_field(signal_id, field, new_value)
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

        entry.bind("<Return>", save)
        entry.bind("<FocusOut>", lambda e: save())

    def clear_filters(self):

        self.filter_ticker.set("")
        self.filter_module.set("")
        self.filter_status.set("")
        self.filter_direction.set("")
        self.filter_date.set("")

        self.refresh()
        
    def run_full_system_thread(self):
        threading.Thread(
            target=run_full_signal_engine_system,
            daemon=True
        ).start()        
    
    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):
        self.destroy()

def run_full_signal_engine_system():

    db_path = get_signals_db_path()
    signals_repo = SignalsRepository(db_path)
    stock_repo = StockDataRepository()

    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT DISTINCT ticker FROM signals", conn)
    conn.close()

    tickers = df["ticker"].dropna().unique().tolist()

    print(f"🚀 FULL SIGNAL ENGINE START ({len(tickers)} tickers)")

    for i, ticker in enumerate(tickers, 1):

        try:
            print(f"📊 [{i}/{len(tickers)}] Running engine: {ticker}")

            # =====================================================
            # FIXED: LOAD MARKET DATA FROM STOCK REPOSITORY
            # =====================================================
            market_df = stock_repo.load_ohlcv_df(
                ticker,
                timeframe="daily",
                limit=600
            )

            if market_df is None or market_df.empty:
                print(f"⚠ No OHLCV data for {ticker}")
                continue

            engine = CandlestickInstitutionalStateEngine(
                ticker=ticker,
                event_store={},
                signals_repo=signals_repo
            )

            engine.run(market_df)

        except Exception as e:
            print(f"❌ ERROR {ticker}: {e}")

    print("✅ FULL SIGNAL ENGINE COMPLETE")
    
# =========================================================
# LAUNCHER
# =========================================================

def open_signals_popup(root):
    SignalsPopup(root)