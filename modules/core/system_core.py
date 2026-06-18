"""
SYSTEM CORE HUB
Single unified access layer for full trading system
SQLite-first architecture (CSV = ingestion only)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
import tkinter.scrolledtext as st

import csv
import os
from datetime import datetime
import uuid
import webbrowser

import pandas as pd
import yfinance as yf

# =========================================================
# INTERNAL MODULES
# =========================================================
from modules import yahooFetcher

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
from modules.accountLedger import show_account_ledger_popup

from modules.pointFigureWyckoff import (
    run_wyckoff_pnf_analysis,
    format_for_journal as format_pnf_for_journal
)

from modules.fractalEngine import (
    analyze_wyckoff_fractals,
    format_for_journal as format_fractal_for_journal
)

from modules.candlestickAnalysis import (
    analyze_multitimeframe_candlesticks,
    format_candlestick_for_journal
)

from modules.liquidity_phase_engine import run_liquidity_phase_engine

from modules.liquidity_multi_timeframe_engine import (
    run_liquidity_multi_timeframe_engine
)

from modules.dtfm_analysis import analyze_dual_timeframe_momentum
from modules.relative_strength_engine import build_relative_strength_block
from modules.risk_engine import get_latest_close, evaluate_stop_loss

# =========================================================
# DATABASE CORE
# =========================================================
from modules.database_manager import DatabaseManager
from modules.database_ui import launch_database_viewer  # FIXED IMPORT

# =========================================================
# DATA LAYER
# =========================================================
class SystemData:

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_trades(self):
        return self.db.get_trades()

    def get_webull(self):
        return self.db.get_webull()

    def get_module_outputs(self):
        return self.db.get_outputs()

    def get_ledger(self):
        return self.db.fetch_all("SELECT * FROM ledger ORDER BY id DESC")

    # FIXED: SQLite ONLY
    def get_stock(self, ticker: str, timeframe: str):
        return self.db.get_stock(ticker.upper(), timeframe)

    # FIXED: SQLite ONLY (no filesystem)
    def search_stock_files(self, ticker: str):
        result = self.db.fetch_all("""
            SELECT DISTINCT timeframe
            FROM stock_ohlcv
            WHERE ticker=?
        """, (ticker.upper(),))

        return [r["timeframe"] for r in result]

    # REQUIRED RELATIONAL WRAPPERS
    def trade_history(self, ticker):
        return self.db.get_trades_with_price_context(ticker)

    def symbol_activity(self, ticker):
        return self.db.get_symbol_activity(ticker)

    def broker_links(self, ticker):
        return self.db.get_broker_trade_links(ticker)


# =========================================================
# SYSTEM CORE
# =========================================================
class SystemCore:

    def __init__(self):
        self.db = DatabaseManager()
        self.data = SystemData(self.db)

    def database(self):
        return self.db

    def launch_db_viewer(self):
        launch_database_viewer()

    def close_price(self, ticker):
        return get_latest_close(ticker)

    def risk_check(self, *args, **kwargs):
        return evaluate_stop_loss(*args, **kwargs)

    def stock(self, ticker, timeframe):
        return self.data.get_stock(ticker, timeframe)

    def trades(self):
        return self.data.get_trades()

    def ledger(self):
        return self.data.get_ledger()

    def webull(self):
        return self.data.get_webull()

    def module_outputs(self):
        return self.data.get_module_outputs()


system = SystemCore()