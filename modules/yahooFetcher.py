import os
import pandas as pd
import yfinance as yf
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import threading
import json
import sqlite3

from modules.path_resolver import (
    get_watchlist_db_path,
    get_webull_db_path,
    get_project_root,
    get_financials_root
)

from modules.stock_data_db.repository import StockDataRepository, FinancialRepository
from modules.stock_data_db.init_db import init_all

init_all()

# =========================================================
# PATH RESOLVER (SOURCE OF TRUTH)
# =========================================================

WATCHLIST_DB = get_watchlist_db_path()
WEBULL_DB = get_webull_db_path()

JOURNAL_FILE = os.path.join(
    get_project_root(),
    "data",
    "systemFiles",
    "journal.csv"
)

OUTPUT_DIR = os.path.join(
    get_project_root(),
    "modules",
    "stock_data"
)

FINANCIALS_DIR = get_financials_root()

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# TIMEFRAMES
# =========================================================

TIMEFRAMES = {
    "daily": {"interval": "1d", "period": "max"},
    "weekly": {"interval": "1wk", "period": "max"},
    "monthly": {"interval": "1mo", "period": "max"},
    "intraday_1m": {"interval": "1m", "period": "7d"},
    "intraday_5m": {"interval": "5m", "period": "60d"},
    "intraday_15m": {"interval": "15m", "period": "60d"},
    "intraday_30m": {"interval": "30m", "period": "60d"},
    "intraday_60m": {"interval": "60m", "period": "730d"},
}

# =========================================================
# GLOBAL UI HOOKS
# =========================================================

dashboard = None
dashboard_log = None

cached_tickers = []
last_journal_mtime = 0

# =========================================================
# LOGGING
# =========================================================

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")

    if dashboard_log is None:
        print(f"[{timestamp}] {msg}")
        return

    def _write():
        dashboard_log.configure(state="normal")
        dashboard_log.insert(tk.END, f"[{timestamp}] {msg}\n")
        dashboard_log.see(tk.END)
        dashboard_log.configure(state="disabled")

    dashboard.after(0, _write)

# =========================================================
# WATCHLIST SOURCE (DB ONLY)
# =========================================================

def load_tickers_from_watchlist():
    try:
        log("🔍 Loading tickers from watchlist DB...")

        if not os.path.exists(WATCHLIST_DB):
            log(f"❌ Watchlist DB not found: {WATCHLIST_DB}")
            return []

        conn = sqlite3.connect(WATCHLIST_DB)
        cur = conn.cursor()

        cur.execute("SELECT ticker FROM watchlist")
        rows = cur.fetchall()

        conn.close()

        tickers = sorted({r[0].strip().upper() for r in rows if r and r[0]})

        log(f"✅ Watchlist loaded ({len(tickers)} tickers)")
        return tickers

    except Exception as e:
        log(f"❌ Watchlist DB error: {e}")
        return []

# =========================================================
# JOURNAL SOURCE (MISSING PIECE)
# =========================================================

def load_tickers_from_journal():
    try:
        log("🔍 Loading tickers from journal...")

        if not os.path.exists(JOURNAL_FILE):
            log("⚠ Journal file missing")
            return []

        df = pd.read_csv(JOURNAL_FILE)

        if "ticker" not in df.columns:
            log("⚠ Journal missing ticker column")
            return []

        tickers = sorted(set(df["ticker"].dropna().astype(str).str.upper()))
        log(f"✅ Journal tickers loaded ({len(tickers)})")
        return tickers

    except Exception as e:
        log(f"❌ Journal load error: {e}")
        return []

def watch_journal_changes():
    global cached_tickers, last_journal_mtime

    try:
        if not os.path.exists(JOURNAL_FILE):
            dashboard.after(2000, watch_journal_changes)
            return

        mtime = os.path.getmtime(JOURNAL_FILE)

        if mtime != last_journal_mtime:
            last_journal_mtime = mtime

            new_tickers = load_tickers_from_journal()

            if set(new_tickers) != set(cached_tickers):
                cached_tickers = new_tickers

                log(f"🔄 Journal updated → {len(new_tickers)} tickers detected")

                threading.Thread(target=_run_update_core, daemon=True).start()

    except Exception as e:
        log(f"Journal watch error: {e}")

    dashboard.after(2000, watch_journal_changes)

# =========================================================
# DATA NORMALIZATION
# =========================================================

def normalize_columns(df):
    try:
        df.columns = [
            "_".join([str(x) for x in col if x]).replace(" ", "_").lower()
            if isinstance(col, tuple)
            else col.replace(" ", "_").lower()
            for col in df.columns
        ]
        return df
    except Exception as e:
        log(f"❌ Column normalization failed: {e}")
        return df

# =========================================================
# DISK CACHE
# =========================================================

def cache_to_disk(ticker, tf_name, df):
    try:
        if df is None or df.empty:
            log(f"⚠ Cache skipped (empty df): {ticker} [{tf_name}]")
            return

        tf_dir = os.path.join(OUTPUT_DIR, tf_name)
        os.makedirs(tf_dir, exist_ok=True)

        file_path = os.path.join(tf_dir, f"{ticker}.csv")

        df.to_csv(file_path, index=False)
        log(f"💾 Cache written: {file_path}")

    except Exception as e:
        log(f"⚠ Cache write failed {ticker} [{tf_name}]: {e}")

# =========================================================
# FINANCIALS
# =========================================================

def fetch_financials(ticker):
    try:
        log(f"📊 Starting financial fetch: {ticker}")

        tk_obj = yf.Ticker(ticker)

        os.makedirs(FINANCIALS_DIR, exist_ok=True)
        base_dir = os.path.join(FINANCIALS_DIR, ticker)
        os.makedirs(base_dir, exist_ok=True)

        metadata = {
            "source": "yahoo_finance",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }

        with open(os.path.join(base_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        def safe_df(df):
            if df is None or df.empty:
                log("⚠ Safe DF skipped empty dataset")
                return None

            df = df.copy()
            df = df.reset_index()

            df.columns = [
                str(c).strip().replace(" ", "_").lower()
                for c in df.columns
            ]

            log(f"📄 Dataset normalized shape={df.shape}")
            return df

        datasets = {
            "income_statement": safe_df(tk_obj.financials),
            "balance_sheet": safe_df(tk_obj.balance_sheet),
            "cashflow": safe_df(tk_obj.cashflow),
            "quarterly_income": safe_df(tk_obj.quarterly_financials),
            "quarterly_balance": safe_df(tk_obj.quarterly_balance_sheet),
            "quarterly_cashflow": safe_df(tk_obj.quarterly_cashflow),
        }

        repo = FinancialRepository()
        saved = 0

        for name, df in datasets.items():
            if df is None:
                log(f"⚠ Skipping {name} (None)")
                continue

            repo.insert_statement(ticker, name, df)
            log(f"🧠 DB write success: {name}")

            csv_path = os.path.join(base_dir, f"{name}.csv")
            df.to_csv(csv_path, index=False)

            log(f"💾 CSV saved: {csv_path}")
            saved += 1

        log(f"📊 {ticker} financials saved ({saved}/6) [DB + CSV]")
        return True

    except Exception as e:
        log(f"❌ Financial error {ticker}: {e}")
        return False

# =========================================================
# DATA INGESTION
# =========================================================

def append_new_data(ticker, tf_name, cfg):
    try:
        log(f"📡 Fetching {ticker} [{tf_name}]...")

        repo = StockDataRepository()

        df_new = yf.download(
            ticker,
            interval=cfg["interval"],
            period=cfg["period"],
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df_new is None or df_new.empty:
            log(f"⚠ No data returned: {ticker} [{tf_name}]")
            return False

        log(f"📥 Raw data received: {ticker} [{tf_name}] shape={df_new.shape}")

        df_new.reset_index(inplace=True)
        df_new = normalize_columns(df_new)

        log(f"🔧 Normalized data: {ticker} [{tf_name}] shape={df_new.shape}")

        repo.insert_ohlcv_df(ticker, tf_name, df_new)
        repo.log_ingestion(ticker, tf_name, len(df_new), "success")

        log(f"🧠 DB write complete: {ticker} [{tf_name}]")

        cache_to_disk(ticker, tf_name, df_new)

        log(f"✔ Completed: {ticker} [{tf_name}] ({len(df_new)})")

        return True

    except Exception as e:
        log(f"❌ {ticker} [{tf_name}] error: {e}")
        return False

# =========================================================
# CORE ENGINE
# =========================================================

def _run_update_core():
    log("🚀 Full update started...")

    tickers = load_tickers_from_watchlist()
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        log(f"📊 Processing {ticker} ({i}/{total})")

        for tf_name, cfg in TIMEFRAMES.items():
            append_new_data(ticker, tf_name, cfg)

        fetch_financials(ticker)

    log("✅ Full update complete")

def _run_update_single(ticker):
    log(f"🚀 Single update: {ticker}")

    for tf_name, cfg in TIMEFRAMES.items():
        append_new_data(ticker, tf_name, cfg)

    fetch_financials(ticker)

    log(f"✅ Done: {ticker}")

# =========================================================
# UI ENTRY
# =========================================================

def run_update():
    try:
        tickers = load_tickers_from_watchlist()

        if not tickers:
            log("No tickers found in watchlist DB")
            return

        preview = tk.Toplevel(dashboard)
        preview.title("Update Preview")
        preview.geometry("520x520")

        tk.Label(preview, text=f"{len(tickers)} tickers ready",
                 font=("Arial", 12, "bold")).pack(pady=10)

        box = tk.Listbox(preview)
        for t in tickers:
            box.insert(tk.END, t)
        box.pack(fill=tk.BOTH, expand=True)

        def start_all():
            preview.destroy()
            threading.Thread(target=_run_update_core, daemon=True).start()

        def start_single():
            sel = box.curselection()
            if not sel:
                log("⚠ No ticker selected")
                return
            ticker = box.get(sel[0])
            preview.destroy()
            threading.Thread(target=_run_update_single, args=(ticker,), daemon=True).start()

        btn = tk.Frame(preview)
        btn.pack()

        tk.Button(btn, text="ALL", command=start_all).pack(side=tk.LEFT)
        tk.Button(btn, text="SELECT", command=start_single).pack(side=tk.LEFT)
        tk.Button(btn, text="CLOSE", command=preview.destroy).pack(side=tk.LEFT)

    except Exception as e:
        log(f"Preview error: {e}")

# =========================================================
# MAIN UI
# =========================================================

def main():
    global dashboard, dashboard_log

    dashboard = tk.Tk()
    dashboard.title("Stock Data Downloader (DB-Driven)")
    dashboard.geometry("950x700")

    ttk.Label(dashboard, text="Stock Downloader", font=("Arial", 18)).pack(pady=10)

    ttk.Button(dashboard, text="Update Data", command=run_update).pack(pady=5)

    dashboard_log = scrolledtext.ScrolledText(dashboard, height=30)
    dashboard_log.pack(fill=tk.BOTH, expand=True)

    dashboard.after(2000, watch_journal_changes)

    dashboard.mainloop()


if __name__ == "__main__":
    main()