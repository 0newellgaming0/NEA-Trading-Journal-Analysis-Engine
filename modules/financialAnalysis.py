import os 
import pandas as pd
from datetime import datetime
import traceback

# =========================================================
# PATH RESOLVER (SOURCE OF TRUTH - FIXED)
# =========================================================
from modules.path_resolver import get_financials_root

# IMPORTANT: NEVER evaluate base_dir at import time incorrectly
FINANCIALS_DIR = get_financials_root()


# =========================================================
# LOGGING (LOCAL MODULE LOGGER - NO SILENT FAILURES)
# =========================================================
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


# =========================================================
# LOAD HELPERS
# =========================================================
def normalize_financial_df(df: pd.DataFrame, ticker="UNKNOWN"):
    log(f"{ticker}: normalize_financial_df called")

    if df is None or df.empty:
        log(f"{ticker}: empty dataframe", "WARN")
        return None

    try:
        df = df.copy()
        log(f"{ticker}: dataframe copied for normalization")

        # writer format assumption: index = metrics
        if isinstance(df.index, pd.RangeIndex):
            log(f"{ticker}: RangeIndex detected → setting metric index")
            df = df.set_index(df.columns[0])

        df.columns = [str(c).strip() for c in df.columns]
        log(f"{ticker}: columns normalized ({len(df.columns)} cols)")

        log(f"{ticker}: aligned to writer format ({df.shape})")
        return df

    except Exception as e:
        log(f"{ticker}: normalization FAILED -> {e}", "ERROR")
        log(traceback.format_exc(), "DEBUG")
        return None


# =========================================================
# LOAD CSV (ROOT-ALIGNED + DEBUG SAFE PATH)
# =========================================================
def load_csv(ticker: str, filename: str, base_dir: str):
    log(f"{ticker}: load_csv called for {filename}")
    path = os.path.join(base_dir, ticker, filename)

    log(f"{ticker}: resolving path -> {path}")

    if not os.path.exists(path):
        log(
            f"{ticker}: missing file -> {filename} "
            f"| expected_path={path} "
            f"| financial_root={base_dir}",
            "ERROR"
        )
        return None

    try:
        log(f"{ticker}: reading CSV {filename}")
        df = pd.read_csv(path)

        log(f"{ticker}: CSV loaded shape={df.shape}")

        df = normalize_financial_df(df, ticker)

        if df is None:
            log(f"{ticker}: normalization returned None | path={path}", "ERROR")

        return df

    except Exception as e:
        log(f"{ticker}: LOAD FAILED {filename} | path={path} | error={e}", "ERROR")
        log(traceback.format_exc(), "DEBUG")
        return None


# =========================================================
# SAFE VALUE EXTRACTION
# =========================================================
def get_latest(df: pd.DataFrame, metric: str, ticker="UNKNOWN"):
    log(f"{ticker}: get_latest metric={metric}")

    if df is None or df.empty:
        log(f"{ticker}: empty df", "WARN")
        return None

    try:
        matches = [idx for idx in df.index if metric.lower() in str(idx).lower()]
        log(f"{ticker}: metric matches found={len(matches)}")

        if not matches:
            log(f"{ticker}: metric NOT FOUND -> {metric}", "WARN")
            return None

        row = matches[0]
        log(f"{ticker}: using row={row}")

        series = pd.to_numeric(df.loc[row], errors="coerce").dropna()

        log(f"{ticker}: extracted numeric series length={len(series)}")

        if series.empty:
            log(f"{ticker}: no numeric values -> {metric}", "WARN")
            return None

        value = series.iloc[0]
        log(f"{ticker}: latest value={value}")

        return value

    except Exception as e:
        log(f"{ticker}: get_latest FAILED -> {e}", "ERROR")
        log(traceback.format_exc(), "DEBUG")
        return None


# =========================================================
# CORE ANALYSIS ENGINE
# =========================================================
def analyze_financials(ticker, base_dir=None):
    if base_dir is None:
        base_dir = FINANCIALS_DIR

    log(f"{ticker}: starting financial analysis | base_dir={base_dir}")

    income = load_csv(ticker, "income_statement.csv", base_dir)
    balance = load_csv(ticker, "balance_sheet.csv", base_dir)
    cashflow = load_csv(ticker, "cashflow.csv", base_dir)

    if income is None and balance is None and cashflow is None:
        log(f"{ticker}: ALL financial datasets missing | base_dir={base_dir}", "ERROR")
        return None

    log(f"{ticker}: datasets loaded → income={income is not None}, balance={balance is not None}, cashflow={cashflow is not None}")

    analysis = {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "source": "yahoo_financials"
    }

    # INCOME
    log(f"{ticker}: extracting INCOME metrics")
    revenue = get_latest(income, "total revenue", ticker)
    net_income = get_latest(income, "net income", ticker)
    gross_profit = get_latest(income, "gross profit", ticker)
    operating_income = get_latest(income, "operating income", ticker)

    analysis.update({
        "revenue": revenue,
        "net_income": net_income,
        "gross_profit": gross_profit,
        "operating_income": operating_income,
    })

    # BALANCE
    log(f"{ticker}: extracting BALANCE metrics")
    total_assets = get_latest(balance, "total assets", ticker)
    total_liab = get_latest(balance, "total liabilities", ticker)
    equity = get_latest(balance, "stockholders equity", ticker)

    analysis.update({
        "total_assets": total_assets,
        "total_liabilities": total_liab,
        "total_equity": equity,
    })

    # CASHFLOW
    log(f"{ticker}: extracting CASHFLOW metrics")
    operating_cf = get_latest(cashflow, "operating cash flow", ticker)
    free_cf = get_latest(cashflow, "free cash flow", ticker)

    analysis.update({
        "operating_cash_flow": operating_cf,
        "free_cash_flow": free_cf,
    })

    # DERIVED
    log(f"{ticker}: computing derived metrics")

    if revenue not in [None, 0]:
        analysis["gross_margin"] = (gross_profit / revenue * 100) if gross_profit else None
        analysis["net_margin"] = (net_income / revenue * 100) if net_income else None
        log(f"{ticker}: margins computed")

    if equity not in [None, 0]:
        analysis["debt_to_equity"] = total_liab / equity if total_liab else None
        log(f"{ticker}: D/E computed")

    # SCORE
    log(f"{ticker}: computing quality score")

    score = 0
    if operating_cf and operating_cf > 0:
        score += 1
    if net_income and net_income > 0:
        score += 1
    if revenue and revenue > 0:
        score += 1
    if analysis.get("net_margin", 0) and analysis["net_margin"] > 5:
        score += 1
    if analysis.get("debt_to_equity") and analysis["debt_to_equity"] < 2:
        score += 1

    analysis["quality_score_5"] = score

    log(f"{ticker}: analysis complete (score={score}/5)")

    return analysis


# =========================================================
# PROMPT FORMATTER
# =========================================================
def format_financial_prompt(ticker, base_dir=None):
    if base_dir is None:
        base_dir = FINANCIALS_DIR

    log(f"{ticker}: formatting financial prompt | base_dir={base_dir}")

    data = analyze_financials(ticker, base_dir)

    if not data:
        log(f"{ticker}: prompt generation FAILED (no data)", "ERROR")
        return f"[Financials] {ticker}: No data available."

    log(f"{ticker}: prompt generation SUCCESS")

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
"""