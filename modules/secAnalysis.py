import os
import json
import pandas as pd
import requests
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC_DIR = os.path.join(PROJECT_ROOT, "sec_filings")

os.makedirs(SEC_DIR, exist_ok=True)

HEADERS = {
    # SEC requires real identifying UA (important for reliability)
    "User-Agent": "NewellTradingSystem/1.0 (institutional research; contact: none)"
}

REQUEST_TIMEOUT = 10


# =========================================================
# LOGGING SAFE WRAPPER
# =========================================================
def log(msg):
    print(msg)


# =========================================================
# CIK LOOKUP
# =========================================================
def get_cik_from_ticker(ticker):
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

        if r.status_code != 200:
            return None

        data = r.json()
        ticker = ticker.upper()

        for _, v in data.items():
            if v["ticker"] == ticker:
                return str(v["cik_str"]).zfill(10)

        return None

    except Exception:
        return None


# =========================================================
# GET EDGAR FILINGS
# =========================================================
def get_filings(cik):
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)

        if r.status_code != 200:
            return None

        return r.json()

    except Exception:
        return None


# =========================================================
# SAVE RAW DATA
# =========================================================
def save_raw_data(ticker, cik, filings_json):
    ticker_dir = os.path.join(SEC_DIR, ticker)
    os.makedirs(ticker_dir, exist_ok=True)

    path = os.path.join(ticker_dir, "filings.json")

    payload = {
        "ticker": ticker,
        "cik": cik,
        "timestamp": datetime.now().isoformat(),
        "data": filings_json
    }

    with open(path, "w") as f:
        json.dump(payload, f, indent=4)


# =========================================================
# ANALYSIS LAYER
# =========================================================
def analyze_filings(filings_json):
    if not filings_json:
        return None

    recent = filings_json.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])

    signals = {
        "last_10k": None,
        "last_10q": None,
        "recent_8k_count": 0,
        "dilution_events": 0,
        "timestamp": datetime.now().isoformat(),
        "source": "sec_edgar"
    }

    for form, date in zip(forms, dates):

        if form == "10-K" and not signals["last_10k"]:
            signals["last_10k"] = date

        if form == "10-Q" and not signals["last_10q"]:
            signals["last_10q"] = date

        if form == "8-K":
            signals["recent_8k_count"] += 1

        if form in ["S-1", "S-3", "424B5"]:
            signals["dilution_events"] += 1

    return signals


# =========================================================
# SAVE SIGNALS
# =========================================================
def save_signals(ticker, signals):
    ticker_dir = os.path.join(SEC_DIR, ticker)
    os.makedirs(ticker_dir, exist_ok=True)

    path = os.path.join(ticker_dir, "signals.json")

    with open(path, "w") as f:
        json.dump(signals, f, indent=4)


# =========================================================
# MAIN PIPELINE
# =========================================================
def analyze_ticker_sec(ticker):

    try:
        cik = get_cik_from_ticker(ticker)

        if not cik:
            log(f"⚠ {ticker} SEC: CIK not found")
            return None

        filings = get_filings(cik)

        if not filings:
            log(f"⚠ {ticker} SEC: no filings returned")
            return None

        save_raw_data(ticker, cik, filings)

        signals = analyze_filings(filings)
        save_signals(ticker, signals)

        log(f"📄 {ticker} SEC data saved (filings + signals)")

        return {
            "ticker": ticker,
            "cik": cik,
            "signals": signals
        }

    except Exception as e:
        log(f"❌ {ticker} SEC error: {e}")
        return None


# =========================================================
# PROMPT FORMATTER (JOURNAL INTEGRATION)
# =========================================================
def format_sec_prompt(ticker):

    data = analyze_ticker_sec(ticker)

    if not data:
        return f"[SEC] {ticker}: No EDGAR data available."

    s = data["signals"]

    return f"""
📑 SEC EDGAR INTELLIGENCE: {ticker}

CIK: {data['cik']}

📌 Filing Snapshot:
- Last 10-K: {s.get('last_10k')}
- Last 10-Q: {s.get('last_10q')}
- 8-K Event Count: {s.get('recent_8k_count')}

⚠️ Institutional Risk Signals:
- Dilution Filings (S-1/S-3/ATM): {s.get('dilution_events')}

🧠 Interpretation:
- Rising 8-K count = event-driven volatility
- S-1/S-3 presence = share structure pressure
- 10-Q recency = earnings cycle positioning

Source: SEC EDGAR (live ingestion)
Timestamp: {s.get('timestamp')}
"""