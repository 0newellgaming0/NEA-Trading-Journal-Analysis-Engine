# =========================================================
# FIBONACCI PULLBACK MODULE (SWING-BASED INSTITUTIONAL VERSION)
# =========================================================

import logging
from modules.eventEngine import extract_event_date
from modules.tline import get_tline, get_sma

logger = logging.getLogger("fibonacci_module")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0

def get_trend(df, i):

    window_5 = df.iloc[max(0, i - 5): i]

    highs = window_5["High"]
    lows = window_5["Low"]

    # higher-high / higher-low structure
    hh = highs.iloc[-1] >= highs.max()
    hl = lows.iloc[-1] >= lows.min()

    # lower-low / lower-high structure
    ll = lows.iloc[-1] <= lows.min()
    lh = highs.iloc[-1] <= highs.max()

    if hh and hl:
        return "BULLISH"

    if ll and lh:
        return "BEARISH"

    return "RANGE"
    
# =========================================================
# SWING DETECTION (LATEST STRUCTURAL SWING ONLY)
# =========================================================
def get_latest_swing(df, i, lookback=25):

    window = df.iloc[max(0, i - lookback): i]

    base_high = f(window["High"].max())
    base_low = f(window["Low"].min())

    recent = df.iloc[max(0, i - 5): i]

    recent_high = f(recent["High"].max())
    recent_low = f(recent["Low"].min())

    close = f(df.iloc[i]["Close"])

    # =========================================================
    # EXPANSION OVERRIDE LOGIC
    # =========================================================

    if close > base_high:
        # bullish expansion → use latest 5-bar high
        return {
            "swing_high": recent_high,
            "swing_low": base_low,
            "range": max(recent_high - base_low, 1e-9),
            "mode": "EXPANSION_UP"
        }

    if close < base_low:
        # bearish expansion → use latest 5-bar low
        return {
            "swing_high": base_high,
            "swing_low": recent_low,
            "range": max(base_high - recent_low, 1e-9),
            "mode": "EXPANSION_DOWN"
        }

    return {
        "swing_high": base_high,
        "swing_low": base_low,
        "range": max(base_high - base_low, 1e-9),
        "mode": "RANGE"
    }


# =========================================================
# FIB LEVELS FROM SWING
# =========================================================
def get_fib_levels(swing_high, swing_low):

    rng = max(swing_high - swing_low, 1e-9)

    return {
        "0.0": swing_high,
        "0.236": swing_high - (0.236 * rng),
        "0.382": swing_high - (0.382 * rng),
        "0.5": swing_high - (0.5 * rng),
        "0.618": swing_high - (0.618 * rng),
        "0.786": swing_high - (0.786 * rng),
        "1.0": swing_low
    }


# =========================================================
# DETECTION (TRUE SWING + FIB CONTEXT SEED)
# =========================================================
def detect_fib_pullback(candle, df, i):

    high = f(candle["High"])
    low = f(candle["Low"])
    open_ = f(candle["Open"])
    close = f(candle["Close"])

    if high <= low:
        return {"detected": False}

    trend = get_trend(df, i)
    swing = get_latest_swing(df, i)

    fibs = get_fib_levels(swing["swing_high"], swing["swing_low"])

    # =========================================================
    # SEED = FIRST RETRACEMENT INTO STRUCTURAL FIB ZONE
    # =========================================================

    bullish_seed = (
        trend == "BULLISH"
        and close < fibs["0.382"]
    )

    bearish_seed = (
        trend == "BEARISH"
        and close > fibs["0.618"]
    )

    if bullish_seed:
        return {
            "detected": True,
            "type": "FIB_PULLBACK",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "swing_high": swing["swing_high"],
            "swing_low": swing["swing_low"],
            "fib_levels": fibs,
            "status": "SEED"
        }

    if bearish_seed:
        return {
            "detected": True,
            "type": "FIB_PULLBACK",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "swing_high": swing["swing_high"],
            "swing_low": swing["swing_low"],
            "fib_levels": fibs,
            "status": "SEED"
        }

    return {"detected": False}


# =========================================================
# ENTRY (REAL PULLBACK INTO NEXT FIB ZONE)
# =========================================================
def detect_fib_entry(event, candle):

    close = f(candle["Close"])
    fibs = event["fib_levels"]
    direction = event["direction"]

    # =========================================================
    # ENTRY = REACTION INTO 0.618 ZONE (NOT TOUCH)
    # =========================================================

    if direction == "Bullish":

        if close <= fibs["0.618"]:
            return {
                "triggered": True,
                "status": "ENTRY_TRIGGER",
                "entry": fibs["0.618"]
            }

    if direction == "Bearish":

        if close >= fibs["0.618"]:
            return {
                "triggered": True,
                "status": "ENTRY_TRIGGER",
                "entry": fibs["0.618"]
            }

    return {"triggered": False}


# =========================================================
# CONFIRMATION (CLOSE BACK IN DIRECTION OF TREND)
# =========================================================
def detect_fib_confirmation(event, candle):

    close = f(candle["Close"])

    direction = event["direction"]

    seed_high = event["high"]
    seed_low = event["low"]

    if direction == "Bullish":
        if close > seed_high:
            return {
                "confirmed": True,
                "status": "CONFIRMED",
                "reason": "Close above seed high"
            }

    if direction == "Bearish":
        if close < seed_low:
            return {
                "confirmed": True,
                "status": "CONFIRMED",
                "reason": "Close below seed low"
            }

    return {"confirmed": False}


# =========================================================
# FAILURE (SWING INVALIDATION ONLY — CRITICAL FIX)
# =========================================================
def detect_fib_failure(event, candle):

    close = f(candle["Close"])

    if event["direction"] == "Bullish":
        if close < event["swing_low"]:
            return {"failed": True, "status": "FAILED"}

    if event["direction"] == "Bearish":
        if close > event["swing_high"]:
            return {"failed": True, "status": "FAILED"}

    return {"failed": False}

def fib_event_rules(event, candle):

    if event.get("days_active", 0) > 30:
        return "EXPIRE"

    status = event.get("status")

    entry = detect_fib_entry(event, candle)
    confirm = detect_fib_confirmation(event, candle)
    fail = detect_fib_failure(event, candle)

    # =========================================================
    # SEED → ENTRY or DIRECT CONFIRMATION (FIXED GAP)
    # =========================================================
    if status == "SEED":

        # PRIORITY 1: immediate structural break
        if confirm.get("confirmed"):
            return "CONFIRM"

        # PRIORITY 2: normal entry
        if entry.get("triggered"):
            event["entry"] = entry["entry"]
            return "ENTRY_TRIGGER"

        return None

    if status == "ENTRY_TRIGGER":

        if confirm.get("confirmed"):
            return "CONFIRM"

        if fail.get("failed"):
            return "FAIL"

        return None

    if status == "CONFIRMED":

        if fail.get("failed"):
            return "FAIL"

        return None

    return None

# =========================================================
# TRADE BUILDER (FIB ZONE ENTRY + SWING STRUCTURE STOP)
# =========================================================
def build_fib_trade_state(event):

    fibs = event["fib_levels"]

    swing_high = event["swing_high"]
    swing_low = event["swing_low"]
    rng = max(swing_high - swing_low, 1e-9)

    if event["direction"] == "Bullish":

        return {
            "trade_type": "FIBONACCI_PULLBACK",
            "direction": "LONG",
            "entry": fibs["0.618"],
            "stop": swing_low,
            "invalidation": swing_low,
            "support": fibs["0.618"],
            "resistance": swing_high,
            "target1": swing_high,
            "target2": swing_high + rng,
            "failure": "Close below swing low",
            "interpretation": "Institutional fib retracement continuation LONG"
        }

    if event["direction"] == "Bearish":

        return {
            "trade_type": "FIBONACCI_PULLBACK",
            "direction": "SHORT",
            "entry": fibs["0.618"],
            "stop": swing_high,
            "invalidation": swing_high,
            "support": swing_low,
            "resistance": fibs["0.618"],
            "target1": swing_low,
            "target2": swing_low - rng,
            "failure": "Close above swing high",
            "interpretation": "Institutional fib retracement continuation SHORT"
        }

    return {}


# =========================================================
# ANALYZE ENGINE
# =========================================================
def analyze_fibonacci(df, event_store=None):

    latest_pattern = None

    for i in range(len(df) - 1, 10, -1):

        detected = detect_fib_pullback(df.iloc[i], df, i)

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "close": detected["close"],
                "swing_high": detected["swing_high"],
                "swing_low": detected["swing_low"],
                "fib_levels": detected["fib_levels"],
                "index": i,
                "date": extract_event_date(df, i),
                "status": "SEED"
            }
            break

    if not latest_pattern:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]
        latest_pattern["days_active"] = i - latest_pattern["index"]

        if latest_pattern["status"] == "SEED":

            if detect_fib_entry(latest_pattern, candle).get("triggered"):
                latest_pattern.update(detect_fib_entry(latest_pattern, candle))
                latest_pattern["status"] = "ENTRY_TRIGGER"

        elif latest_pattern["status"] == "ENTRY_TRIGGER":

            if detect_fib_confirmation(latest_pattern, candle).get("confirmed"):
                latest_pattern["status"] = "CONFIRMED"

            if detect_fib_failure(latest_pattern, candle).get("failed"):
                latest_pattern["status"] = "FAILED"
                break

        elif latest_pattern["status"] == "CONFIRMED":

            if detect_fib_failure(latest_pattern, candle).get("failed"):
                latest_pattern["status"] = "FAILED"
                break

    trade = build_fib_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "FIBONACCI_PULLBACK"
    }