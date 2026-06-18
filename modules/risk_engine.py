import logging
import pandas as pd
import numpy as np

from modules.tlineAnalysis import ema, tline_stop_price

logger = logging.getLogger(__name__)


# =========================================================
# SAFE CLOSE EXTRACTION
# =========================================================
def get_latest_close(df, ticker=""):
    if not isinstance(df, pd.DataFrame) or df.empty:
        logger.error("get_latest_close(): invalid dataframe")
        return None

    col = f"close_{ticker.lower()}"

    if col not in df.columns:
        logger.error(f"Missing column {col}")
        return None

    try:
        val = df[col].iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
    except Exception as e:
        logger.exception(f"close extraction failed: {e}")
        return None


# =========================================================
# SAFE SERIES BUILDER (NEW CRITICAL ADDITION)
# =========================================================
def _build_ohlc(df, ticker):
    """
    Normalizes OHLC series for T-Line calculation.
    """
    t = ticker.lower()

    close = df.get(f"close_{t}", df.get("close"))
    high  = df.get(f"high_{t}", df.get("high"))
    low   = df.get(f"low_{t}", df.get("low"))

    if close is None or high is None or low is None:
        return None, None, None

    close = pd.to_numeric(close, errors="coerce")
    high = pd.to_numeric(high, errors="coerce")
    low = pd.to_numeric(low, errors="coerce")

    return close, high, low


# =========================================================
# T-LINE STOP WRAPPER (SAFE + COMPLETE)
# =========================================================
def get_tline_stop(df, ticker=""):
    """
    Fully autonomous T-Line stop calculator.
    """

    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Invalid dataframe")

    close, high, low = _build_ohlc(df, ticker)

    if close is None:
        raise ValueError("Missing OHLC data")

    close = close.dropna()
    high = high.dropna()
    low = low.dropna()

    if len(close) < 20:
        raise ValueError("Insufficient data for EMA8/ATR logic")

    ema8 = ema(close, 8)

    stop = tline_stop_price(
        close=close,
        ema8=ema8,
        high=high,
        low=low
    )

    if pd.isna(stop):
        raise ValueError("T-Line stop computation failed")

    return float(stop)


# =========================================================
# STOP LOSS EVALUATION ENGINE (FIXED CORE)
# =========================================================
def evaluate_stop_loss(latest_close, stop_val, df=None, daily_df=None, ticker=""):
    """
    Fully institutional dual-stop engine:
    - Structural stop
    - 60m T-Line stop
    - Daily T-Line stop
    + PULLBACK classification layer
    """

    if latest_close is None:
        return {
            "status": "UNAVAILABLE",
            "block": "⚠️ Risk engine unavailable (no price data)"
        }

    # ----------------------------------------
    # STRUCTURAL STOP
    # ----------------------------------------
    stop_val = float(stop_val or 0)
    structural_breached = latest_close < stop_val

    # ----------------------------------------
    # 60M T-LINE STOP
    # ----------------------------------------
    tline_stop = None
    tline_breached = False
    tline_status = "UNAVAILABLE"

    if df is not None:
        try:
            tline_stop = get_tline_stop(df, ticker)
            tline_breached = latest_close < tline_stop
            tline_status = "BREACHED" if tline_breached else "VALID"
        except Exception as e:
            logger.warning(f"60M T-line unavailable: {e}")

    # ----------------------------------------
    # DAILY T-LINE STOP
    # ----------------------------------------
    daily_tline_stop = None
    daily_tline_breached = False
    daily_tline_status = "UNAVAILABLE"

    if daily_df is not None:
        try:
            daily_tline_stop = get_tline_stop(daily_df, ticker)
            daily_tline_breached = latest_close < daily_tline_stop
            daily_tline_status = "BREACHED" if daily_tline_breached else "VALID"
        except Exception as e:
            logger.warning(f"Daily T-line unavailable: {e}")

    # =========================================================
    # 🧠 CORE STATE CLASSIFICATION (NEW LOGIC)
    # =========================================================

    # Default state
    status_state = "VALID"

    # PULLBACK condition (your rule)
    if tline_breached and not daily_tline_breached:
        status_state = "PULLBACK"

    # BREACHED condition (highest severity)
    elif structural_breached or daily_tline_breached:
        status_state = "BREACHED"

    # ----------------------------------------
    # FINAL FLAG
    # ----------------------------------------
    stop_breached = status_state == "BREACHED"

    # ================================
    # 🚨 BREACH STATE
    # ================================
    if stop_breached:

        block = f"""
🚨🚨 STOP LOSS BREACH DETECTED 🚨🚨

LATEST CLOSE: {latest_close}

────────────────────────────
STRUCTURAL STOP: {stop_val}
STRUCTURAL BREACH: {structural_breached}

────────────────────────────
60M T-LINE STOP: {tline_stop if tline_stop is not None else "N/A"}
60M T-LINE BREACH: {tline_breached if tline_stop else "N/A"}

────────────────────────────
DAILY T-LINE STOP: {daily_tline_stop if daily_tline_stop is not None else "N/A"}
DAILY T-LINE BREACH: {daily_tline_breached if daily_tline_stop else "N/A"}

⚠️ STATUS: BREACHED

- Monitor for J-Hook Formation or Failure
- If not in trade, look for entry.

"""

        return {
            "breached": True,
            "status": "BREACHED",
            "state": status_state,
            "structural_breached": structural_breached,
            "tline_breached": tline_breached,
            "daily_tline_breached": daily_tline_breached,
            "tline_stop": tline_stop,
            "daily_tline_stop": daily_tline_stop,
            "block": block
        }

    # ================================
    # 🟡 PULLBACK STATE
    # ================================
    if status_state == "PULLBACK":

        block = f"""
🟡 PULLBACK STATE DETECTED

LATEST CLOSE: {latest_close}

────────────────────────────
STRUCTURAL STOP: {stop_val}

────────────────────────────
60M T-LINE STOP: {tline_stop if tline_stop is not None else "N/A"}
60M STATUS: BREACHED

────────────────────────────
DAILY T-LINE STOP: {daily_tline_stop if daily_tline_stop is not None else "N/A"}
DAILY STATUS: STILL VALID

📌 INTERPRETATION:
- Intraday weakness into T-Line
- Higher timeframe structure still intact
- Classified as PULLBACK, not failure
"""

        return {
            "breached": False,
            "status": "PULLBACK",
            "state": status_state,
            "structural_breached": structural_breached,
            "tline_breached": tline_breached,
            "daily_tline_breached": daily_tline_breached,
            "tline_stop": tline_stop,
            "daily_tline_stop": daily_tline_stop,
            "block": block
        }

    # ================================
    # 🟢 VALID STATE
    # ================================
    block = f"""
🟢 STOP LOSS STATUS: VALID

LATEST CLOSE: {latest_close}

────────────────────────────
STRUCTURAL STOP: {stop_val}

────────────────────────────
60M T-LINE STOP: {tline_stop if tline_stop is not None else "N/A"}
60M STATUS: VALID

────────────────────────────
DAILY T-LINE STOP: {daily_tline_stop if daily_tline_stop is not None else "N/A"}
DAILY STATUS: VALID

Structure remains intact.
"""

    return {
        "breached": False,
        "status": "VALID",
        "state": status_state,
        "structural_breached": structural_breached,
        "tline_breached": tline_breached,
        "daily_tline_breached": daily_tline_breached,
        "tline_stop": tline_stop,
        "daily_tline_stop": daily_tline_stop,
        "block": block
    }