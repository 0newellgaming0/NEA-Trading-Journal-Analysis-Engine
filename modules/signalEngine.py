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
# IMPULSE-AWARE RANGE (NEW CORE FIX)
# =========================================================
def get_impulse_range(df, end_index=None, lookback=20):

    """
    FIX:
    replaces rolling 50-bar statistical range

    Now uses:
    - local structure window
    - anchored to detection index
    """

    if end_index is None:
        window = df.iloc[-lookback:]
    else:
        start = max(0, end_index - lookback)
        window = df.iloc[start:end_index + 1]

    return float(window["High"].max()), float(window["Low"].min())


# =========================================================
# PULLBACK DEPTH (FIXED CORE LOGIC)
# =========================================================
def evaluate_pullback_depth(df, trend, end_index=None):

    """
    FIXED:
    no longer uses global 50-bar envelope
    now uses impulse-local range
    """

    if len(df) < 20:
        return {"depth": 0.0, "fib_zone": None, "score": 0}

    high, low = get_impulse_range(df, end_index=end_index, lookback=20)
    close = float(df["Close"].iloc[-1])

    impulse = high - low

    if impulse <= 0:
        return {"depth": 0.0, "fib_zone": None, "score": 0}

    if trend == "Bullish":
        retrace = (high - close) / impulse

    elif trend == "Bearish":
        retrace = (close - low) / impulse

    else:
        return {"depth": 0.0, "fib_zone": None, "score": 0}

    if 0.382 <= retrace <= 0.618:
        zone = "Optimal"
        score = 20

    elif retrace < 0.382:
        zone = "Shallow"
        score = 10

    elif retrace <= 0.786:
        zone = "Deep"
        score = 8

    else:
        zone = "Broken"
        score = 0

    return {
        "depth": retrace,
        "fib_zone": zone,
        "score": score
    }


# =========================================================
# SWING STRUCTURE (UNCHANGED - OK)
# =========================================================
def evaluate_swing_structure(df):

    if len(df) < 20:
        return {"trend": "Unknown", "score": 0}

    highs = df["High"].tail(10).tolist()
    lows = df["Low"].tail(10).tolist()

    swing_highs = []
    swing_lows = []

    for i in range(1, len(highs) - 1):

        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            swing_highs.append(highs[i])

        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            swing_lows.append(lows[i])

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {"trend": "Neutral", "score": 5}

    higher_high = swing_highs[-1] > swing_highs[-2]
    higher_low = swing_lows[-1] > swing_lows[-2]

    lower_high = swing_highs[-1] < swing_highs[-2]
    lower_low = swing_lows[-1] < swing_lows[-2]

    if higher_high and higher_low:
        return {"trend": "Bullish", "score": 20}

    if lower_high and lower_low:
        return {"trend": "Bearish", "score": 20}

    return {"trend": "Neutral", "score": 5}


# =========================================================
# EMA PULLBACK (SLIGHT STABILITY FIX)
# =========================================================
def evaluate_ma_pullback(df):

    if len(df) < 50:
        return {"aligned": False, "side": None, "score": 0}

    close = df["Close"]

    ema20 = close.ewm(span=20).mean().iloc[-1]
    price = close.iloc[-1]

    distance = abs(price - ema20) / price

    if distance > 0.02:   # FIXED (was 0.015)
        return {"aligned": False, "side": None, "score": 0}

    if price >= ema20:
        return {"aligned": True, "side": "Bullish", "score": 15}

    return {"aligned": True, "side": "Bearish", "score": 15}


# =========================================================
# MOMENTUM (STRUCTURE FIXED)
# =========================================================
def evaluate_pullback_momentum(df):

    if len(df) < 30:
        return {"direction": "Neutral", "score": 0}

    close = df["Close"]

    ema8 = close.ewm(span=8).mean()
    ema21 = close.ewm(span=21).mean()

    slope = ema8.iloc[-1] - ema8.iloc[-2]

    current = df.iloc[-1]
    previous = df.iloc[-2]

    bullish_structure = (
        current["Close"] > previous["Close"] and
        current["Low"] >= previous["Low"]
    )

    bearish_structure = (
        current["Close"] < previous["Close"] and
        current["High"] <= previous["High"]
    )

    if (
        ema8.iloc[-1] > ema21.iloc[-1]
        and slope > 0
        and bullish_structure
    ):
        return {"direction": "Bullish", "score": 15}

    if (
        ema8.iloc[-1] < ema21.iloc[-1]
        and slope < 0
        and bearish_structure
    ):
        return {"direction": "Bearish", "score": 15}

    return {"direction": "Neutral", "score": 5}


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
# MAIN COMPOSITE
# =========================================================
def evaluate_pullback_setup(df, f=float):

    trend = evaluate_trend(df, f)
    structure = evaluate_structure(df)
    fib = evaluate_fibonacci(df)
    swing = evaluate_swing_structure(df)

    depth = evaluate_pullback_depth(
        df,
        trend["trend"]
    )

    ema = evaluate_ma_pullback(df)
    momentum = evaluate_pullback_momentum(df)

    score = (
        trend["score"]
        + structure["score"]
        + fib["score"]
        + swing["score"]
        + depth["score"]
        + ema["score"]
        + momentum["score"]
    )

    return {
        "trend": trend,
        "structure": structure,
        "fibonacci": fib,
        "swing": swing,
        "pullback": depth,
        "ema": ema,
        "momentum": momentum,
        "score": score
    }