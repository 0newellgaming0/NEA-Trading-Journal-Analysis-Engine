import os
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINANCIALS_DIR = os.path.join(PROJECT_ROOT, "financials")


# =========================================================
# LOAD HELPERS
# =========================================================
def load_csv(ticker, filename):
    path = os.path.join(FINANCIALS_DIR, ticker, filename)
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path, index_col=0)
    except Exception:
        return None


# =========================================================
# SAFE VALUE EXTRACTION
# =========================================================
def get_latest(df, row_name):
    if df is None or df.empty:
        return None

    try:
        row = df.loc[row_name]
        return row.iloc[0] if len(row) > 0 else None
    except Exception:
        return None


def pct_change(new, old):
    try:
        if old in [0, None] or pd.isna(old) or pd.isna(new):
            return None
        return ((new - old) / abs(old)) * 100
    except Exception:
        return None


# =========================================================
# CORE ANALYSIS ENGINE
# =========================================================
def analyze_financials(ticker):
    income = load_csv(ticker, "income_statement.csv")
    balance = load_csv(ticker, "balance_sheet.csv")
    cashflow = load_csv(ticker, "cashflow.csv")

    if income is None and balance is None and cashflow is None:
        return None

    analysis = {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "source": "yahoo_financials"
    }

    # =====================================================
    # INCOME STATEMENT METRICS
    # =====================================================
    revenue = get_latest(income, "Total Revenue")
    net_income = get_latest(income, "Net Income")
    gross_profit = get_latest(income, "Gross Profit")
    operating_income = get_latest(income, "Operating Income")

    analysis["revenue"] = revenue
    analysis["net_income"] = net_income
    analysis["gross_profit"] = gross_profit
    analysis["operating_income"] = operating_income

    # Margins
    if revenue:
        analysis["gross_margin"] = (gross_profit / revenue) * 100 if gross_profit else None
        analysis["net_margin"] = (net_income / revenue) * 100 if net_income else None

    # =====================================================
    # BALANCE SHEET METRICS
    # =====================================================
    total_assets = get_latest(balance, "Total Assets")
    total_liab = get_latest(balance, "Total Liab")
    total_equity = get_latest(balance, "Total Stockholder Equity")

    analysis["total_assets"] = total_assets
    analysis["total_liabilities"] = total_liab
    analysis["total_equity"] = total_equity

    if total_equity:
        analysis["debt_to_equity"] = total_liab / total_equity if total_liab else None

    # =====================================================
    # CASH FLOW METRICS
    # =====================================================
    operating_cf = get_latest(cashflow, "Operating Cash Flow")
    free_cf = get_latest(cashflow, "Free Cash Flow")

    analysis["operating_cash_flow"] = operating_cf
    analysis["free_cash_flow"] = free_cf

    # =====================================================
    # SIMPLE QUALITY SCORE (INSTITUTIONAL HEURISTIC)
    # =====================================================
    score = 0

    if operating_cf and operating_cf > 0:
        score += 1
    if net_income and net_income > 0:
        score += 1
    if revenue and revenue > 0:
        score += 1
    if analysis.get("net_margin") and analysis["net_margin"] > 5:
        score += 1
    if analysis.get("debt_to_equity") and analysis["debt_to_equity"] < 2:
        score += 1

    analysis["quality_score_5"] = score

    return analysis


# =========================================================
# PROMPT FORMATTER (FOR journal.py)
# =========================================================
def format_financial_prompt(ticker):
    data = analyze_financials(ticker)

    if not data:
        return f"[Financials] {ticker}: No data available."

    return f"""
📊 FINANCIAL ANALYSIS: {ticker}

Revenue: {data.get('revenue')}
Net Income: {data.get('net_income')}
Gross Profit: {data.get('gross_profit')}
Operating Income: {data.get('operating_income')}

Margins:
- Gross Margin: {data.get('gross_margin')}
- Net Margin: {data.get('net_margin')}

Balance Sheet:
- Total Assets: {data.get('total_assets')}
- Total Liabilities: {data.get('total_liabilities')}
- Equity: {data.get('total_equity')}
- Debt/Equity: {data.get('debt_to_equity')}

Cash Flow:
- Operating Cash Flow: {data.get('operating_cash_flow')}
- Free Cash Flow: {data.get('free_cash_flow')}

Institutional Score (5):
{data.get('quality_score_5')}/5

Source: Yahoo Financial Statements
"""