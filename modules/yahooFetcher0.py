import os
import pandas as pd
import yfinance as yf
import tkinter as tk
import webbrowser
from tkinter import ttk, scrolledtext
from datetime import datetime
import csv
import threading
import json

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

JOURNAL_FILE = os.path.join(PROJECT_ROOT, "journal.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "modules", "stock_data")
FINANCIALS_DIR = os.path.join(PROJECT_ROOT, "financials")

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

# =========================================================
# SETUP
# =========================================================
def ensure_output_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(FINANCIALS_DIR, exist_ok=True)

    for tf in TIMEFRAMES:
        os.makedirs(os.path.join(OUTPUT_DIR, tf), exist_ok=True)

ensure_output_dirs()

# =========================================================
# SAFE LOGGING
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
# JOURNAL
# =========================================================
def load_tickers_from_journal():
    if not os.path.exists(JOURNAL_FILE):
        return []

    tickers = set()

    with open(JOURNAL_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("ticker", "").strip().upper()
            if t:
                tickers.add(t)

    return sorted(tickers)

# =========================================================
# CLEAN DATA
# =========================================================
def normalize_columns(df):
    df.columns = [
        "_".join([str(x) for x in col if x]).replace(" ", "_").lower()
        if isinstance(col, tuple)
        else col.replace(" ", "_").lower()
        for col in df.columns
    ]
    return df

# =========================================================
# FUNDAMENTALS
# =========================================================
def fetch_financials(ticker):
    try:
        tk_obj = yf.Ticker(ticker)

        base_dir = os.path.join(FINANCIALS_DIR, ticker)
        os.makedirs(base_dir, exist_ok=True)

        metadata = {
            "source": "yahoo_finance",
            "ticker": ticker,
            "timestamp": datetime.now().isoformat()
        }

        meta_path = os.path.join(base_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        def safe_df(df):
            if df is None or df.empty:
                return None
            df = df.copy().reset_index()
            df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
            return df

        datasets = {
            "income_statement.csv": safe_df(tk_obj.financials),
            "balance_sheet.csv": safe_df(tk_obj.balance_sheet),
            "cashflow.csv": safe_df(tk_obj.cashflow),
            "quarterly_income.csv": safe_df(tk_obj.quarterly_financials),
            "quarterly_balance.csv": safe_df(tk_obj.quarterly_balance_sheet),
            "quarterly_cashflow.csv": safe_df(tk_obj.quarterly_cashflow),
        }

        saved = 0
        for filename, df in datasets.items():
            if df is not None:
                path = os.path.join(base_dir, filename)
                df.to_csv(path, index=False)
                saved += 1

        log(f"📊 {ticker} financials saved ({saved}/6 tables)")
        return True

    except Exception as e:
        log(f"❌ Financial fetch error for {ticker}: {e}")
        return False

# =========================================================
# OUTPUT
# =========================================================
def save_data(file_path, df):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)

# =========================================================
# DOWNLOAD ENGINE
# =========================================================
def append_new_data(ticker, tf_name, cfg):
    file_path = os.path.join(OUTPUT_DIR, tf_name, f"{ticker}.csv")

    try:
        df_new = yf.download(
            ticker,
            interval=cfg["interval"],
            period=cfg["period"],
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df_new is None or df_new.empty:
            log(f"⚠ {ticker} [{tf_name}] no data")
            return False

        df_new.reset_index(inplace=True)
        df_new = normalize_columns(df_new)

        if os.path.exists(file_path):
            df_old = pd.read_csv(file_path)

            last_dt = pd.to_datetime(df_old.iloc[-1, 0])
            df_new = df_new[pd.to_datetime(df_new.iloc[:, 0]) > last_dt]

            if df_new.empty:
                return False

            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new

        if len(df) > 1500:
            df = df.iloc[-1500:].reset_index(drop=True)

        save_data(file_path, df)

        log(f"✔ {ticker} [{tf_name}] saved ({len(df)})")
        return True

    except Exception as e:
        log(f"❌ {ticker} [{tf_name}] error: {e}")
        return False

# =========================================================
# FULL UPDATE CORE
# =========================================================
def _run_update_core():
    log("🚀 Full update started...")

    tickers = load_tickers_from_journal()
    total = len(tickers)

    for i, ticker in enumerate(tickers, 1):
        log(f"📊 {ticker} ({i}/{total})")

        for tf_name, cfg in TIMEFRAMES.items():
            append_new_data(ticker, tf_name, cfg)

        fetch_financials(ticker)

    log("✅ Full update complete")

# =========================================================
# SINGLE TICKER UPDATE CORE (NEW)
# =========================================================
def _run_update_single(ticker):
    log(f"🚀 Single update started: {ticker}")

    try:
        for tf_name, cfg in TIMEFRAMES.items():
            append_new_data(ticker, tf_name, cfg)

        fetch_financials(ticker)

        log(f"✅ Single update complete: {ticker}")

    except Exception as e:
        log(f"❌ Single update error {ticker}: {e}")

# =========================================================
# PREVIEW WINDOW
# =========================================================
def run_update():
    try:
        tickers = load_tickers_from_journal()

        if not tickers:
            log("No tickers found")
            return

        preview = tk.Toplevel(dashboard)
        preview.title("Update Preview")
        preview.geometry("520x520")
        preview.lift()
        preview.focus_force()

        # HEADER
        header = tk.Label(
            preview,
            text=f"{len(tickers)} tickers ready",
            font=("Arial", 12, "bold")
        )
        header.pack(pady=10)

        # LISTBOX (SELECTABLE)
        list_frame = tk.Frame(preview)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        box = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set
        )

        for t in tickers:
            box.insert(tk.END, t)

        box.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=box.yview)

        # BUTTON BAR
        btn_frame = tk.Frame(preview)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        def start_all():
            preview.destroy()
            threading.Thread(target=_run_update_core, daemon=True).start()

        def start_single():
            selected = box.curselection()
            if not selected:
                log("⚠ No ticker selected")
                return

            ticker = box.get(selected[0])
            preview.destroy()
            threading.Thread(target=_run_update_single, args=(ticker,), daemon=True).start()

        def close():
            preview.destroy()
            log("Update cancelled")

        tk.Button(btn_frame, text="Start ALL", command=start_all, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=start_single, width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=close, width=10).pack(side=tk.LEFT, padx=5)

        preview.update_idletasks()

    except Exception as e:
        print("PREVIEW ERROR:", e)
        log(f"Preview error: {e}")

# =========================================================
# UI
# =========================================================
def main():
    global dashboard, dashboard_log

    dashboard = tk.Tk()
    dashboard.title("Stock Data Downloader")
    dashboard.geometry("950x700")

    ttk.Label(dashboard, text="Stock Downloader", font=("Arial", 18)).pack(pady=10)

    ttk.Button(dashboard, text="Update Data (Preview)", command=run_update).pack(pady=5)

    dashboard_log = scrolledtext.ScrolledText(dashboard, height=30)
    dashboard_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    dashboard.mainloop()

if __name__ == "__main__":
    main()