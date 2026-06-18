"""
journal_dependencies.py

Centralized import hub for journal.py

Instead of importing dozens of modules individually,
journal.py can simply do:

from modules.journal_dependencies import *

"""

# ==========================================================
# INTERNAL MODULES
# ==========================================================

import modules.journal_filters as jf
import modules.executed_trades_notes as etn

from modules import yahooFetcher

from modules.financialAnalysis import format_financial_prompt
from modules.historicalAnalysis import analyze_historical_data
from modules.tlineAnalysis import analyze_tline_intraday

from modules.portfolio_overview import PortfolioOverviewPopup

from modules.pointFigureWyckoff import (
    run_wyckoff_pnf_analysis,
    format_for_journal as format_pnf_for_journal
)

from modules.fractalEngine import (
    analyze_wyckoff_fractals,
    format_for_journal as format_fractal_for_journal
)

from modules.accountLedger import show_account_ledger_popup

from modules.candlestickAnalysis import (
    analyze_multitimeframe_candlesticks,
    format_candlestick_for_journal
)

from modules.liquidity_phase_engine import (
    run_liquidity_phase_engine
)

from modules.liquidity_multi_timeframe_engine import (
    run_liquidity_multi_timeframe_engine
)

from modules.dtfm_analysis import (
    analyze_dual_timeframe_momentum
)

from modules.relative_strength_engine import (
    build_relative_strength_block
)

from modules.risk_engine import (
    get_latest_close,
    evaluate_stop_loss
)

from modules.pinbarAnalysis import (
    analyze_pinbar
)

from modules.watchlist_popup import (
    WatchlistPopup
)

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

# ==========================================================
# STANDARD LIBRARIES
# ==========================================================

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import tkinter.font as tkFont
import tkinter.scrolledtext as st

import csv
import os
import uuid
import webbrowser

from datetime import datetime

# ==========================================================
# THIRD PARTY
# ==========================================================

import pandas as pd
import yfinance as yf

# ==========================================================
# EXPORTS
# ==========================================================

__all__ = [

    # aliases
    "jf",
    "etn",

    # tkinter
    "tk",
    "ttk",
    "messagebox",
    "tkFont",
    "st",

    # standard libs
    "csv",
    "os",
    "uuid",
    "webbrowser",
    "datetime",

    # third party
    "pd",
    "yf",

    # modules
    "yahooFetcher",
    "format_financial_prompt",
    "analyze_historical_data",
    "analyze_tline_intraday",
    "PortfolioOverviewPopup",
    "run_wyckoff_pnf_analysis",
    "format_pnf_for_journal",
    "analyze_wyckoff_fractals",
    "format_fractal_for_journal",
    "show_account_ledger_popup",
    "analyze_multitimeframe_candlesticks",
    "format_candlestick_for_journal",
    "run_liquidity_phase_engine",
    "run_liquidity_multi_timeframe_engine",
    "analyze_dual_timeframe_momentum",
    "build_relative_strength_block",
    "get_latest_close",
    "evaluate_stop_loss",
    "analyze_pinbar",
    "WatchlistPopup",

    # volumeAnalysis
    "rvol",
    "detect_volume_spike",
    "detect_volume_contraction",
    "up_volume_percentage",
    "down_volume_percentage",
    "obv",
    "obv_slope",
    "accumulation_distribution",
    "ad_slope",
    "large_volume_up_days",
    "large_volume_down_days",
    "institutional_accumulation_state",
]