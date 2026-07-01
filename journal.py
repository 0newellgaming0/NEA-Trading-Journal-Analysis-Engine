import modules.journal_filters as jf
import modules.executed_trades_notes as etn
import modules.risk_grid_engine as rge

from modules.risk_grid_engine import (
    initialize_risk_engine,
    recalc,
    auto_calc_stop,
    safe_recalc,
    get_engine_state,
    set_engine_state,
    build_preview_row,
    preview_text,
    low,
    last_high,
    safe_float
)

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
import tkinter.scrolledtext as st

import csv
import os
from datetime import datetime
import yfinance as yf
import pandas as pd
import webbrowser
import uuid

from modules import yahooFetcher
import modules.webull.webullDownloader as webullDownloader

from modules.volumeAnalysis import (
    rvol,
    detect_volume_spike,
    detect_volume_contraction,
    up_volume_percentage,
    down_volume_percentage,
    obv,
    obv_slope,
    accumulation_distribution,
    ad_slope,
    large_volume_up_days,
    large_volume_down_days,
    institutional_accumulation_state
)

from modules.financialAnalysis import format_financial_prompt
from modules.historicalAnalysis import analyze_historical_data
from modules.tlineAnalysis import analyze_tline_intraday

from modules.portfolio_overview import PortfolioOverviewPopup
from modules.pointFigureWyckoff import run_wyckoff_pnf_analysis, format_for_journal as format_pnf_for_journal
from modules.fractalEngine import analyze_wyckoff_fractals, format_for_journal as format_fractal_for_journal

from modules.accountLedger import show_account_ledger_popup

from modules.candlestickAnalysis import (
    analyze_multitimeframe_candlesticks,
    format_candlestick_for_journal
)

from modules.liquidity_multi_timeframe_engine import run_liquidity_multi_timeframe_engine
from modules.dtfm_analysis import analyze_dual_timeframe_momentum
from modules.relative_strength_engine import build_relative_strength_block
from modules.risk_engine import get_latest_close, evaluate_stop_loss

from modules.watchlist_popup import WatchlistPopup
from modules.signals_popup import open_signals_popup

# ✅ PATH RESOLVER (ONLY SOURCE OF TRUTH NOW)
from modules.path_resolver import get_stock_data_path, get_project_root, get_watchlist_db_path
from modules.yahoo_history import load_yahoo_history
from modules.volume_context import load_volume_analysis
from modules.candlestick_state_engine import CandlestickInstitutionalStateEngine
from modules.eventEngine import EventStore

import logging

# =========================================================
# CONFIG (PATH-RESOLVER ALIGNED)
# =========================================================
GLOBAL_EVENT_STORE = EventStore()
BASE_DIR = get_project_root()

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "nea28.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

README_DIR = os.path.join(BASE_DIR, "readMe")
PLAN_DIR = os.path.join(BASE_DIR, "plan")

SYSTEM_FILES_DIR = os.path.join(BASE_DIR, "data", "systemFiles")
ANALYSIS_DIR = os.path.join(BASE_DIR, "data", "analysis")

os.makedirs(README_DIR, exist_ok=True)
os.makedirs(PLAN_DIR, exist_ok=True)
os.makedirs(SYSTEM_FILES_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)

# =========================================================
# SYSTEM FILES (NO HARDCODED RELATIVE PATHS OUTSIDE RESOLVER)
# =========================================================

JOURNAL_FILE = os.path.join(SYSTEM_FILES_DIR, "journal.csv")
WEBULL_FILE = os.path.join(SYSTEM_FILES_DIR, "Webull_Orders_Records.csv")
HOWTO_FILE = os.path.join(SYSTEM_FILES_DIR, "howTo.txt")
SHOW_HOWTO_FILE = os.path.join(SYSTEM_FILES_DIR, "show_howto_flag.txt")
LEDGER_FILE = os.path.join(SYSTEM_FILES_DIR, "account_ledger.csv")
EXECUTED_TRADES_NOTES_FILE = os.path.join(SYSTEM_FILES_DIR, "executed_trade_notes.csv")


LEDGER_FIELDS = [
    "id",
    "timestamp",
    "investor",
    "entry_class",
    "transaction_type",
    "debit",
    "credit",
    "gain_loss",
    "distribution",
    "equity_after",
    "ownership_pct",
    "notes"
]
journal_rows = []
EXECUTED_TRADE_NOTE_FIELDS = [
    "trade_id",
    "ticker",
    "placed_time",
    "notes",
    "analysis_notes",
    "management_notes"
]
CSV_FIELDS = [
    "timestamp",
    "ticker",
    "account",
    "risk_dollar",
    "stop",

    "ladder_1_price",
    "ladder_1_shares",
    "ladder_1_total",

    "ladder_2_price",
    "ladder_2_shares",
    "ladder_2_total",

    "ladder_3_price",

    "ladder_4_price",

    "buy_now_price",
    "buy_now_shares",
    "buy_now_total",

    "trade_notes",
    "analysis_notes",
    "management_notes"
]


financial_block = ""
history_block = ""
daily_volume_block = ""
intraday_block = ""
volume_block = ""
historical_results = ""
historical_block = ""
pnf_block = ""
fractal_block = ""
pinbar_result = ""
engulfing_result = ""
inside_bar_result = ""
hammer_result = ""
marubozu_result = ""
analyze_reversal_patterns_result = "" 
star_pattern_result = ""
harami_pattern_result = ""
three_inside_pattern_result = ""

# =========================================================
# SAFE FILE INIT (UNCHANGED LOGIC, CLEAN PATHS)
# =========================================================

if not os.path.exists(JOURNAL_FILE):
    with open(JOURNAL_FILE, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

if not os.path.exists(LEDGER_FILE):
    with open(LEDGER_FILE, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=LEDGER_FIELDS).writeheader()

if not os.path.exists(EXECUTED_TRADES_NOTES_FILE):
    with open(EXECUTED_TRADES_NOTES_FILE, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=EXECUTED_TRADE_NOTE_FIELDS).writeheader()

# =========================================================
# ANALYSIS EXPORTER
# =========================================================
def export_analysis_md(ticker, analysis_blocks):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    folder = os.path.join(ANALYSIS_DIR, ticker.upper())
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, f"{ticker}_{timestamp}.md")

    def normalize_content(content):
        """
        Forces everything into clean markdown text.
        Prevents CSV/DataFrame leaks into output.
        """

        # If pandas DataFrame sneaks in → convert properly
        if isinstance(content, pd.DataFrame):
            sections = []

            for _, row in content.iterrows():
                module = row.get("module", "MODULE")
                prompt = row.get("journal_prompt", "")

                sections.append(
                    f"""## {module}

{prompt}
"""
                )

            return "\n\n---\n\n".join(sections)

        # If dict-like row
        if isinstance(content, dict):
            return str(content.get("journal_prompt", content))

        # Default: string cleanup (kills CSV headers accidentally passed in)
        text = str(content)

        # remove accidental CSV header leaks
        if text.strip().lower().startswith("ticker,module"):
            return ""

        return text

    with open(path, "w", encoding="utf-8") as f:

        # =========================
        # CLEAN HEADER (FIXED)
        # =========================
        f.write(f"""# {ticker} Institutional Analysis Report

Generated: {datetime.now():%Y-%m-%d %H:%M:%S}

---

> Analysis generated by NEA28  
> Work in Progress  
> Not Financial Advice  

---
""")

        # =========================
        # BLOCK OUTPUT
        # =========================
        for name, content in analysis_blocks.items():

            clean = normalize_content(content)

            if not clean:
                continue

            f.write(f"## {name.replace('_', ' ').title()}\n\n")
            f.write(clean)
            f.write("\n\n---\n\n")

    return path
    
# =========================================================
# MARKET DATA LOADING (NOW FULLY PATH_RESOLVER-BASED)
# =========================================================

def load_market_context(ticker):
    ticker = ticker.upper()

    daily_path = get_stock_data_path(ticker, "daily")
    intraday_path = get_stock_data_path(ticker, "intraday_60m")
    weekly_path = get_stock_data_path(ticker, "weekly")

    daily_df = pd.read_csv(daily_path) if os.path.exists(daily_path) else None
    intraday_df = pd.read_csv(intraday_path) if os.path.exists(intraday_path) else None
    weekly_df = pd.read_csv(weekly_path) if os.path.exists(weekly_path) else None

    for df in [intraday_df, weekly_df]:
        if df is not None and "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    return daily_df, intraday_df, weekly_df


def load_intraday_15m(ticker):
    path = get_stock_data_path(ticker, "intraday_15m")
    return pd.read_csv(path) if os.path.exists(path) else None


def load_intraday_60m(ticker):
    path = get_stock_data_path(ticker, "intraday_60m")
    return pd.read_csv(path) if os.path.exists(path) else None


def load_weekly(ticker):
    path = get_stock_data_path(ticker, "weekly")
    return pd.read_csv(path) if os.path.exists(path) else None
    
# =========================================================
# INTRADAY STRUCTURE CONTEXT
# =========================================================

def build_intraday_context(ticker, intraday_df):
    if intraday_df is None or intraday_df.empty:
        return "No intraday data available."

    ticker = ticker.lower()

    close_col = f"close_{ticker}"
    high_col = f"high_{ticker}"
    low_col = f"low_{ticker}"
    volume_col = f"volume_{ticker}"

    required = [close_col, high_col, low_col, volume_col]

    for col in required:
        if col not in intraday_df.columns:
            return f"Missing intraday column: {col}"

    latest = intraday_df.iloc[-1]

    prev = (
        intraday_df.iloc[-2]
        if len(intraday_df) > 1
        else latest
    )

    latest_close = latest[close_col]
    prev_close = prev[close_col]

    bar_change = latest_close - prev_close
    bar_pct = ((bar_change / prev_close) * 100) if prev_close else 0

    rolling_vol = intraday_df[volume_col].rolling(10).mean().iloc[-1]

    volume_spike = (
        latest[volume_col] > rolling_vol
        if pd.notna(rolling_vol)
        else False
    )

    session_high = intraday_df[high_col].max()
    session_low = intraday_df[low_col].min()

    return {
        "last_close": round(latest_close, 2),
        "bar_change": round(bar_change, 2),
        "bar_pct": round(bar_pct, 2),
        "volume_spike": volume_spike,
        "session_high": round(session_high, 2),
        "session_low": round(session_low, 2),
    }
# =========================================================
# PROMPT ROW BUILDER (ENGINE INTEGRATION LAYER)
# =========================================================
def build_prompt_row(row_data):

    snapshot = rge.get_trade_snapshot()

    return {
        **row_data,

        "buy_now_price": snapshot.get("entry_price"),
        "buy_now_shares": snapshot.get("shares"),
        "buy_now_total": snapshot.get("trade_total"),

        "account": snapshot.get("account"),
        "risk_dollar": snapshot.get("risk_dollar"),

        "stop": snapshot.get(
            "stop_loss",
            snapshot.get("stop", row_data.get("stop", ""))
        )
    }
    
# ==========================================================
# ROOT
# ==========================================================
root = tk.Tk()
rge.initialize_risk_engine(root)
root.title("NEWELL TRADING GROUP -NEA28V1-BETA")
root.geometry("1850x950")
root.configure(bg="#f2f2f2")

def should_show_howto():
    if not os.path.exists(SHOW_HOWTO_FILE):
        return True
    try:
        with open(SHOW_HOWTO_FILE, "r", encoding="utf-8") as f:
            return f.read().strip() != "0"
    except:
        return True


def set_show_howto(value: bool):
    with open(SHOW_HOWTO_FILE, "w") as f:
        f.write("1" if value else "0")
        
def show_howto_popup():
    popup = tk.Toplevel(root)
    popup.title("System Introduction - HOW TO")
    popup.geometry("900x700")
    popup.configure(bg="#f2f2f2")

    txt = st.ScrolledText(popup, wrap="word", font=("Courier", 10))
    txt.pack(fill="both", expand=True, padx=10, pady=10)

    # ALWAYS READ ONLY FROM howto.txt
    try:
        with open(HOWTO_FILE, "r", encoding="utf-8") as f:
            txt.insert("1.0", f.read())
    except Exception as e:
        txt.insert("1.0", f"howto.txt not found or error reading file:\n{e}")

    txt.config(state="disabled")

    bottom = tk.Frame(popup, bg="#f2f2f2")
    bottom.pack(fill="x", pady=5)

    dont_show = tk.BooleanVar(value=False)

    tk.Checkbutton(
        bottom,
        text="Do not show this window again at startup",
        variable=dont_show,
        bg="#f2f2f2",
        font=("Arial", 10)
    ).pack(side="left", padx=10)

    def close_popup():
        # ONLY WRITE TO FLAG FILE — NEVER TOUCH HOWTO.TXT
        try:
            with open(SHOW_HOWTO_FILE, "w", encoding="utf-8") as f:
                f.write("0" if dont_show.get() else "1")
        except Exception as e:
            messagebox.showerror("Error", str(e))

        popup.destroy()

    tk.Button(
        bottom,
        text="Continue",
        font=("Arial", 10, "bold"),
        bg="#4caf50",
        fg="white",
        command=close_popup
    ).pack(side="right", padx=10)
    
# ==========================================================
# DARK MODE STATE
# ==========================================================
dark_mode = tk.BooleanVar(value=False)

def apply_theme():
    if dark_mode.get():
        bg = "#1e1e1e"
        fg = "#e0e0e0"
        entry_bg = "#2b2b2b"
        tree_bg = "#252526"
    else:
        bg = "#f2f2f2"
        fg = "#000000"
        entry_bg = "#ffffff"
        tree_bg = "#ffffff"

    root.configure(bg=bg)
    left.configure(bg=bg)
    right.configure(bg=tree_bg)
    footer.configure(bg=bg)
    header.configure(bg="#333333" if dark_mode.get() else "#d84315")

    for widget in root.winfo_children():
        try:
            widget.configure(bg=bg, fg=fg)
        except:
            pass

    style = ttk.Style()
    style.configure("Treeview",
                    background=tree_bg,
                    fieldbackground=tree_bg,
                    foreground=fg,
                    rowheight=18)
    style.configure("Treeview.Heading",
                    background=bg,
                    foreground=fg,
                    font=("Arial",9,"bold"))

# ==========================================================
# CONTAINER FOR LEFT + RIGHT
# ==========================================================
main_content = tk.Frame(root, bg="#f2f2f2")
main_content.pack(side="top", fill="both", expand=True)

# LEFT PANEL
left = tk.Frame(main_content, bg="#f2f2f2")
left.pack(side="left", fill="y")

# RIGHT PANEL
right = tk.Frame(main_content, bg="white")
right.pack(side="right", fill="both", expand=True)
right.pack_propagate(False)

def open_folder_viewer(folder_path, title="File Viewer", geometry="900x700"):

    target_dir = os.path.join(BASE_DIR, folder_path)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # ======================================================
    # ONLY ONE RULE: PURE DIRECTORY LISTING
    # ======================================================
    files = sorted([
        f for f in os.listdir(target_dir)
        if os.path.isfile(os.path.join(target_dir, f))
    ])

    if not files:
        tk.messagebox.showwarning(
            "No Files",
            f"No files found in {folder_path}"
        )
        return

    popup = tk.Toplevel(root)
    popup.title(title)
    popup.geometry(geometry)
    popup.configure(bg="#f2f2f2")

    # TOP BAR
    top_bar = tk.Frame(popup, bg="#f2f2f2")
    top_bar.pack(fill="x", pady=5)

    current_file_label = tk.Label(
        top_bar,
        text="",
        font=("Arial", 11, "bold"),
        bg="#f2f2f2"
    )
    current_file_label.pack(side="left", padx=10)

    # TEXT AREA
    txt = st.ScrolledText(popup, wrap="word", font=("Courier", 10))
    txt.pack(fill="both", expand=True, padx=10, pady=(0, 5))

    # FOOTER
    footer_frame = tk.Frame(popup, bg="#f2f2f2")
    footer_frame.pack(fill="x", side="bottom", pady=5)

    tk.Label(
        footer_frame,
        text="© 2026 Newell Trading Group. All rights reserved.",
        font=("Arial", 9),
        bg="#f2f2f2"
    ).pack(side="left", padx=10)

    nav_frame = tk.Frame(footer_frame, bg="#f2f2f2")
    nav_frame.pack(side="right", padx=10)

    # FILE LOADER
    def load_file(index):

        file_name = files[index]
        file_path = os.path.join(target_dir, file_name)

        current_file_label.config(text=f"Viewing: {file_name}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file:\n\n{e}"

        txt.config(state="normal")
        txt.delete("1.0", tk.END)
        txt.insert("1.0", content)
        txt.config(state="disabled")

        prev_btn.file_index = (index - 1) % len(files)
        next_btn.file_index = (index + 1) % len(files)

    # NAVIGATION
    def next_file(event=None):
        load_file(next_btn.file_index)

    def prev_file(event=None):
        load_file(prev_btn.file_index)

    prev_btn = tk.Label(
        nav_frame,
        text="◀ Previous",
        font=("Arial", 9, "underline"),
        fg="blue",
        cursor="hand2",
        bg="#f2f2f2"
    )
    prev_btn.pack(side="left", padx=10)
    prev_btn.bind("<Button-1>", prev_file)

    next_btn = tk.Label(
        nav_frame,
        text="Next ▶",
        font=("Arial", 9, "underline"),
        fg="blue",
        cursor="hand2",
        bg="#f2f2f2"
    )
    next_btn.pack(side="left", padx=10)
    next_btn.bind("<Button-1>", next_file)

    # INIT
    load_file(0)
    
def show_readme():
    open_folder_viewer("readMe", "README Viewer", "900x700")

# ==========================================================
# SCRAPER FILES POPUP
# ==========================================================
def show_scraper_files_popup():
    open_folder_viewer("scraperFiles", "Scraper Files", "1000x750")
    
# ==========================================================
# PLAN FILES POPUP (SCRAPER-STYLE DYNAMIC LOADER)
# ==========================================================
def show_plan_popup():
    open_folder_viewer("plan", "Plan Viewer", "900x700")

# ==========================================================
# DEVELOPER NOTES README POPUP
# ==========================================================
def show_developer_notes_popup():
    open_folder_viewer(
        "readMe/developerNotes",
        "Developer Notes",
        "900x700"
    )
    
def show_analysis_files_popup():
    import sqlite3

    def load_tickers():
        tickers = set()
        db_path = get_watchlist_db_path()

        if not os.path.exists(db_path):
            return ["NO DATA"]

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            cur.execute("SELECT ticker FROM watchlist")
            rows = cur.fetchall()

            for r in rows:
                if r and r[0]:
                    tickers.add(r[0].strip().upper())

            conn.close()

        except Exception:
            return ["NO DATA"]

        return sorted(list(tickers)) if tickers else ["NO DATA"]

    tickers = load_tickers()

    popup = tk.Toplevel(root)
    popup.title("Analysis File Browser")
    popup.geometry("350x120")
    popup.configure(bg="#f2f2f2")

    tk.Label(
        popup,
        text="Select Ticker Folder",
        font=("Arial", 12, "bold"),
        bg="#f2f2f2"
    ).pack(pady=10)

    selected_ticker = tk.StringVar(value=tickers[0])

    dropdown = ttk.Combobox(
        popup,
        textvariable=selected_ticker,
        values=tickers,
        state="readonly",
        width=20
    )
    dropdown.pack(pady=5)

    def open_selected():
        ticker = selected_ticker.get().upper().strip()

        # ✅ FIX: now uses data/analysis correctly
        folder_path = os.path.join("data", "analysis", ticker)

        open_folder_viewer(
            folder_path,
            title=f"Analysis Files - {ticker}",
            geometry="1000x750"
        )

        popup.destroy()

    tk.Button(
        popup,
        text="Open",
        font=("Arial", 11, "bold"),
        bg="#4caf50",
        fg="white",
        command=open_selected
    ).pack(pady=10)

def load_webull_executions():
    if not os.path.isfile(WEBULL_FILE):
        return []

    with open(WEBULL_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    executions = []
    for r in rows:
        if r.get("Status","").lower() == "filled":
            executions.append(r)
    return executions

def run_yahoo_update():
    try:
        yahooFetcher.run_update()  # now handles preview + execution internally
    except Exception as e:
        messagebox.showerror("Update Error", str(e))
        
def run_webull_update():
    try:
        webullDownloader.run_update()  # same pattern as yahooFetcher
    except Exception as e:
        messagebox.showerror("Webull Update Error", str(e))        

def open_portfolio_overview():

    csv_path = WEBULL_FILE

    if not os.path.exists(csv_path):

        messagebox.showerror(
            "Missing CSV",
            f"Could not locate:\n{csv_path}"
        )

        return

    PortfolioOverviewPopup(root, csv_path)
    
def show_watchlist_popup():
    global root
    WatchlistPopup(root)
    
def show_signals_popup():
    global root
    open_signals_popup(root)
    
# ==========================================================
# HEADER
# ==========================================================
header = tk.Frame(left, bg="#F2F2F2")
header.pack(fill="x")

tk.Label(
    header,
    text="RISK MANAGEMENT - NEA28V1",
    bg="#F0F0F0",
    font=("Arial", 18, "bold")
).pack(side="left", padx=10)

tk.Entry(
    header,
    textvariable=rge.ticker,
    font=("Arial", 14, "bold"),
    width=12
).pack(side="right", padx=10)

# ==========================================================
# MAIN GRID
# ==========================================================
grid = tk.Frame(left, bg="#f2f2f2")
grid.pack(pady=10)

def box(parent, label, var, bg, row, col):
    tk.Label(parent, text=label, font=("Arial", 12, "bold")).grid(row=row, column=col, padx=5)
    tk.Entry(
        parent,
        textvariable=var,
        font=("Arial", 14, "bold"),
        bg=bg,
        width=10,
        justify="center"
    ).grid(row=row + 1, column=col, padx=5)

# Account, Low, Risk %, Risk $
box(grid, "Account", rge.account, "#ffff00", 0, 0)
box(grid, "Low", rge.low, "#ffff00", 0, 1)
box(grid, "Risk %", rge.risk_pct, "#ffff00", 0, 2)
box(grid, "Risk $", rge.risk_dollar, "#7cb342", 0, 3)

# Stop / Last High
box(grid, "Stop Loss", rge.stop, "#ffff00", 2, 0)
box(grid, "Last High", rge.last_high, "#ffff00", 2, 1)

# Ladder / Fib boxes
labels = ["Range High", "Range Low", "Wave 1 Retracement", "Shakeout"]

for i in range(4):
    box(grid, labels[i], rge.ladder_prices[i], "#ffffff", 4, i)
    box(grid, f"Shares {i+1}", rge.ladder_shares[i], "#aed581", 6, i)
    box(grid, f"Total {i+1}", rge.ladder_totals[i], "#ffc107", 8, i)

box(grid, "Total Cost", rge.total_cost, "#aed581", 10, 0)
box(grid, "# Shares", rge.total_shares, "#aed581", 10, 1)

for i in range(4):
    box(grid, f"1:1 Target {i+1}", rge.rr_targets[i], "#ff7043", 12, i)

box(grid, "BUY NOW", rge.buy_now_price, "#aed581", 14, 0)
box(grid, "BUY Shares", rge.buy_now_shares, "#aed581", 14, 1)
box(grid, "BUY Total $$", rge.buy_now_total, "#aed581", 14, 2)

# ==========================================================
# SAVE
# ==========================================================
def save():

    # 🔥 SINGLE SOURCE OF TRUTH
    snapshot = rge.get_trade_snapshot()

    row = {
        "timestamp": datetime.now().isoformat(),
        "ticker": rge.ticker.get(),

        "account": snapshot.get("account", ""),
        "risk_dollar": snapshot.get("risk_dollar", ""),
        "stop": snapshot.get("stop", snapshot.get("stop_loss", "")),

        "ladder_1_price": snapshot["ladder"][0]["price"],
        "ladder_1_shares": snapshot["ladder"][0]["shares"],
        "ladder_1_total": snapshot["ladder"][0]["total"],

        "ladder_2_price": snapshot["ladder"][1]["price"],
        "ladder_2_shares": snapshot["ladder"][1]["shares"],
        "ladder_2_total": snapshot["ladder"][1]["total"],

        "ladder_3_price": snapshot["ladder"][2]["price"],
        "ladder_4_price": snapshot["ladder"][3]["price"],

        "buy_now_price": snapshot.get("entry_price", ""),
        "buy_now_shares": snapshot.get("shares", ""),
        "buy_now_total": snapshot.get("trade_total", ""),

        "trade_notes": "",
        "analysis_notes": "",
        "management_notes": ""
    }

    with open(JOURNAL_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writerow(row)

    load_journal()

    template_ticker_var.set(rge.ticker.get())
    update_template_panel()


# ==========================================================
# SAVE ENTRY BUTTON (RESTORED)
# ==========================================================
save_frame = tk.Frame(left, bg="#f2f2f2")
save_frame.pack(pady=(5, 0), fill="x")

tk.Button(
    save_frame,
    text="SAVE ENTRY",
    font=("Arial", 12, "bold"),
    bg="#4caf50",
    fg="white",
    padx=10,
    pady=6,
    command=save
).pack(fill="x", padx=10)
# ==========================================================
# BLOG / SIGNAL TEMPLATE PANEL (Below Save Entry)
# ==========================================================
def load_journal_data():
    """Load journal CSV into a dictionary keyed by ticker."""
    data = {}
    if not os.path.isfile(JOURNAL_FILE):
        return data
    with open(JOURNAL_FILE,newline="",encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("ticker","").strip()
            if t:
                data[t] = row
    return data
    
def safe_numeric_convert(df, col):

    try:
        df[col] = pd.to_numeric(df[col])
    except Exception:
        df[col] = df[col]  # leave unchanged if it fails  

# =========================================================
# PROMPT GENERATOR
# =========================================================        
def generate_signal_template(row):

    # =====================================================
    # GLOBAL BLOCKS
    # =====================================================
    global financial_block
    global history_block
    global daily_volume_block
    global intraday_block
    global volume_block
    global historical_results 
    global historical_block
    global intraday_15m_prompt
    global intraday_60m_prompt 
    global pnf_block    
    global fractal_block

    ticker = row.get("ticker", "").upper()

    rs_block = build_relative_strength_block(
        ticker,
        "daily"
    )

    logger.info(f"[{ticker}] Starting analysis pipeline")

    # =====================================================
    # LOAD DATASETS
    # =====================================================
    daily_df, intraday_df, weekly_df = load_market_context(ticker)

    logger.info(
        f"[{ticker}] Data loaded | "
        f"Daily={daily_df is not None} "
        f"60M={intraday_df is not None} "
        f"Weekly={weekly_df is not None}"
    )

    intraday_15m_df = load_intraday_15m(ticker)
    intraday_60m_df = load_intraday_60m(ticker)
    weekly_df = load_weekly(ticker)

    logger.info(
        f"[{ticker}] Additional datasets loaded | "
        f"15M={intraday_15m_df is not None} "
        f"60M={intraday_60m_df is not None}"
    )

    # =====================================================
    # LOAD FINANCIAL ANALYSIS BLOCK
    # =====================================================
    financial_block = "[FUNDAMENTALS]\n" + format_financial_prompt(ticker)

    logger.info(f"[{ticker}] Financial block complete")

    # =====================================================
    # DAILY CONTEXT
    # =====================================================
    history_block = load_yahoo_history(
        ticker,
        timeframe="daily",
        limit=80
    )

    logger.info(f"[{ticker}] Daily history loaded")

    try:
        logger.info(f"[{ticker}] Running risk engine")

        stop_val = float(row.get("stop", 0))

        latest_close = get_latest_close(
            intraday_60m_df,
            ticker=row.get("ticker", "")
        )

        risk_state = evaluate_stop_loss(
            latest_close,
            stop_val,
            df=intraday_60m_df,
            daily_df=daily_df,
            ticker=row.get("ticker", "")
        )

        stop_breached = risk_state["breached"]
        stop_block = risk_state["block"]

        logger.info(
            f"[{ticker}] Risk engine completed | "
            f"Breached={stop_breached}"
        )

    except Exception:
        logger.exception(
            f"[{ticker}] Risk engine FAILED"
        )

        stop_block = "⚠️ Risk engine error. See log."
        stop_breached = False

    # =====================================================
    # WEEKLY CONTEXT
    # =====================================================
    weekly_block = load_yahoo_history(
        ticker,
        timeframe="weekly",
        limit=80
    )

    logger.info(f"[{ticker}] Weekly history loaded")

    # =====================================================
    # DAILY VOLUME CONTEXT
    # =====================================================
    daily_volume_block = load_volume_analysis(
        ticker,
        timeframe="daily",
        limit=80
    )

    logger.info(f"[{ticker}] Daily volume analysis complete")

    # =====================================================
    # INTRADAY CONTEXT
    # =====================================================
    intraday_block = load_yahoo_history(
        ticker,
        timeframe="intraday_60m",
        limit=40
    )

    volume_block = load_volume_analysis(
        ticker,
        timeframe="intraday_60m",
        limit=40
    )

    logger.info(f"[{ticker}] Intraday context complete")

    # =====================================================
    # T-LINE ANALYSIS
    # =====================================================
    try:
        logger.info(f"[{ticker}] Running T-Line analysis")

        intraday_15m_prompt = analyze_tline_intraday(
            intraday_15m_df,
            ticker,
            "15M"
        )

        intraday_60m_prompt = analyze_tline_intraday(
            intraday_60m_df,
            ticker,
            "60M"
        )

        dtfm_prompt = analyze_dual_timeframe_momentum(
            intraday_60m_df,
            daily_df,
            ticker,
            "DTFM"
        )

        logger.info(f"[{ticker}] T-Line analysis complete")

    except Exception:
        logger.exception(
            f"[{ticker}] T-Line analysis FAILED"
        )

        intraday_15m_prompt = "T-Line 15M unavailable."
        intraday_60m_prompt = "T-Line 60M unavailable."
        dtfm_prompt = "DTFM unavailable."

    # =====================================================
    # CANDLESTICK MULTI-TIMEFRAME ENGINE
    # =====================================================
    try:
        logger.info(f"[{ticker}] Running candlestick engine")

        candlestick_result = analyze_multitimeframe_candlesticks(
            intraday_15m_df,
            intraday_60m_df,
            daily_df,
            ticker
        )

        candlestick_block = format_candlestick_for_journal(
            candlestick_result
        )

        logger.info(f"[{ticker}] Candlestick engine complete")

    except Exception:
        logger.exception(
            f"[{ticker}] Candlestick engine FAILED"
        )

        candlestick_block = (
            "Candlestick analysis unavailable. "
            "See log."
        )

    # =====================================================
    # LIQUIDITY ENGINE
    # =====================================================
    try:
        logger.info(f"[{ticker}] Running liquidity engine")

        liquidity_output = run_liquidity_multi_timeframe_engine({
            "15m": intraday_15m_df,
            "60m": intraday_60m_df,
            "1D": daily_df,
            "weekly": weekly_df
        })

        phase_context_block = liquidity_output.get(
            "phase_context_block",
            "Liquidity phase context unavailable."
        )

        liquidity_block = liquidity_output.get(
            "liquidity_block",
            "Liquidity block unavailable."
        )

        logger.info(f"[{ticker}] Liquidity engine complete")

    except Exception:
        logger.exception(
            f"[{ticker}] Liquidity engine FAILED"
        )

        phase_context_block = "Liquidity engine failed."
        liquidity_block = "Liquidity engine failed."

    # =====================================================
    # WYCKOFF PNF ANALYSIS
    # =====================================================
    try:
        logger.info(f"[{ticker}] Running PnF engine")

        pnf_result = run_wyckoff_pnf_analysis(
            ticker=ticker,
            timeframe="daily",
            box_size=1.0,
            reversal=3
        )

        pnf_block = format_pnf_for_journal(
            pnf_result
        )

        logger.info(f"[{ticker}] PnF engine complete")

    except Exception:
        logger.exception(
            f"[{ticker}] PnF engine FAILED"
        )

        pnf_block = "PnF analysis unavailable."

    # =====================================================
    # INSTITUTIONAL CANDLE ENGINE
    # =====================================================
    try:
        logger.info(
            f"[{ticker}] Running institutional candle engine"
        )

        engine = CandlestickInstitutionalStateEngine(
            ticker,
            GLOBAL_EVENT_STORE
        )

        candlestick_df = engine.run(
            daily_df
        )

        candlestick_modules_report = []

        for _, row in candlestick_df.iterrows():

            candlestick_modules_report.append(
                f"""
# {row['module']}

{row['journal_prompt']}
"""
            )

        candlestick_block1 = "\n\n---\n\n".join(
            candlestick_modules_report
        )

        logger.info(
            f"[{ticker}] Institutional candle engine complete"
        )

    except Exception:
        logger.exception(
            f"[{ticker}] Institutional candle engine FAILED"
        )

        candlestick_block1 = (
            "Institutional candlestick analysis unavailable."
        )

        
    # =====================================================
    # FRACTAL STRUCTURE ANALYSIS (SAFE FIX)
    # =====================================================
    try:
        daily_df, intraday_df, weekly_df = load_market_context(ticker)

        if isinstance(daily_df, pd.DataFrame) and not daily_df.empty:

            fractal_result = analyze_wyckoff_fractals(
                daily_df,
                ticker=ticker
            )

            fractal_block = format_fractal_for_journal(fractal_result)

        else:
            fractal_block = "Fractal analysis unavailable: invalid or empty dataset"

    except Exception as e:
        fractal_block = f"Fractal analysis error: {str(e)}"

    # =====================================================
    # HISTORICAL CONTEXT (YFINANCE)
    # =====================================================
    try:
        historical_df = yf.download(
            ticker,
            period="5y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        historical_analysis = analyze_historical_data(
            historical_df,
            ticker=ticker
        )

        historical_results = historical_analysis.get(
            "prompt_summary",
            "Historical analysis unavailable."
        )

        historical_block = historical_results

    except Exception as e:
        historical_results = f"Historical analysis failed: {str(e)}"
        historical_block = historical_results

    # =====================================================
    # FORMATTERS
    # =====================================================
    def fmt(field):
        value = row.get(field, "")
        try:
            return f"{float(value):.4f}"
        except:
            return value

    try:
        buy_now = float(row.get("buy_now_price", 0))
        stop_val = float(row.get("stop", 0))

        rr_target = round(
            buy_now + 2 * (buy_now - stop_val),
            4
        )
    except:
        rr_target = fmt("ladder_2_price")

    analysis_blocks = {
        "candlestick_modules": candlestick_block1,
        "candlestick_summary": candlestick_block,
        "fundamentals": financial_block,
        "historical": historical_block,
        "risk_engine": stop_block,
        "tline_15m": intraday_15m_prompt,
        "tline_60m": intraday_60m_prompt,
        "weekly_context": weekly_block,
        "daily_context": history_block,
        "daily_volume": daily_volume_block,
        "intraday_context": intraday_block,
        "intraday_volume": volume_block,
        "dual_timeframe_momentum": dtfm_prompt,
        "point_and_figure": pnf_block,
        "fractal": fractal_block,
        "liquidity_phase": phase_context_block,
        "liquidity_engine": liquidity_block,
        "relative_strength": rs_block
    }
    
    export_path = export_analysis_md(
        ticker,
        analysis_blocks
    )    

    template = f"""==================================================
📅Today's Date: {datetime.now().isoformat()}
📅Journal Entry Date: {row.get('timestamp','').split('T')[0]}
📈Ticker: {row.get('ticker','')}
==================================================
{historical_results}
{dtfm_prompt}
{stop_block}
{candlestick_block1}
{candlestick_block}
{financial_block}
{weekly_block}
{history_block}
{daily_volume_block}
{intraday_block}
{volume_block}
{pnf_block}
{fractal_block}
{phase_context_block}
{liquidity_block}
{rs_block}
{intraday_15m_prompt }
{intraday_60m_prompt }

"""
    return template

# ==========================================================
# JOURNAL FILTER / SEARCH BAR
# ==========================================================
filter_frame = tk.Frame(right, bg="white")
filter_frame.pack(fill="x", padx=5, pady=(5, 0))

tk.Label(
    filter_frame,
    text="Search / Filter Journal",
    font=("Arial", 10, "bold"),
    bg="white"
).pack(side="left", padx=(5, 15))

# FILTER TYPE
filter_type_var = tk.StringVar(value="ticker")

filter_options = ttk.Combobox(
    filter_frame,
    textvariable=filter_type_var,
    values=["ticker", "timestamp"],
    state="readonly",
    width=12
)

filter_options.pack(side="left", padx=5)

# SEARCH INPUT
filter_search_var = tk.StringVar()

filter_entry = tk.Entry(
    filter_frame,
    textvariable=filter_search_var,
    font=("Arial", 10),
    width=30
)

filter_entry.pack(side="left", padx=5)

# RESULT COUNT
filter_count_label = tk.Label(
    filter_frame,
    text="",
    font=("Arial", 9, "bold"),
    bg="white",
    fg="#555555"
)

filter_count_label.pack(side="left", padx=10)

# ==========================================================
# FILTER FUNCTION
# ==========================================================
def apply_journal_filters(*args):
    jf.apply_journal_filters(
        tree,
        journal_rows,
        filter_search_var,
        filter_type_var,
        CSV_FIELDS,
        preview_text,
        filter_count_label
    )

# ==========================================================
# CLEAR FILTERS
# ==========================================================
def clear_journal_filters():

    filter_search_var.set("")
    filter_type_var.set("ticker")

    apply_journal_filters()

tk.Button(
    filter_frame,
    text="Clear Filters",
    font=("Arial", 9, "bold"),
    bg="#b71c1c",
    fg="white",
    padx=10,
    command=clear_journal_filters
).pack(side="left", padx=5)

# LIVE FILTERING
filter_search_var.trace_add("write", apply_journal_filters)
filter_type_var.trace_add("write", apply_journal_filters)

# ==========================================================
# TREEVIEW WITH CLICK REFRESH TEMPLATE
# ==========================================================
tree_frame = tk.Frame(right)
tree_frame.pack(fill="both", expand=True)

vsb = tk.Scrollbar(tree_frame, orient="vertical")
hsb = tk.Scrollbar(tree_frame, orient="horizontal")

tree = ttk.Treeview(
    tree_frame,
    columns=CSV_FIELDS,
    show="headings",
    height=15,
    yscrollcommand=vsb.set,
    xscrollcommand=hsb.set
)

vsb.config(command=tree.yview)
hsb.config(command=tree.xview)

vsb.pack(side="right", fill="y")
hsb.pack(side="bottom", fill="x")
tree.pack(side="left", fill="both", expand=True)

style = ttk.Style()
style.configure("Treeview", font=("Arial",8), rowheight=18)
style.configure("Treeview.Heading", font=("Arial",9,"bold"))

COLUMN_LABELS = {
    "ladder_1_price": "Range High",
    "ladder_2_price": "Range Low",
    "ladder_3_price": "Wave 1",
    "ladder_4_price": "Shakeout"
}

for c in CSV_FIELDS:
    tree.heading(c, text=COLUMN_LABELS.get(c,c))
    tree.column(c, width=100, anchor="center")

# ==========================================================
# EXECUTED TRADES PANEL (Below Trade Journal)
# ==========================================================
trades_frame = tk.Frame(right, bg="white")
trades_frame.pack(fill="x", expand=False, pady=(5,0))

tk.Label(
    trades_frame,
    text="Executed Trades (Webull)",
    font=("Arial",10,"bold"),
    bg="white"
).pack(anchor="w", padx=5, pady=(2,0))

trades_vsb = tk.Scrollbar(trades_frame, orient="vertical")
trades_hsb = tk.Scrollbar(trades_frame, orient="horizontal")

trades_table = ttk.Treeview(
    trades_frame,
    show="headings",
    height=12,
    yscrollcommand=trades_vsb.set,
    xscrollcommand=trades_hsb.set
)

trades_vsb.config(command=trades_table.yview)
trades_hsb.config(command=trades_table.xview)

trades_vsb.pack(side="right", fill="y")
trades_hsb.pack(side="bottom", fill="x")
trades_table.pack(side="left", fill="both", expand=True, padx=5, pady=2)


# ==========================================================
# AUTO-FIT COLUMNS ON DOUBLE-CLICK
# ==========================================================
def auto_fit_columns(event=None):

    fnt = tkFont.Font()

    for col in CSV_FIELDS:

        max_width = fnt.measure(col) + 15

        for item in tree.get_children():

            cell_text = str(tree.set(item, col))

            max_width = max(
                max_width,
                min(fnt.measure(cell_text) + 15, 600)
            )

        tree.column(col, width=max_width)


# ==========================================================
# REFRESH TEMPLATE PANEL ON TREE SELECTION
# ==========================================================
def tree_selection_update(event):

    selected = tree.selection()
    if not selected:
        return

    item = selected[0]
    t = tree.set(item, "ticker")

    if t and t in template_journal_data:
        template_ticker_var.set(t)
        update_template_panel()

    try:
        ticker_value = tree.set(item, "ticker").strip().upper()

        if not ticker_value:
            return

        daily_path = get_stock_data_path(ticker_value, "daily")

        if not os.path.exists(daily_path):
            return

        daily_df = pd.read_csv(daily_path)

        if daily_df.empty:
            return

        ticker_lower = ticker_value.lower()

        high_col = f"high_{ticker_lower}"
        low_col = f"low_{ticker_lower}"

        if high_col not in daily_df.columns:
            high_col = "high"
        if low_col not in daily_df.columns:
            low_col = "low"

        if high_col not in daily_df.columns or low_col not in daily_df.columns:
            return

        daily_df[high_col] = pd.to_numeric(daily_df[high_col], errors="coerce")
        daily_df[low_col] = pd.to_numeric(daily_df[low_col], errors="coerce")

        session_high = round(daily_df[high_col].max(), 2)
        session_low = round(daily_df[low_col].min(), 2)

        # ==============================
        # HARD SAFE GUARDS (FIX)
        # ==============================
        if last_high is not None:
            try:
                last_high.set(session_high)
            except Exception:
                pass

        if low is not None:
            try:
                low.set(session_low)
            except Exception:
                pass

        auto_calc_stop()
        recalc()

    except Exception as e:
        print("Daily structure autofill error:", e)

tree.bind("<<TreeviewSelect>>", tree_selection_update)

# ==========================================================
# DELETE JOURNAL ENTRY
# ==========================================================
def delete_journal_entry(timestamp_to_delete):

    global journal_rows

    confirm = messagebox.askyesno(
        "Delete Entry",
        "Are you sure you want to permanently delete this journal entry?"
    )

    if not confirm:
        return False

    try:

        remaining_rows = []

        for row in journal_rows:

            if row.get("timestamp") != timestamp_to_delete:
                remaining_rows.append(row)

        # Rewrite CSV
        with open(
            JOURNAL_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=CSV_FIELDS,
                extrasaction="ignore"
            )

            writer.writeheader()

            for row in remaining_rows:
                clean_row = {}

                for field in CSV_FIELDS:
                    value = row.get(field, "")

                    # HARD SAFETY: remove None keys/values
                    if value is None:
                        value = ""

                    clean_row[field] = value

                writer.writerow(clean_row)

        load_journal()

        return True

    except Exception as e:

        messagebox.showerror(
            "Delete Error",
            str(e)
        )

        return False

# ==========================================================
# ADVANCED JOURNAL ENTRY EDITOR
# ==========================================================
def open_entry_editor(event=None):

    selected = tree.selection()

    if not selected:
        return

    item_id = selected[0]
    values = tree.item(item_id, "values")

    selected_timestamp = values[0]
    entry_timestamp = selected_timestamp

    row_data = None

    # Find FULL matching CSV row
    for row in journal_rows:

        if row.get("timestamp") == selected_timestamp:
            row_data = row
            break

    if row_data is None:
        messagebox.showerror(
            "Error",
            "Unable to locate journal entry."
        )
        return

    # ======================================================
    # POPUP WINDOW
    # ======================================================
    popup = tk.Toplevel(root)
    popup.title(f"Trade Journal Entry - {row_data.get('ticker','')}")
    popup.geometry("800x650")
    popup.configure(bg="#f2f2f2")

    # ======================================================
    # NOTEBOOK / TABS
    # ======================================================
    notebook = ttk.Notebook(popup)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)

    analysis_tab = tk.Frame(notebook, bg="#f2f2f2")
    trade_tab = tk.Frame(notebook, bg="#f2f2f2")
    notes_tab = tk.Frame(notebook, bg="#f2f2f2")
    management_tab = tk.Frame(notebook, bg="#f2f2f2")    

    notebook.add(analysis_tab, text="Analysis")
    notebook.add(trade_tab, text="Trade")
    notebook.add(notes_tab, text="Notes")
    notebook.add(management_tab, text="Management")

    # ======================================================
    # TRADE TAB
    # ======================================================
    FIELD_LABELS = {
        "timestamp": "Entry Date",
        "ticker": "Ticker",
        "account": "Account Size",
        "risk_dollar": "Risk Dollar",
        "stop": "Stop Loss",
        "ladder_1_price": "Range High",
        "ladder_1_shares": "Range High Shares",
        "ladder_1_total": "Range High Total",
        "ladder_2_price": "Range Low",
        "ladder_2_shares": "Range Low Shares",
        "ladder_2_total": "Range Low Total",
        "ladder_3_price": "Wave 1 Retracement",
        "ladder_4_price": "Shakeout",
        "buy_now_price": "Buy Now Price",
        "buy_now_shares": "Buy Now Shares",
        "buy_now_total": "Buy Now Total"
    }

    popup_vars = {}

    trade_fields = [
        "ticker",
        "account",
        "risk_dollar",
        "stop",

        "ladder_1_price",
        "ladder_1_shares",
        "ladder_1_total",
        "ladder_2_price",
        "ladder_2_shares",
        "ladder_2_total",
        "ladder_3_price",
        "ladder_4_price",

        "buy_now_price",
        "buy_now_shares",
        "buy_now_total"
    ]

    row_index = 0

    for field in trade_fields:

        tk.Label(
            trade_tab,
            text=FIELD_LABELS.get(field, field),
            font=("Arial", 11, "bold"),
            bg="#f2f2f2"
        ).grid(row=row_index, column=0, sticky="w", padx=10, pady=6)

        var = tk.StringVar(value=row_data.get(field, ""))

        popup_vars[field] = var

        entry = tk.Entry(
            trade_tab,
            textvariable=var,
            font=("Arial", 11),
            width=30
        )

        entry.grid(row=row_index, column=1, padx=10, pady=6)

        row_index += 1

    # ======================================================
    # LIVE RECALC
    # ======================================================
    def popup_recalc(*args):

        try:
            risk_dollar = float(popup_vars["risk_dollar"].get())
            stop = float(popup_vars["stop"].get())
            buy_now = float(popup_vars["buy_now_price"].get())

            risk_per_share = buy_now - stop

            if risk_per_share <= 0:
                return

            shares = risk_dollar / risk_per_share
            total = shares * buy_now

            popup_vars["buy_now_shares"].set(
                round(shares, 2)
            )

            popup_vars["buy_now_total"].set(
                round(total, 2)
            )

        except:
            pass

    # Auto-update calculations
    popup_vars["risk_dollar"].trace_add("write", popup_recalc)
    popup_vars["stop"].trace_add("write", popup_recalc)
    popup_vars["buy_now_price"].trace_add("write", popup_recalc)

    # ======================================================
    # NOTES TAB
    # ======================================================
    tk.Label(
        notes_tab,
        text="Trade Notes / Journal Notes",
        font=("Arial", 12, "bold"),
        bg="#f2f2f2"
    ).pack(anchor="w", padx=10, pady=(10,5))

    notes_text = st.ScrolledText(
        notes_tab,
        wrap="word",
        font=("Courier", 10)
    )

    notes_text.pack(fill="both", expand=True, padx=10, pady=10)

    notes_text.insert(
        "1.0",
        row_data.get("trade_notes", "")
    )

    # ======================================================
    # ANALYSIS TAB
    # ======================================================
    top_analysis_frame = tk.Frame(
        analysis_tab,
        bg="#f2f2f2"
    )

    top_analysis_frame.pack(fill="x")

    tk.Label(
        top_analysis_frame,
        text="Institutional Analysis / AI Response",
        font=("Arial", 12, "bold"),
        bg="#f2f2f2"
    ).pack(side="left", padx=10, pady=10)

    ticker_name = row_data.get("ticker", "").strip()

    if ticker_name:

        def copy_prompt():
            
            enriched_row = row_data.copy()

            snapshot = rge.get_trade_snapshot()

            enriched_row["buy_now_price"] = snapshot.get("entry_price", enriched_row.get("buy_now_price", ""))
            enriched_row["buy_now_shares"] = snapshot.get("shares", enriched_row.get("buy_now_shares", ""))
            enriched_row["buy_now_total"] = snapshot.get("trade_total", enriched_row.get("buy_now_total", ""))

            enriched_row["account"] = snapshot.get("account", enriched_row.get("account", ""))
            enriched_row["risk_dollar"] = snapshot.get("risk_dollar", enriched_row.get("risk_dollar", ""))
            enriched_row["stop"] = snapshot.get("stop", snapshot.get("stop_loss", enriched_row.get("stop", "")))            

            generated_prompt = generate_signal_template(
                build_prompt_row(row_data)
            )

            popup.clipboard_clear()
            popup.clipboard_append(generated_prompt)

            messagebox.showinfo(
                "Copied",
                "Generated prompt copied to clipboard."
            )

        tk.Button(
            top_analysis_frame,
            text="COPY GENERATED PROMPT",
            font=("Arial", 10, "bold"),
            bg="#1976d2",
            fg="white",
            command=copy_prompt
        ).pack(side="right", padx=10)

    analysis_text = st.ScrolledText(
        analysis_tab,
        wrap="word",
        font=("Courier", 10)
    )

    analysis_text.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    analysis_text.insert(
        "1.0",
        row_data.get("analysis_notes", "")
    )

    # ======================================================
    # MANAGEMENT TAB
    # ======================================================
    management_container = tk.Frame(
        management_tab,
        bg="#f2f2f2"
    )

    management_container.pack(
        fill="both",
        expand=True
    )

    # ======================================================
    # TOP PANEL (GENERATED PROMPT)
    # ======================================================
    top_management_prompt_frame = tk.Frame(
        management_container,
        bg="#f2f2f2",
        height=260
    )

    top_management_prompt_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(10, 5)
    )

    top_management_prompt_frame.pack_propagate(False)

    top_management_header = tk.Frame(
        top_management_prompt_frame,
        bg="#f2f2f2"
    )

    top_management_header.pack(fill="x")

    tk.Label(
        top_management_header,
        text="Generated Trade Management Prompt",
        font=("Arial", 12, "bold"),
        bg="#f2f2f2"
    ).pack(side="left")

    management_prompt_text = st.ScrolledText(
        top_management_prompt_frame,
        wrap="word",
        font=("Courier", 10),
        height=12
    )

    management_prompt_text.pack(
        fill="both",
        expand=True,
        pady=(5, 0)
    )

    # ======================================================
    # GENERATED MANAGEMENT PROMPT
    # ======================================================
    generated_management_prompt = f"""
    You are a seasoned 30 year institutional trader.

    Analyze the following ticker information, as of today's new and available information, and determine:

    - Multi timeframe, top down analysis. 
    - Swing trade focus, 1H-1D entry execution  
    - Profit preservation, 15M-1H trade management    
    - Whether price structure suggests continuation, compression, or failure
    - Candlestick pattern and volume interaction     
    - Fibonacci support/resistance interaction
    - If the trade still maintains favorable institutional asymmetry
    - Whether current positioning aligns with Wyckoff accumulation/distribution behavior
    - Potential Top Down Multi timeframe Elliott Wave count 
    - Elliott Wave continuation or invalidation conditions
    - Signs of institutional absorption or liquidity exit
    - Trade management improvements
    - Whether the active stop placement remains structurally valid
    - Whether stop placement should be tightened, widened, or trailed
    - If the position should be risk-reduced, scaled, or expanded
    - Risk/reward profile changes
    - Position sizing adjustments
    - Exit planning
    - Partial profit strategies
    - Scenario planning for bullish, bearish, and neutral outcomes
    - Analysis primarily focused on new "Trade Notes" and "Analysis Notes"

    Provide detailed institutional-level trade management analysis.
    
    ==================================================
    TRADE NOTES
    ==================================================

    {row_data.get("trade_notes","")}

    ==================================================
    PREVIOUS NOTES
    ==================================================

    {row_data.get("management_notes","")}

    ==================================================
    UPDATED ANALYSIS DATA
    ==================================================

    {row_data.get("analysis_notes","")}
    """

    management_prompt_text.insert(
        "1.0",
        generated_management_prompt
    )

    management_prompt_text.config(
        state="disabled"
    )

    # ======================================================
    # COPY BUTTON
    # ======================================================
    def copy_management_prompt():

        popup.clipboard_clear()

        popup.clipboard_append(
            generated_management_prompt
        )

        messagebox.showinfo(
            "Copied",
            "Management prompt copied to clipboard."
        )

    tk.Button(
        top_management_header,
        text="COPY PROMPT",
        font=("Arial", 10, "bold"),
        bg="#1976d2",
        fg="white",
        command=copy_management_prompt
    ).pack(side="right")

    # ======================================================
    # BOTTOM PANEL (EDITABLE NOTES)
    # ======================================================
    bottom_management_frame = tk.Frame(
        management_container,
        bg="#f2f2f2",
        height=260
    )

    bottom_management_frame.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(5, 10)
    )

    bottom_management_frame.pack_propagate(False)

    tk.Label(
        bottom_management_frame,
        text="Trade Management / Position Planning Notes",
        font=("Arial", 12, "bold"),
        bg="#f2f2f2"
    ).pack(anchor="w")

    management_text = st.ScrolledText(
        bottom_management_frame,
        wrap="word",
        font=("Courier", 10),
        height=12
    )

    management_text.pack(
        fill="both",
        expand=True,
        pady=(5, 0)
    )

    management_text.insert(
        "1.0",
        row_data.get("management_notes", "")
    )
    
    def update_current_entry():

        try:
            updated_rows = []

            for row in journal_rows:

                # match selected entry
                if row.get("timestamp") == entry_timestamp:

                    updated_row = {}

                    for field in CSV_FIELDS:

                        if field == "timestamp":
                            # keep original timestamp (important for identity)
                            updated_row[field] = entry_timestamp

                        elif field == "trade_notes":
                            updated_row[field] = notes_text.get("1.0", tk.END).strip()

                        elif field == "analysis_notes":
                            updated_row[field] = analysis_text.get("1.0", tk.END).strip()
                            
                        elif field == "management_notes":
                            updated_row[field] = management_text.get("1.0", tk.END).strip()                            

                        elif field in popup_vars:
                            updated_row[field] = popup_vars[field].get()

                        else:
                            updated_row[field] = ""

                    updated_rows.append(updated_row)

                else:
                    updated_rows.append(row)

            # rewrite CSV completely (safe overwrite)
            with open(JOURNAL_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(updated_rows)

            # refresh global state + UI
            load_journal()

            messagebox.showinfo(
                "Updated",
                "Entry successfully updated."
            )

            popup.destroy()

        except Exception as e:
            messagebox.showerror(
                "Update Error",
                str(e)
            )
            
    def export_management_prompt_to_analysis_file(ticker: str, prompt: str):

        try:
            # =====================================================
            # SAFE TICKER
            # =====================================================
            safe_ticker = ticker.strip().upper() if ticker else "UNKNOWN"

            # =====================================================
            # ANALYSIS ROOT (CORRECT STRUCTURE)
            # =====================================================
            base_dir = os.path.join(
                get_project_root(),
                "data",
                "analysis",
                safe_ticker
            )

            os.makedirs(base_dir, exist_ok=True)

            # =====================================================
            # FILE NAME
            # =====================================================
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{safe_ticker}_{timestamp}.txt"

            file_path = os.path.join(base_dir, filename)

            # =====================================================
            # WRITE FILE
            # =====================================================
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(prompt)

            print(f"[ANALYSIS EXPORT] Saved: {file_path}")

            return file_path

        except Exception as e:
            print("Analysis export error:", e)
            return None
        
    # ======================================================
    # SAVE NEW ENTRY
    # ======================================================
    def save_as_new():

        try:

            row_dict = {}

            for field in CSV_FIELDS:
                if field == "timestamp":
                    row_dict[field] = datetime.now().isoformat()

                elif field == "trade_notes":
                    row_dict[field] = notes_text.get("1.0", tk.END).strip()

                elif field == "analysis_notes":
                    row_dict[field] = analysis_text.get("1.0", tk.END).strip()

                elif field == "management_notes":
                    row_dict[field] = management_text.get("1.0", tk.END).strip()

                else:
                    row_dict[field] = popup_vars.get(field).get() if field in popup_vars else ""

            # =====================================================
            # WRITE TO JOURNAL CSV
            # =====================================================
            with open(JOURNAL_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writerow(row_dict)

            load_journal()

            # =====================================================
            # GENERATE MANAGEMENT PROMPT
            # =====================================================
            generated_prompt = generated_management_prompt

            # =====================================================
            # EXPORT TO ANALYSIS DIRECTORY (NEW FEATURE)
            # =====================================================
            ticker = row_dict.get("ticker", "UNKNOWN")

            file_path = export_management_prompt_to_analysis_file(
                ticker,
                generated_prompt
            )

            # =====================================================
            # SUCCESS MESSAGE
            # =====================================================
            msg = "New journal entry saved successfully."

            if file_path:
                msg += f"\n\nAnalysis file created:\n{file_path}"

            messagebox.showinfo(
                "Saved",
                msg
            )

            popup.destroy()

        except Exception as e:

            messagebox.showerror(
                "Save Error",
                f"{e}"
            )
            
    # ======================================================
    # DELETE ENTRY
    # ======================================================
    def delete_current_entry():

        deleted = delete_journal_entry(
            entry_timestamp
        )

        if deleted:

            messagebox.showinfo(
                "Deleted",
                "Journal entry deleted successfully."
            )

            popup.destroy()
            
    # ======================================================
    # BUTTON BAR
    # ======================================================
    bottom_frame = tk.Frame(
        popup,
        bg="#f2f2f2"
    )

    bottom_frame.pack(fill="x", pady=5)

    tk.Button(
        bottom_frame,
        text="UPDATE CURRENT ENTRY",
        font=("Arial", 11, "bold"),
        bg="#1565c0",
        fg="white",
        padx=20,
        pady=10,
        command=update_current_entry
    ).pack(side="left", padx=10)

    tk.Button(
        bottom_frame,
        text="SAVE AS NEW ENTRY",
        font=("Arial", 11, "bold"),
        bg="#43a047",
        fg="white",
        padx=20,
        pady=10,
        command=save_as_new
    ).pack(side="left", padx=10)
    
    tk.Button(
        bottom_frame,
        text="DELETE ENTRY",
        font=("Arial", 11, "bold"),
        bg="#b71c1c",
        fg="white",
        padx=20,
        pady=10,
        command=delete_current_entry
    ).pack(side="left", padx=10)
    
    tk.Button(
        bottom_frame,
        text="CLOSE",
        font=("Arial", 11, "bold"),
        bg="#d32f2f",
        fg="white",
        padx=20,
        pady=10,
        command=popup.destroy
    ).pack(side="right", padx=10)

tree.bind("<Double-1>", open_entry_editor)

# ==========================================================
# LOAD JOURNAL
# ==========================================================
def load_journal():

    tree.delete(*tree.get_children())

    global template_journal_data
    global template_tickers
    global journal_rows

    template_journal_data = load_journal_data()
    template_tickers = sorted(template_journal_data.keys())

    update_template_panel()

    journal_rows = []
    journal_preview_rows = []

    with open(
        JOURNAL_FILE,
        newline="",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            clean_row = {
                k: (v if v is not None else "")
                for k, v in row.items()
            }

            # Ensure missing columns exist
            for field in CSV_FIELDS:
                if field not in clean_row:
                    clean_row[field] = ""
                
            journal_rows.append(clean_row)
            journal_preview_rows.append(build_preview_row(clean_row))

    # Apply active filters after loading
    apply_journal_filters()

def fmt_trade_value(val):
    try:
        val = str(val).replace("@","").replace(",","")
        return f"{float(val):.4f}"
    except:
        return val


PRICE_LIKE_COLS = {
    "Price",
    "Avg Price",
    "Limit Price",
    "Filled Price",
    "Amount",
    "Value",
    "Total",
}

# ==========================================================
# TEMPLATE PANEL
# ==========================================================
template_journal_data = {}
template_tickers = []
template_ticker_var = tk.StringVar()
template_frame = tk.Frame(left, bg="#f2f2f2")
template_frame.pack(pady=10, fill="both", expand=True)

tk.Label(template_frame, text="Prompt Generator",
         font=("Arial",10,"bold"), bg="#f2f2f2").pack(pady=(0,5))

template_text_widget = tk.Text(template_frame, wrap="word", font=("Courier",10), height=20)
template_text_widget.pack(fill="both", expand=True, padx=5, pady=2)
template_text_widget.config(state="disabled")

# ==========================================================
# FOOTER (Below Prompt Generator)
# ==========================================================
footer = tk.Frame(root, bg="#f2f2f2", height=22)
footer.pack(side="bottom", fill="x")
footer.pack_propagate(False)

tk.Label(
    footer,
    text="© 2026 Newell Trading Group. All rights reserved.",
    font=("Arial", 9),
    bg="#f2f2f2"
).pack(side="left", padx=10)

links_frame = tk.Frame(footer, bg="#f2f2f2")
links_frame.pack(side="right", padx=10)

def create_link_label(parent, text, url=None, callback=None):
    def on_click(event):
        if url:
            webbrowser.open(url)
        elif callback:
            callback()
    lbl = tk.Label(
        parent,
        text=text,
        font=("Arial", 9, "underline"),
        fg="blue",
        cursor="hand2",
        bg="#f2f2f2"
    )
    lbl.pack(side="left", padx=5)
    lbl.bind("<Button-1>", on_click)

create_link_label(links_frame, "Webull Data", callback=run_webull_update)
create_link_label(links_frame, "Update Data", callback=run_yahoo_update)
create_link_label(links_frame, "Watchlist", callback=show_watchlist_popup)
create_link_label(links_frame, "Signals DB", callback=show_signals_popup)
create_link_label(links_frame, "Analysis Directory", callback=show_analysis_files_popup)
create_link_label(links_frame, "Scraper Files", callback=show_scraper_files_popup)
create_link_label(links_frame, "Account Ledger", callback=lambda: show_account_ledger_popup(root))
create_link_label(links_frame, "Portfolio Overview", callback=open_portfolio_overview)
create_link_label(links_frame, "Ticker Screener", url="https://finviz.com/screener.ashx?v=211&f=fa_pe_profitable,sh_avgvol_o1000,sh_price_u20,ta_sma50_pb,targetprice_above")
create_link_label(links_frame, "Webull", url="https://a.webull.com/3DbgLHTELPBRR5YmGC")
create_link_label(links_frame, "SEC Filings", url="https://www.sec.gov/edgar/searchedgar/companysearch")
create_link_label(links_frame, "Macro Calendar", url="https://www.forexfactory.com/calendar")
create_link_label(links_frame, "Help", callback=show_readme)
create_link_label(links_frame, "Plan", callback=show_plan_popup)
create_link_label(links_frame, "Developer Notes", callback=show_developer_notes_popup)

# ==========================================================
# DEFAULT PROMPT GENERATOR TEXT
# ==========================================================
DEFAULT_PROMPT_TEXT = """
USE THIS PROMPT TO FIND TICKERS

Based on the available information as of today, provide a list of 35 tickers that meet the requirements below:
Institutional Asymmetry Screener Framework
Optimized for:
Institutional accumulation detection
Structural imbalance setups
Low-float momentum continuation
Catalyst-driven expansion
Short squeeze mechanics
Early-stage repricing
Multi-day/multi-week runners
Survivable small/mid-cap growth
Early Expansion Regimes
-Especially compression-to-expansion transitions.


Do not include tickers that are unreasonably price for my risk management profile and account value (no tickers above $100)

The goal is to screen for:

accelerating structural conditions before full market repricing occurs.

CORE PHILOSOPHY

Price is treated as:

a contextual variable
a participation indicator
a liquidity behavior signal

—not a hard filter.

Instead, the system prioritizes:

liquidity expansion
float constraints
growth acceleration
institutional behavior
balance-sheet survivability
ownership shifts
catalyst amplification
TIER 1 — EARLY ACCUMULATION SCREENER
“Pre-Discovery Institutional Rotation”
Purpose

Find companies before broad momentum ignition.

Ideal Environment
stealth accumulation
early RVOL increase
improving fundamentals
institutional positioning beginning
Filter Configuration
Filter	Setting
Avg Volume	Over 750K
Relative Volume	Over 1.5
Current Volume	Over 500K
Float	Under 20M
Shares Outstanding	Under 50M
Sales Growth Q/Q	Over 15%
EPS Growth Q/Q	Over 15%
Current Ratio	Over 1.5
Debt/Equity	Under 0.75
Insider Ownership	Over 5%
Insider Transactions	Positive
Institutional Transactions	Positive
Institutional Ownership	Under 35%
Target Price	Above Price
Analyst Recom	Buy or Better
Price Interpretation
Price Behavior	Meaning
Sub-$2	Early speculative accumulation
$2–$10	Strongest asymmetrical discovery zone
$10+	Institutional positioning phase

TIER 2 — MOMENTUM EXPANSION SCREENER
“Institutional Discovery Phase”
Purpose

Find stocks actively transitioning into momentum expansion.

Ideal Environment
strong RVOL
catalyst confirmation
institutional discovery
breakout continuation
Filter Configuration
Filter	Setting
Avg Volume	Over 1M
Relative Volume	Over 3
Current Volume	Over 2M
Float	Under 30M
Shares Outstanding	Under 75M
Sales Growth Q/Q	Over 20%
EPS Growth Q/Q	Over 20%
Revenue Surprise	Positive
Earnings Surprise	Positive
ROE	Over 8%
Current Ratio	Over 1.5
Quick Ratio	Over 1
Debt/Equity	Under 1
Gross Margin	Positive
Insider Ownership	Over 5%
Institutional Transactions	Positive
Short Float	Over 10%
Price Interpretation
Price Behavior	Meaning
Low price + RVOL spike	Retail ignition
Mid-price + RVOL spike	Institutional discovery
Higher-price + RVOL spike	Fund rotation

TIER 3 — HIGH-PROBABILITY CONTINUATION SCREENER
“Quality Momentum Persistence”
Purpose

Find stocks likely to continue after initial expansion.

Ideal Environment
strong balance sheet
improving margins
real revenue growth
sustained participation
Filter Configuration
Filter	Setting
Relative Volume	Over 2
Avg Volume	Over 2M
Sales Growth Q/Q	Over 25%
EPS Growth Q/Q	Over 25%
EPS Growth Next Year	Positive
Revenue Surprise	Positive
ROE	Over 10%
Gross Margin	Over 20%
Operating Margin	Positive
Net Margin	Positive
Current Ratio	Over 2
Debt/Equity	Under 0.75
Institutional Transactions	Positive
Insider Transactions	Positive
Price Interpretation
Price Structure	Interpretation
Tight consolidation after expansion	Institutional absorption
Rising price + stable RVOL	Controlled continuation
Higher price + improving margins	Sustainable repricing

TIER 4 — PARABOLIC SQUEEZE SCREENER
“Liquidity Vacuum / Forced Repricing”
Purpose

Find explosive imbalance conditions.

Ideal Environment
constrained float
elevated short pressure
abnormal participation
aggressive catalyst
Filter Configuration
Filter	Setting
Float	Under 10M
Shares Outstanding	Under 30M
Relative Volume	Over 5
Current Volume	Over 5M
Avg Volume	Over 1M
Short Float	Over 20%
Sales Growth Q/Q	Positive
Revenue Surprise	Positive
Insider Ownership	Over 5%
Institutional Transactions	Positive
Debt/Equity	Under 1
Current Ratio	Over 1.2
Price Interpretation
Price Structure	Meaning
Low price + tiny float	Halt/squeeze probability
Mid-price + short pressure	Controlled squeeze
Higher price + constrained float	Institutional scarcity

TIER 5 — INSTITUTIONAL QUALITY MOMENTUM
“Best Overall Blend”
Purpose

Highest overall expectancy configuration.

Ideal Environment
accelerating fundamentals
expanding participation
institutional accumulation
survivable balance sheet
constrained supply
Filter Configuration
Filter	Setting
Avg Volume	Over 1M
Relative Volume	Over 3
Float	Under 30M
Shares Outstanding	Under 75M
Sales Growth Q/Q	Over 20%
EPS Growth Q/Q	Over 20%
EPS Growth Next Year	Positive
Revenue Surprise	Positive
Earnings Surprise	Positive
ROE	Over 8%
Current Ratio	Over 1.5
Quick Ratio	Over 1
Debt/Equity	Under 0.8
LT Debt/Equity	Under 0.75
Gross Margin	Over 20%
Insider Ownership	Over 5%
Insider Transactions	Positive
Institutional Ownership	Under 40%
Institutional Transactions	Positive
Short Float	Over 10%
Structural Interpretation Framework
What You Want To See
Structural Behavior	Interpretation
Rising RVOL + stable float	Supply constraint
Revenue acceleration + rising volume	Real repricing
Insider buying + institutional buying	Alignment
Low debt + strong current ratio	Lower dilution risk
Positive surprises + rising participation	Momentum persistence
Short pressure + strong fundamentals	Forced repricing potential
Optimal Price Behavior by Tier
Price Context	Interpretation
Low price + improving fundamentals	Early asymmetry
Mid-price + rising institutional activity	Discovery phase
Higher price + sustained margins	Leadership trend
Rising price + shrinking supply	Squeeze probability
Stable price + expanding RVOL	Accumulation
MOST IMPORTANT COMBINATIONS
Combination #1 — “Stealth Accumulation”
RVOL > 1.5
Float < 20M
Institutional transactions positive
Sales growth accelerating
Insider buying
Combination #2 — “Institutional Discovery”
RVOL > 3
Revenue surprise positive
EPS growth accelerating
Short float > 10%
Float constrained
Combination #3 — “Forced Repricing”
Short float > 20%
Float < 10M
RVOL > 5
Positive catalyst
Improving fundamentals
FINAL MASTER PHILOSOPHY

The best prospects are usually NOT:

the cheapest stocks
the highest short-interest stocks
the lowest float stocks

The best prospects are usually:

Companies where:
operational metrics are accelerating,
liquidity participation is expanding,
institutional positioning is changing,
supply is constrained,
catalysts are active,
and price has not yet fully reflected the structural shift.

That is the highest expectancy institutional asymmetry framework.
"""

# ==========================================================
# TEMPLATE PANEL UPDATE
# ==========================================================
def update_template_panel(event=None):

    template_text_widget.config(state="normal")

    template_text_widget.delete(
        "1.0",
        tk.END
    )

    template_text_widget.insert(
        tk.END,
        DEFAULT_PROMPT_TEXT
    )

    template_text_widget.config(
        state="disabled"
    )

# ==========================================================
# LOAD EXECUTED TRADES
# ==========================================================
def load_executed_trades():

    trades = load_webull_executions()

    trades_table.delete(
        *trades_table.get_children()
    )

    if not trades:
        return

    ordered_cols = ["Placed Time"]

    ordered_cols += [
        c for c in trades[0].keys()
        if c not in ("Placed Time", "Status")
    ]

    trades_table["columns"] = ordered_cols

    for c in ordered_cols:

        label = "Date" if c == "Placed Time" else c

        trades_table.heading(
            c,
            text=label
        )

        trades_table.column(
            c,
            width=110,
            anchor="center"
        )

    for r in trades:

        row_vals = []

        for c in ordered_cols:

            val = r.get(c, "")

            if c in PRICE_LIKE_COLS:

                try:

                    val_clean = (
                        str(val)
                        .replace("@", "")
                        .replace(",", "")
                    )

                    val_float = float(val_clean)

                    val = "{:g}".format(val_float)

                except:
                    pass

            row_vals.append(val)

        trades_table.insert(
            "",
            "end",
            values=row_vals
        )


# ==========================================================
# LOAD EXECUTED TRADE NOTES
# ==========================================================
def load_executed_trade_notes():
    return etn.load_executed_trade_notes(EXECUTED_TRADES_NOTES_FILE)

# ==========================================================
# REFRESH EXECUTED TRADE ANALYSIS CONTEXT
# ==========================================================
def refresh_executed_trade_context(row_data):
    etn.refresh_executed_trade_context(
        row_data,
        template_ticker_var,
        update_template_panel
    )
        
# ==========================================================
# EXECUTED TRADE PROMPT GENERATOR
# ==========================================================
def generate_executed_trade_prompt(row_data):

    # Refresh active analysis context
    refresh_executed_trade_context(row_data)
    
    safe_history_block = globals().get(
        "history_block",
        ""
    )

    safe_daily_volume_block = globals().get(
        "daily_volume_block",
        ""
    )

    safe_intraday_block = globals().get(
        "intraday_block",
        ""
    )

    safe_volume_block = globals().get(
        "volume_block",
        ""
    )

    safe_financial_block = globals().get(
        "financial_block",
        ""
    )

    safe_historical_results = globals().get(
        "historical_results",
        ""
    )

    safe_intraday_15m_prompt = globals().get(
        "intraday_15m_prompt",
        ""
    )

    safe_intraday_60m_prompt = globals().get(
        "intraday_60m_prompt",
        ""
    )

    template_text = """
You are a seasoned 30 year institutional trader.

Perform a complete institutional-grade post-trade review.

Focus heavily on:
- execution quality
- continuation vs redistribution
- volatility expansion
- institutional accumulation/distribution
- stop placement quality
- entry efficiency
- trade management analysis (primary focus)
- exit efficiency (if a sell entry, no short orders)
- scaling logic
- momentum alignment
- t-line continuation structures
- j-hook continuation probability
- rsi 80+ notification
- Elliott Wave context
- Wyckoff phase behavior
- Wyckoff point and figure analysis
- Fibonacci interaction
- trade management quality
- asymmetric opportunity evaluation
- trade psychology
- risk management effectiveness

====================================================
EXECUTED TRADE DATA
====================================================

"""

    for col in trades_table["columns"]:

        value = row_data.get(
            col,
            ""
        )

        if col in PRICE_LIKE_COLS:

            try:

                value_clean = (
                    str(value)
                    .replace("@", "")
                    .replace(",", "")
                )

                value_float = float(value_clean)

                value = f"{value_float:g}"

            except:
                pass

        template_text += f"{col}: {value}\n"

    template_text += f"""

====================================================
📊 DAILY HISTORICAL CONTEXT
====================================================

{safe_history_block}

====================================================
📊 DAILY VOLUME ANALYSIS
====================================================

{safe_daily_volume_block}

====================================================
📊 INTRADAY 60M CONTEXT
====================================================

{safe_intraday_block}

====================================================
📊 INTRADAY VOLUME ANALYSIS
====================================================

{safe_volume_block}

====================================================
📊 FINANCIAL METRICS
====================================================

{safe_financial_block}

====================================================
📊 PRICE ACTION ANALYSIS
====================================================

{safe_historical_results}

{safe_intraday_15m_prompt}

{safe_intraday_60m_prompt}

===========================
📊 Wyckoff Point & Figure Structure (Institutional Model)
===========================

{pnf_block}

{fractal_block}
====================================================

Required Analysis Sections:

🛑 Stop Quality Review
🎯 Exit Efficiency Review
📈 Trade Execution Quality
📉 Institutional Positioning
📊 Volume Participation Analysis
🧠 Momentum Alignment
🌊 Elliott Wave Context
📦 Wyckoff Phase Evaluation
📦 Wyckoff Point and Figure Evaluation
📐 Fibonacci Interaction
⚖️ Risk/Reward Efficiency
📈 Continuation Probability
📉 Redistribution Probability
🔥 Volatility Expansion Assessment
🪤 Trap / Liquidity Sweep Analysis
📌 T-Line Continuation Structure
📚 Lessons Learned
📋 Future Improvements
"""

    return template_text


# ==========================================================
# SINGLE CLICK -> UPDATE PROMPT PANEL
# ==========================================================
def executed_trade_selection_update(event=None):

    selected = trades_table.selection()

    if not selected:
        return

    item = selected[0]

    row_values = trades_table.item(
        item,
        "values"
    )

    row_data = {
        col: val
        for col, val in zip(
            trades_table["columns"],
            row_values
        )
    }

    template_text = generate_executed_trade_prompt(
        row_data
    )

    template_text_widget.config(
        state="normal"
    )

    template_text_widget.delete(
        "1.0",
        tk.END
    )

    template_text_widget.insert(
        tk.END,
        template_text
    )

    template_text_widget.config(
        state="disabled"
    )


# ==========================================================
# EXECUTED TRADE POPUP EDITOR
# ==========================================================
def open_executed_trade_editor(event=None):

    selected = trades_table.selection()

    if not selected:
        return

    item_id = selected[0]

    row_values = trades_table.item(
        item_id,
        "values"
    )

    row_data = {
        col: val
        for col, val in zip(
            trades_table["columns"],
            row_values
        )
    }

    ticker = (
        row_data.get("Ticker")
        or row_data.get("Symbol")
        or ""
    )

    placed_time = row_data.get(
        "Placed Time",
        ""
    )

    trade_id = f"{ticker}_{placed_time}"

    notes_map = load_executed_trade_notes()

    saved_notes = notes_map.get(
        trade_id,
        {}
    )

    template_text = generate_executed_trade_prompt(
        row_data
    )

    # ======================================================
    # POPUP
    # ======================================================
    popup = tk.Toplevel(root)

    popup.title(
        f"Executed Trade Review - {ticker}"
    )

    popup.geometry("1100x800")

    popup.configure(bg="#f2f2f2")

    notebook = ttk.Notebook(popup)

    notebook.pack(
        fill="both",
        expand=True,
        padx=5,
        pady=5
    )

    trade_tab = tk.Frame(notebook, bg="#f2f2f2")
    notes_tab = tk.Frame(notebook, bg="#f2f2f2")
    analysis_tab = tk.Frame(notebook, bg="#f2f2f2")
    management_tab = tk.Frame(notebook, bg="#f2f2f2")

    notebook.add(trade_tab, text="Trade")
    notebook.add(notes_tab, text="Notes")
    notebook.add(analysis_tab, text="Analysis")
    notebook.add(management_tab, text="Management")

    # ======================================================
    # TRADE TAB
    # ======================================================
    trade_canvas = tk.Canvas(
        trade_tab,
        bg="#f2f2f2",
        highlightthickness=0
    )

    scrollbar = ttk.Scrollbar(
        trade_tab,
        orient="vertical",
        command=trade_canvas.yview
    )

    scroll_frame = tk.Frame(
        trade_canvas,
        bg="#f2f2f2"
    )

    scroll_frame.bind(
        "<Configure>",
        lambda e: trade_canvas.configure(
            scrollregion=trade_canvas.bbox("all")
        )
    )

    trade_canvas.create_window(
        (0, 0),
        window=scroll_frame,
        anchor="nw"
    )

    trade_canvas.configure(
        yscrollcommand=scrollbar.set
    )

    trade_canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    popup_vars = {}

    row_index = 0

    for field in trades_table["columns"]:

        tk.Label(
            scroll_frame,
            text=field,
            font=("Arial", 11, "bold"),
            bg="#f2f2f2"
        ).grid(
            row=row_index,
            column=0,
            sticky="w",
            padx=10,
            pady=5
        )

        var = tk.StringVar(
            value=row_data.get(field, "")
        )

        popup_vars[field] = var

        tk.Entry(
            scroll_frame,
            textvariable=var,
            font=("Arial", 11),
            width=45
        ).grid(
            row=row_index,
            column=1,
            padx=10,
            pady=5
        )

        row_index += 1

    # ======================================================
    # NOTES TAB
    # ======================================================
    notes_text = st.ScrolledText(
        notes_tab,
        wrap="word",
        font=("Courier", 10)
    )

    notes_text.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    notes_text.insert(
        "1.0",
        saved_notes.get(
            "notes",
            ""
        )
    )

    # ======================================================
    # ANALYSIS TAB
    # ======================================================
    analysis_text = st.ScrolledText(
        analysis_tab,
        wrap="word",
        font=("Courier", 10)
    )

    analysis_text.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    analysis_text.insert(
        "1.0",
        saved_notes.get(
            "analysis_notes",
            template_text
        )
    )

    # ======================================================
    # MANAGEMENT TAB
    # ======================================================
    management_text = st.ScrolledText(
        management_tab,
        wrap="word",
        font=("Courier", 10)
    )

    management_text.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    management_text.insert(
        "1.0",
        saved_notes.get(
            "management_notes",
            ""
        )
    )

    # ======================================================
    # SAVE / UPDATE
    # ======================================================
    def update_executed_trade_entry():

        rows = []

        if os.path.exists(
            EXECUTED_TRADES_NOTES_FILE
        ):

            with open(
                EXECUTED_TRADES_NOTES_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                rows = list(
                    csv.DictReader(f)
                )

        updated = False

        for row in rows:

            if row.get("trade_id") == trade_id:

                row["trade_id"] = trade_id
                row["ticker"] = ticker
                row["placed_time"] = placed_time

                row["notes"] = notes_text.get(
                    "1.0",
                    tk.END
                ).strip()

                row["analysis_notes"] = analysis_text.get(
                    "1.0",
                    tk.END
                ).strip()

                row["management_notes"] = management_text.get(
                    "1.0",
                    tk.END
                ).strip()

                updated = True

        if not updated:

            rows.append({

                "trade_id": trade_id,

                "ticker": ticker,

                "placed_time": placed_time,

                "notes": notes_text.get(
                    "1.0",
                    tk.END
                ).strip(),

                "analysis_notes": analysis_text.get(
                    "1.0",
                    tk.END
                ).strip(),

                "management_notes": management_text.get(
                    "1.0",
                    tk.END
                ).strip()
            })

        with open(
            EXECUTED_TRADES_NOTES_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=EXECUTED_TRADE_NOTE_FIELDS
            )

            writer.writeheader()

            writer.writerows(rows)

        messagebox.showinfo(
            "Updated",
            "Executed trade review updated."
        )

    # ======================================================
    # BUTTON BAR
    # ======================================================
    bottom_frame = tk.Frame(
        popup,
        bg="#f2f2f2"
    )

    bottom_frame.pack(
        fill="x",
        pady=5
    )

    tk.Button(
        bottom_frame,
        text="UPDATE ENTRY",
        font=("Arial", 11, "bold"),
        bg="#1565c0",
        fg="white",
        padx=20,
        pady=10,
        command=update_executed_trade_entry
    ).pack(
        side="left",
        padx=10
    )

    tk.Button(
        bottom_frame,
        text="CLOSE",
        font=("Arial", 11, "bold"),
        bg="#d32f2f",
        fg="white",
        padx=20,
        pady=10,
        command=popup.destroy
    ).pack(
        side="right",
        padx=10
    )


# ==========================================================
# BINDINGS
# ==========================================================
trades_table.bind(
    "<<TreeviewSelect>>",
    executed_trade_selection_update
)

trades_table.bind(
    "<Double-1>",
    open_executed_trade_editor
)

load_journal()
load_executed_trades()
auto_calc_stop()

if should_show_howto():
    root.after(500, show_howto_popup)


root.mainloop()
