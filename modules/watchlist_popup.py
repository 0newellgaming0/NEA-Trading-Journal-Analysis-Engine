import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import threading
import time
import os
import pandas as pd
from datetime import datetime, timedelta

from modules.path_resolver import (
    get_watchlist_db_path,
    get_webull_db_path,
    get_project_root
)

try:
    import yfinance as yf
except Exception:
    yf = None


# =========================================================
# PATHS (SOURCE OF TRUTH)
# =========================================================

WATCHLIST_DB = get_watchlist_db_path()
WEBULL_DB = get_webull_db_path()

JOURNAL_PATH = os.path.join(get_project_root(), "data", "systemFiles", "journal.csv")

last_mtime = 0
# =========================================================
# WATCHLIST DB (ONLY TICKERS FROM JOURNAL)
# =========================================================

def init_db():
    conn = sqlite3.connect(WATCHLIST_DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()


def db_upsert(ticker):
    conn = sqlite3.connect(WATCHLIST_DB)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO watchlist (ticker)
        VALUES (?)
    """, (ticker.upper(),))

    conn.commit()
    conn.close()


def db_load():
    conn = sqlite3.connect(WATCHLIST_DB)
    cur = conn.cursor()

    cur.execute("SELECT ticker FROM watchlist")
    rows = cur.fetchall()

    conn.close()
    return [r[0] for r in rows]


# =========================================================
# JOURNAL → WATCHLIST (ONLY SOURCE)
# =========================================================

def extract_tickers_from_journal(journal_path=JOURNAL_PATH):
    try:
        df = pd.read_csv(journal_path)

        if "ticker" not in df.columns:
            return []

        return (
            df["ticker"]
            .dropna()
            .astype(str)
            .str.upper()
            .unique()
            .tolist()
        )

    except Exception:
        return []


def sync_watchlist_from_journal():
    tickers = extract_tickers_from_journal()

    for t in tickers:
        db_upsert(t)


def watch_journal_file(app):
    global last_mtime

    if not os.path.exists(JOURNAL_PATH):
        app.after(2000, lambda: watch_journal_file(app))
        return

    try:
        mtime = os.path.getmtime(JOURNAL_PATH)

        if mtime != last_mtime:
            last_mtime = mtime

            # sync journal → DB
            sync_watchlist_from_journal()

            # reload DB
            app.watchlist = db_load()
            app.load_table()
            app.refresh()

    except Exception as e:
        print("watch error:", e)

    app.after(2000, lambda: watch_journal_file(app))
    
# =========================================================
# WEBULL DB (SOURCE OF TRUTH = webull.db ONLY)
# =========================================================

def init_webull_db():
    conn = sqlite3.connect(WEBULL_DB)
    cur = conn.cursor()

    cur.execute("""
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


def load_webull_orders():
    conn = sqlite3.connect(WEBULL_DB)
    cur = conn.cursor()

    cur.execute("SELECT Symbol FROM webull_orders")
    rows = cur.fetchall()

    conn.close()
    return [r[0].upper() for r in rows if r[0]]


# =========================================================
# MARKET SNAPSHOT
# =========================================================

def get_snapshot(ticker):
    if yf is None:
        return None

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")

        if hist is None or len(hist) < 2:
            return None

        last = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2]

        change_pct = ((last - prev) / prev) * 100
        volume = hist["Volume"].iloc[-1]

        return {
            "price": round(float(last), 2),
            "change": round(float(change_pct), 2),
            "volume": int(volume)
        }

    except Exception:
        return None


def get_state(change_pct):
    if change_pct is None:
        return "N/A"
    if change_pct > 2:
        return "MARKUP"
    if change_pct < -2:
        return "MARKDOWN"
    if abs(change_pct) <= 0.5:
        return "ACC/DIST"
    return "TRANSITION"


    
# =========================================================
# WATCHLIST UI
# =========================================================

class WatchlistPopup(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)

        init_db()
        init_webull_db()

        self.parent = parent
        self.running = True

        self.title("Institutional Watchlist (Journal Only Source)")
        self.geometry("820x540")

        self.sort_reverse = False

        self.build_ui()

        # ONLY SOURCE IS JOURNAL FOR WATCHLIST
        sync_watchlist_from_journal()

        self.watchlist = db_load()
        self.load_table()

        self.after(100, self._initial_load)
        self.schedule_auto_refresh()

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(2000, lambda: watch_journal_file(self))

    def schedule_auto_refresh(self):
        now = datetime.now()

        # fixed refresh points (4x daily)
        refresh_hours = (0, 6, 12, 18)

        # find next valid run today
        next_run = None

        for h in refresh_hours:
            candidate = now.replace(hour=h, minute=0, second=0, microsecond=0)
            if candidate > now:
                next_run = candidate
                break

        # if none left today → schedule tomorrow 00:00
        if next_run is None:
            next_run = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        # compute delay safely
        delay_ms = int((next_run - now).total_seconds() * 1000)

        # HARD SAFETY CLAMP (prevents Tkinter scheduling bugs)
        if delay_ms < 1000:
            delay_ms = 1000

        # prevent multiple overlapping timers
        try:
            if hasattr(self, "_refresh_job"):
                self.after_cancel(self._refresh_job)
        except Exception:
            pass

        self._refresh_job = self.after(delay_ms, self._auto_refresh_tick)
        
    def _auto_refresh_tick(self):
        if not self.winfo_exists():
            return

        self.manual_sync()   # refresh DB from journal
        self.refresh()       # refresh UI

        self.schedule_auto_refresh()
    
    def _initial_load(self):
        if not self.winfo_exists():
            return

        # STEP 1: sync journal → DB
        sync_watchlist_from_journal()

        # STEP 2: reload DB state
        self.watchlist = db_load()

        # STEP 3: rebuild table ONCE
        self.load_table()

        # STEP 4: snapshot update
        self.refresh()       

        # Default sort: Percent Change (Highest -> Lowest)
        self.sort_states["change"] = True
        self.sort_by("change")

    # ---------------- UI ----------------
    def build_ui(self):

        header = tk.Frame(self)
        header.pack(fill="x")

        tk.Label(
            header,
            text="WATCHLIST (Journal Source Only)",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10)

        tk.Button(
            header,
            text="SYNC JOURNAL",
            command=self.manual_sync
        ).pack(side="right", padx=5)

        tk.Button(
            header,
            text="REFRESH",
            command=self.refresh
        ).pack(side="right", padx=5)

        columns = (
            "id",
            "ticker",
            "price",
            "change",
            "volume",
            "state"
        )

        self.columns = columns

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings"
        )

        self.tree.pack(
            fill="both",
            expand=True
        )


        for c in columns:

            self.tree.heading(
                c,
                text=c.upper(),
                command=lambda _c=c: self.sort_by(_c)
            )

            self.tree.column(
                c,
                width=120
            )


        # Right click popup
        self.tree.bind(
            "<Button-3>",
            self.show_popup
        )


        self.sort_states = {
            c: False for c in columns
        }

    # ---------------- LOAD ----------------
    def load_table(self):

        self.tree.delete(
            *self.tree.get_children()
        )

        conn = sqlite3.connect(WATCHLIST_DB)

        cur = conn.cursor()

        cur.execute("""
            SELECT id,ticker
            FROM watchlist
            ORDER BY ticker
        """)

        rows = cur.fetchall()

        conn.close()


        for row in rows:

            self.tree.insert(
                "",
                "end",
                values=(
                    row[0],
                    row[1],
                    "-",
                    "-",
                    "-",
                    "-"
                )
            )

    # ---------------- SYNC ----------------
    def manual_sync(self):

        sync_watchlist_from_journal()

        self.watchlist = db_load()

        self.load_table()

        self.refresh()

    # ---------------- REFRESH ----------------
    def refresh(self):
        if not self.winfo_exists():
            return

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            ticker = values[1]

            snap = get_snapshot(ticker)
            if not snap:
                continue

            state = get_state(snap["change"])

            self.tree.item(
                item,
                values=(
                    values[0],          # preserve database id
                    ticker,
                    snap["price"],
                    snap["change"],
                    snap["volume"],
                    state
                )
            )

    # ---------------- SORT ----------------
    def sort_by(self, col):

        items = []

        for item in self.tree.get_children():
            value = self.tree.set(item, col)
            items.append((value, item))

        def convert(value):

            # Handle empty values
            if value in ("", "-", "N/A", None):
                return float("-inf")

            # Numeric columns
            if col in ("id", "price", "change", "volume"):

                try:
                    return float(
                        str(value)
                        .replace(",", "")
                        .replace("%", "")
                        .replace("$", "")
                        .strip()
                    )
                except Exception:
                    return float("-inf")

            # Text columns
            return str(value).lower()

        reverse = self.sort_states[col]

        items.sort(
            key=lambda x: convert(x[0]),
            reverse=reverse
        )

        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

        self.sort_states[col] = not reverse

    # ---------------- POPUP ----------------
        
    def show_popup(self, event):

        row = self.tree.identify_row(event.y)

        if not row:
            return


        self.tree.selection_set(row)


        menu = tk.Menu(
            self,
            tearoff=0
        )


        menu.add_command(
            label="Delete Database Row",
            command=self.delete_selected_row
        )


        menu.post(
            event.x_root,
            event.y_root
        )        
        
    def delete_selected_row(self):

        selected = self.tree.selection()

        if not selected:
            return


        values = self.tree.item(
            selected[0],
            "values"
        )


        row_id = values[0]
        ticker = values[1]


        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete {ticker} from watchlist database?"
        )


        if not confirm:
            return



        conn = sqlite3.connect(
            WATCHLIST_DB
        )

        cur = conn.cursor()


        cur.execute(
            """
            DELETE FROM watchlist
            WHERE id=?
            """,
            (row_id,)
        )


        conn.commit()
        conn.close()



        self.tree.delete(
            selected[0]
        )


        self.watchlist = db_load()        

    # ---------------- CLOSE ----------------
    def close(self):
        self.running = False
        self.destroy()


def open_watchlist(root):
    WatchlistPopup(root)