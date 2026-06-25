import pandas as pd
import numpy as np
import logging

logger = logging.getLogger("signal_engine")


# =========================================================
# TREND
# =========================================================
def evaluate_trend(df, f):

    logger.info("[TREND] evaluate_trend called")

    if len(df) < 50:
        return {"trend": "Unknown", "score": 0}

    if "Close" not in df.columns:
        raise ValueError("Missing Close column")

    close = pd.to_numeric(df["Close"], errors="coerce").dropna()

    ema8 = f(close.ewm(span=8).mean().iloc[-1])
    ema21 = f(close.ewm(span=21).mean().iloc[-1])
    sma50 = f(close.rolling(50).mean().iloc[-1])

    if ema8 > ema21 and ema21 > sma50:
        return {"trend": "Bullish", "score": 15}

    if ema8 < ema21 and ema21 < sma50:
        return {"trend": "Bearish", "score": 15}

    return {"trend": "Neutral", "score": 5}


# =========================================================
# SWEEP
# =========================================================
def detect_liquidity_sweep(df):

    if len(df) < 20:
        return {"sweep": False, "type": None, "score": 0}

    current = df.iloc[-1]
    prev = df.iloc[:-1]

    swing_low = prev["Low"].min()
    swing_high = prev["High"].max()

    if current["Low"] < swing_low and current["Close"] > swing_low:
        return {"sweep": True, "type": "Spring", "score": 25}

    if current["High"] > swing_high and current["Close"] < swing_high:
        return {"sweep": True, "type": "Upthrust", "score": 25}

    return {"sweep": False, "type": None, "score": 0}


# =========================================================
# STRUCTURE
# =========================================================
def evaluate_structure(df):

    if len(df) < 50:
        return {"score": 0, "label": "Unknown"}

    current = df.iloc[-1]

    support = df["Low"].rolling(50).min().iloc[-1]
    resistance = df["High"].rolling(50).max().iloc[-1]

    near_support = abs(current["Close"] - support) / current["Close"] < 0.03
    near_resistance = abs(current["Close"] - resistance) / current["Close"] < 0.03

    if near_support:
        return {"score": 15, "label": "Near Support"}

    if near_resistance:
        return {"score": 15, "label": "Near Resistance"}

    return {"score": 0, "label": "Neutral"}


# =========================================================
# FIBONACCI
# =========================================================
def evaluate_fibonacci(df):

    if len(df) < 50:
        return {"score": 0, "label": "No Data"}

    high = df["High"].tail(50).max()
    low = df["Low"].tail(50).min()
    close = df["Close"].iloc[-1]

    levels = [
        high - (high - low) * 0.382,
        high - (high - low) * 0.50,
        high - (high - low) * 0.618,
        high - (high - low) * 0.786
    ]

    for lvl in levels:
        if abs(close - lvl) / close < 0.01:
            return {"score": 5, "label": f"Aligned @ {round(lvl, 2)}"}

    return {"score": 0, "label": "No Alignment"}