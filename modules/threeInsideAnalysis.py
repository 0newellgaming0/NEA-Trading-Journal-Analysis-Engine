import numpy as np
import pandas as pd

# =========================================================
# SAFE SCALAR EXTRACTOR
# =========================================================
def f(x):
    try:
        if isinstance(x, pd.Series):
            x = x.iloc[-1]
        if pd.isna(x):
            return 0.0
        return float(x)
    except:
        return 0.0


# =========================================================
# OHLC NORMALIZER
# =========================================================
def normalize_ohlcv_columns(df, ticker=None):
    df = df.copy()

    if ticker is None:
        for col in df.columns:
            if col.startswith("close_"):
                ticker = col.split("_")[-1]
                break

    if ticker is None:
        raise ValueError("Cannot detect ticker from dataframe columns")

    t = ticker.lower()

    def pick(col):
        return df[col] if col in df.columns else pd.Series(np.nan, index=df.index)

    df["Open"] = pick(f"open_{t}")
    df["High"] = pick(f"high_{t}")
    df["Low"] = pick(f"low_{t}")
    df["Close"] = pick(f"close_{t}")
    df["Volume"] = pick(f"volume_{t}")

    return df


def enforce_schema(df):
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["Open", "High", "Low", "Close"])


# =========================================================
# CORE UTILITIES
# =========================================================
def is_inside(c1, c2):
    return f(c2["High"]) < f(c1["High"]) and f(c2["Low"]) > f(c1["Low"])


def body(c):
    return abs(f(c["Close"]) - f(c["Open"]))


def rng(c):
    return max(f(c["High"]) - f(c["Low"]), 1e-9)


def is_bull(c):
    return f(c["Close"]) > f(c["Open"])


def is_bear(c):
    return f(c["Close"]) < f(c["Open"])


# =========================================================
# CANDLE 1 TREND FILTER
# =========================================================
def candle1_trend_filter(c1):

    o, c = f(c1["Open"]), f(c1["Close"])
    h, l = f(c1["High"]), f(c1["Low"])

    range_size = max(h - l, 1e-9)
    body_ratio = abs(c - o) / range_size

    return {
        "valid": body_ratio > 0.45,
        "direction": "bullish" if c > o else "bearish"
    }


# =========================================================
# TRUE HARAMI (BODY ONLY)
# =========================================================
def is_true_harami(c1, c2):

    c1_o, c1_c = f(c1["Open"]), f(c1["Close"])
    c2_o, c2_c = f(c2["Open"]), f(c2["Close"])

    return (
        max(c2_o, c2_c) <= max(c1_o, c1_c) and
        min(c2_o, c2_c) >= min(c1_o, c1_c)
    )


# =========================================================
# BREAKOUT VALIDATION
# =========================================================
def candle3_breakout_valid(c1, c3, direction):

    c1_high = f(c1["High"])
    c1_low = f(c1["Low"])
    c3_close = f(c3["Close"])

    expansion = rng(c3) > rng(c1) * 0.60

    if direction == "bullish":
        return c3_close > c1_high and expansion
    else:
        return c3_close < c1_low and expansion


# =========================================================
# CENTER CLASSIFIER
# =========================================================
def classify_three_inside_center(candle):
    o, h, l, c = f(candle["Open"]), f(candle["High"]), f(candle["Low"]), f(candle["Close"])

    rng_ = max(h - l, 1e-9)
    body_ = abs(c - o)
    body_pct = body_ / rng_

    upper = h - max(o, c)
    lower = min(o, c) - l

    balance = min(upper, lower) / max(max(upper, lower), 1e-9)

    if body_pct <= 0.10:
        return {"type": "Doji", "strength": "STRONG"}

    if body_pct <= 0.30 and balance >= 0.5:
        return {"type": "Balanced", "strength": "STRONG"}

    if body_pct <= 0.40:
        return {"type": "Weak", "strength": "WEAK"}

    return {"type": "Invalid", "strength": "INVALID"}


# =========================================================
# STATE MACHINE
# =========================================================
def detect_three_inside_pattern(df):

    if len(df) < 3:
        return {"state": "NONE"}

    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

    trend = candle1_trend_filter(c1)
    if not trend["valid"]:
        return {"state": "NONE"}

    if not is_true_harami(c1, c2):
        return {"state": "NONE"}

    center = classify_three_inside_center(c2)
    if center["strength"] == "INVALID":
        return {"state": "NONE"}

    breakout = candle3_breakout_valid(c1, c3, trend["direction"])

    # -----------------------------------------------------
    # CONFIRMED
    # -----------------------------------------------------
    if breakout:
        return {
            "state": "CONFIRMED",
            "stage": 4,
            "type": "ThreeInsideUp" if trend["direction"] == "bullish" else "ThreeInsideDown",
            "direction": trend["direction"],
            "high": f(c3["High"]),
            "low": f(c3["Low"]),
            "close": f(c3["Close"])
        }

    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------
    return {
        "state": "PENDING_CONFIRMATION",
        "stage": 3,
        "type": "ThreeInside",
        "direction": "NEUTRAL",
        "center_type": center["type"],
        "candle1_high": f(c1["High"]),
        "candle1_low": f(c1["Low"])
    }

# =========================================================
# FORMING STATE
# =========================================================
def detect_three_inside_forming(df):

    if len(df) < 2:
        return None

    c1, c2 = df.iloc[-2], df.iloc[-1]

    if not is_true_harami(c1, c2):
        return None

    return {
        "state": "FORMING",
        "expected": "ThreeInsideUp / ThreeInsideDown",
        "center_type": classify_three_inside_center(c2)["type"]
    }


# =========================================================
# TRADE PLAN
# =========================================================
def build_three_inside_trade_plan(pattern):

    state = pattern.get("state")

    # -----------------------------------------------------
    # CONFIRMED
    # -----------------------------------------------------
    if state == "CONFIRMED":

        rng_ = abs(pattern["high"] - pattern["low"])

        if pattern["type"] == "ThreeInsideUp":
            return {
                "setup": "THREE INSIDE UP",
                "LONG_TRIGGER": pattern["high"],
                "SHORT_TRIGGER": None,
                "LONG_STOP": pattern["low"],
                "SHORT_STOP": None,
                "target1": pattern["high"] + rng_,
                "target2": pattern["high"] + 2 * rng_
            }

        return {
            "setup": "THREE INSIDE DOWN",
            "LONG_TRIGGER": None,
            "SHORT_TRIGGER": pattern["low"],
            "LONG_STOP": None,
            "SHORT_STOP": pattern["high"],
            "target1": pattern["low"] - rng_,
            "target2": pattern["low"] - 2 * rng_
        }

    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------
    if state == "PENDING_CONFIRMATION":

        return {
            "setup": "PENDING BREAKOUT SETUP",
            "LONG_TRIGGER": float(pattern.get("candle1_high", 0)),
            "SHORT_TRIGGER": float(pattern.get("candle1_low", 0)),
            "LONG_STOP": float(pattern.get("candle1_low", 0)),
            "SHORT_STOP": float(pattern.get("candle1_high", 0)),
            "target1": None,
            "target2": None
        }

    # -----------------------------------------------------
    # NO PATTERN
    # -----------------------------------------------------
    return {
        "setup": "NO THREE INSIDE",
        "LONG_TRIGGER": None,
        "SHORT_TRIGGER": None,
        "LONG_STOP": None,
        "SHORT_STOP": None,
        "target1": None,
        "target2": None
    }


# =========================================================
# MAIN ENGINE
# =========================================================
def analyze_three_inside_pattern(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 3:
        return {"journal_prompt": "Insufficient data"}

    last3 = df.iloc[-3:]

    pattern = detect_three_inside_pattern(last3)
    forming = detect_three_inside_forming(df.iloc[-2:])
    trade_plan = build_three_inside_trade_plan(pattern)

    return {
        "journal_prompt": format_three_inside_journal_prompt({
            "pattern": pattern,
            "forming": forming,
            "trade_plan": trade_plan,
            "candle_1": last3.iloc[0].to_dict(),
            "candle_2": last3.iloc[1].to_dict(),
            "candle_3": last3.iloc[2].to_dict()
        })
    }


# =========================================================
# FORMATTER
# =========================================================
def format_candle(candle, label="CANDLE"):
    return f"""
{label}:
- Open:   {candle.get('Open')}
- High:   {candle.get('High')}
- Low:    {candle.get('Low')}
- Close:  {candle.get('Close')}
- Volume: {candle.get('Volume')}
"""


def format_three_inside_journal_prompt(result):

    p = result["pattern"]
    tp = result["trade_plan"]

    c1 = format_candle(result["candle_1"], "CANDLE 1")
    c2 = format_candle(result["candle_2"], "CANDLE 2")
    c3 = format_candle(result["candle_3"], "CANDLE 3")

    # =====================================================
    # STATE-GATED STAGE DISPLAY (FIX)
    # =====================================================
    state = p.get("state")

    if state == "NONE":
        stage_line = "- Stage: None"
    else:
        stage_line = f"- Stage: {p.get('stage', 'N/A')}"

    return f"""
# ==================================================
📌 THREE INSIDE PATTERN ANALYSIS
# ==================================================

PATTERN:
- State: {state}
- Type: {p.get('type')}
- Direction: {p.get('direction')}

STATUS:
{stage_line}
- Center: {p.get('center_type', 'N/A')}

--------------------------------------------------
📊 LAST 3 CANDLES

{c1}
{c2}
{c3}

--------------------------------------------------
🎯 TRADE PLAN
- Setup: {tp.get('setup')}

- LONG_TRIGGER: {tp.get('LONG_TRIGGER')}
- LONG_STOP: {tp.get('LONG_STOP')}
- Target1: {tp.get('target1')}
- Target2: {tp.get('target2')}

- SHORT_TRIGGER: {tp.get('SHORT_TRIGGER')}
- SHORT_STOP: {tp.get('SHORT_STOP')}

--------------------------------------------------
🧠 INTERPRETATION
{ "No valid Three Inside structure detected."
  if state == "NONE"
  else "FORMING → PENDING BREAKOUT → CONFIRMATION ONLY ON CLOSE" }
"""