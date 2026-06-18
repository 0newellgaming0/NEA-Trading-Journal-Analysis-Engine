# NEA28V1 — Institutional Trading Risk & Journal Engine - WIP

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-event--driven-lightgrey)
![UI](https://img.shields.io/badge/UI-Tkinter%20%2F%20Treeview-green)
![Data](https://img.shields.io/badge/data-CSV%20%2F%20Pandas-orange)
![Status](https://img.shields.io/badge/status-active-brightgreen)

---

## 📌 Overview

**NEA28V1** is a **desktop institutional trading journal, execution tracking system, and analysis engine** designed to replicate a professional-grade trade desk workflow.

It integrates:

- Multi-layer trade journaling (manual + executed trades)
- Institutional-grade prompt generation engine (LLM-ready analysis)
- Risk-adjusted position sizing system
- Wyckoff + Elliott + T-Line + Volume + Fibonacci analytical framework
- Multi-tab trade inspection UI (Trade / Notes / Analysis / Management)
- CSV-based persistence layer with full overwrite-safe updates
- Executed trade reconciliation engine (broker import support)
- Automated prompt export system for post-trade AI analysis

---

## 🧠 Core Philosophy

This system is built on one core principle:

> **Price is not a value — it is a representation of liquidity behavior.**

The system prioritizes:

- Institutional accumulation/distribution behavior
- Liquidity expansion & contraction
- Structural asymmetry (risk vs reward imbalance)
- Volume participation over price direction alone
- Multi-timeframe confluence (1M → Monthly)
- Execution quality over prediction accuracy

---

## 🏗️ System Architecture

NEA28V1 Trading System
│
├── 📊 DATA LAYER
│   ├── Journal CSV Engine
│   ├── Executed Trade Import Layer
│   ├── Multi-Timeframe Stock Data (1M → Monthly)
│   └── Analysis Export System
│
├── 🧠 STRATEGY ENGINE
│   ├── Wyckoff Structure Engine
│   ├── T-Line (EMA-8) System
│   ├── Volume & RVOL Engine
│   ├── Elliott Wave Context Layer
│   ├── Fibonacci Interaction Zones
│   └── Candlestick Pattern Engine
│
├── 📈 RISK ENGINE
│   ├── Position Sizing Model
│   ├── Stop Loss Validation System
│   ├── Ladder Entry Structuring
│   └── Risk/Reward Calibration
│
├── 🧾 JOURNAL SYSTEM
│   ├── Trade Lifecycle Editor
│   ├── Notes + Analysis Persistence
│   ├── CSV Safe Write System
│   └── Prompt Generation Engine
│
├── 🔁 EXECUTION SYSTEM
│   ├── Broker Trade Import (Webull compatible)
│   ├── Trade ID Mapping Layer
│   ├── Post-Trade Review Engine
│   └── Management Prompt Generator
│
└── 🖥️ UI LAYER (Tkinter)
    ├── Trade Table (TreeView)
    ├── Multi-Tab Notebook UI
    ├── Prompt Generator Panel
    ├── Analysis Console
    └── Execution Review Popups

---

## 📁 Folder Structure

/modules
/stock_data/
daily/
weekly/
intraday_1m/
intraday_5m/
intraday_15m/
intraday_30m/
intraday_60m/

/analysis
└── <TICKER>/
└── YYYY-MM-DD_HH-MM-SS.txt

journal.csv
executed_trades.csv
executed_trade_notes.csv

---

## 🧾 Core System Modules

---

# 📊 1. Journal Entry Editor System

### Purpose
The journal editor is the **primary trade lifecycle interface**.

It supports:

- Full trade editing (popup modal)
- Live recalculated position sizing
- Multi-tab structured analysis
- Trade note persistence
- Risk alignment validation
- Management prompt generation

---

### Features

#### Trade Tab
- Editable:
  - ticker
  - account size
  - risk dollar
  - stop loss
  - ladder entries (price / shares / totals)
  - buy-now execution block

#### Live Risk Engine

risk_per_share = buy_now_price - stop_loss
shares = risk_dollar / (risk_per_share)
total = shares * buy_now_price

---

#### Notes Tab
- Freeform trade journal notes
- Stored in CSV under `trade_notes`

---

#### Analysis Tab
- Institutional AI analysis input/output block
- Clipboard export of generated prompt

---

#### Management Tab
- Generated institutional management prompt
- Editable trade management commentary
- Position adjustment logic

---

# 🔁 2. Executed Trade Review Engine

### Purpose
Reconstructs **real broker executions into structured institutional analysis**

---

### Features

#### Trade Import Layer
- Loads executed trades via:
  - `load_webull_executions()`

#### Trade Mapping
trade_id = ticker + placed_time

---

#### Persistent Notes System
executed_trade_notes.csv

- trade_id
- ticker
- placed_time
- notes
- analysis_notes
- management_notes

---

# 🧠 3. Institutional Prompt Engine

### Purpose
Generates **LLM-ready institutional trade analysis prompts**

---

### Output Includes:

- Wyckoff structure evaluation
- Elliott Wave context
- Fibonacci interaction zones
- Volume expansion analysis
- T-Line continuation signals
- Risk efficiency review
- Stop loss validity
- Trade psychology
- Execution efficiency scoring

---

### Data Injection Sources

- daily_history_block
- intraday_block
- volume_block
- financial_block
- historical_results
- PnF structure block
- fractal structure block

---

# 📈 4. Risk Management Engine

Risk per trade = fixed dollar amount  
Position size = risk / (entry - stop)

---

### Features

- Dynamic recalculation
- Stop-loss validation guard
- Prevents invalid negative risk
- Auto updates shares + exposure

---

### Ladder System

- Range High Entry
- Range Low Entry
- Wave 1 Retracement Entry
- Shakeout Entry
- Buy Now Execution

---

# 📊 5. Analysis Engine (Multi-Discipline)

## Wyckoff Engine
- Accumulation / Distribution detection
- Spring / Upthrust identification

## Volume Engine
- RVOL analysis
- OBV slope
- Institutional pressure

## Elliott Wave
- Structural wave context

## T-Line System
- EMA-8 trend structure
- J-Hook continuation

## Fibonacci Layer
- Support / resistance mapping

---

# 🖥️ 6. UI SYSTEM

- Tkinter root window
- ttk.Notebook tabs
- TreeView trade table
- ScrolledText analysis panels

---

## Main UI Components

- Trade Table
- Popup Editor
- Prompt Generator Panel

---

# 📤 7. Export System

/data/analysis/<TICKER>/<timestamp>.txt

Contains:
- Full institutional prompt
- Trade snapshot
- AI-ready context

---

# 🔄 8. Data Lifecycle

User Entry → Journal CSV → UI Editor → Prompt Engine → Analysis Export → AI Review → Management Update → Re-save

---

# ⚙️ 9. Key Functions

- open_entry_editor()
- load_journal()
- save_as_new()
- update_current_entry()
- load_executed_trades()
- open_executed_trade_editor()
- generate_executed_trade_prompt()
- popup_recalc()
- export_management_prompt_to_analysis_file()

---

# 🧩 10. External Dependencies

tkinter  
csv  
os  
datetime  
pandas  
webbrowser  

---

# 🚀 11. Setup Instructions

Run system:

python main.py

Requirements:
Python 3.10+  
Tkinter enabled  
CSV write permissions  
Valid /modules/stock_data structure  

---

# 📌 12. Key Design Principles

No black-box decisions  
Every trade is auditable  
Every execution is reconstructable  
All analysis is prompt-driven  
UI reflects institutional desk structure  
Risk is deterministic  

---

# 🧠 13. Institutional Workflow

1. Load journal  
2. Select ticker  
3. Run analysis prompt  
4. Validate risk structure  
5. Adjust ladder entries  
6. Save/update journal  
7. Export analysis  
8. Review executed trades  
9. Post-trade AI review  
10. Iterate  

---

# 📎 14. Future Expansion

- Broker API integration  
- Real-time feeds  
- Wyckoff automation  
- Cloud sync  
- AI trade scoring  

---

© 2026 Newell Trading Group
All rights reserved.
