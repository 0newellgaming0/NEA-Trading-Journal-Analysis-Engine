# =========================================================
# BULL / BEAR PULLBACK MODULE (TLINE PARITY - FIXED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date
from modules.tline import get_tline, get_sma

logger = logging.getLogger("flag_module")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# PRIMARY LEVELS
# =========================================================
def get_primary_levels(df, i, lookback=10):

    try:
        window = df.iloc[max(0, i - lookback): i]

        return {
            "support": f(window["Low"].min()),
            "resistance": f(window["High"].max()),
            "range": f(window["High"].max() - window["Low"].min()),
            "midpoint": f((window["High"].max() + window["Low"].min()) / 2)
        }

    except:
        return {
            "support": 0.0,
            "resistance": 0.0,
            "range": 0.0,
            "midpoint": 0.0
        }


# =========================================================
# DETECTION (TLINE PARITY FIXED)
# =========================================================
def detect_pullback(candle, df, i):

    high = f(candle["High"])
    low = f(candle["Low"])
    open_ = f(candle["Open"])
    close = f(candle["Close"])

    ema8 = f(get_tline(df, i))
    ema8_prev = f(get_tline(df, i - 1))

    sma50 = f(get_sma(df, i, 50))
    sma200 = f(get_sma(df, i, 200))

    if high <= low:
        return {"detected": False}

    bullish_trend = ema8 > sma50 and sma50 >= sma200
    bearish_trend = ema8 < sma50 and sma50 <= sma200

    # =========================================================
    # SEED = FIRST DISPLACEMENT INTO EMA8 (NOT REJECTION)
    # =========================================================
    bullish_seed = (
        bullish_trend
        and close < ema8
        and close < open_
    )

    bearish_seed = (
        bearish_trend
        and close > ema8
        and close > open_
    )

    if bullish_seed:
        return {
            "detected": True,
            "type": "EMA_PULLBACK",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "ema8": ema8,
            "entry_high": high,
            "entry_low": low,
            "status": "SEED"
        }

    if bearish_seed:
        return {
            "detected": True,
            "type": "EMA_PULLBACK",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "ema8": ema8,
            "entry_high": high,
            "entry_low": low,
            "status": "SEED"
        }

    return {"detected": False}


# =========================================================
# ENTRY (MATCHES YOUR RULE: BREAK / CLOSE THROUGH LEVEL)
# =========================================================
def detect_pullback_entry(event, candle):

    close = f(candle["Close"])
    ema8 = f(get_tline_from_event(event)) if "get_tline_from_event" in globals() else f(event.get("ema8", 0))

    direction = event.get("direction")

    # =========================================================
    # ENTRY = CONTINUATION OF DISPLACEMENT, NOT RECLAIM
    # Bullish: continuation = break BELOW EMA8
    # Bearish: continuation = break ABOVE EMA8
    # =========================================================

    if direction == "Bullish":
        if close < ema8:
            return {
                "triggered": True,
                "status": "ENTRY_TRIGGER"
            }

    if direction == "Bearish":
        if close > ema8:
            return {
                "triggered": True,
                "status": "ENTRY_TRIGGER"
            }

    return {"triggered": False}


# =========================================================
# CONFIRMATION
# =========================================================
def detect_pullback_confirmation(event, candle):

    if event.get("status") != "ENTRY_TRIGGER":
        return {"confirmed": False}

    close = f(candle["Close"])
    open_ = f(candle["Open"])

    direction = event.get("direction")

    if direction == "Bullish":
        if close > event["entry_high"] and close > open_:
            return {"confirmed": True, "status": "CONFIRMED"}

    if direction == "Bearish":
        if close < event["entry_low"] and close < open_:
            return {"confirmed": True, "status": "CONFIRMED"}

    return {"confirmed": False}


# =========================================================
# FAILURE (FIXED TO MATCH YOUR RULE)
# =========================================================
def detect_pullback_failure(event, candle):

    close = f(candle["Close"])

    status = event.get("status")
    direction = event.get("direction")

    if status not in ("SEED", "ENTRY_TRIGGER", "CONFIRMED"):
        return {"failed": False}

    # =========================================================
    # FAILURE = BREACH OF SEED STRUCTURE
    # =========================================================

    if direction == "Bullish":
        if close < event["low"]:
            return {"failed": True, "status": "FAILED"}

    if direction == "Bearish":
        if close > event["high"]:
            return {"failed": True, "status": "FAILED"}

    return {"failed": False}


# =========================================================
# EVENT RULES
# =========================================================
def pullback_event_rules(event, candle):

    if event.get("days_active", 0) > 20:
        return "EXPIRE"

    status = event.get("status")

    if status == "SEED":
        if detect_pullback_entry(event, candle).get("triggered"):
            return "ENTRY_TRIGGER"
        return None

    if status == "ENTRY_TRIGGER":
        if detect_pullback_confirmation(event, candle).get("confirmed"):
            return "CONFIRM"
        if detect_pullback_failure(event, candle).get("failed"):
            return "FAIL"
        return None

    if status == "CONFIRMED":
        if detect_pullback_failure(event, candle).get("failed"):
            return "FAIL"
        return None

    return None


# =========================================================
# TRADE BUILDER (PARITY SAFE)
# =========================================================
def build_pullback_trade_state(event):

    high = f(event["high"])
    low = f(event["low"])
    rng = max(high - low, 1e-9)

    direction = event["direction"]
    levels = event.get("levels", {})

    entry_high = f(event.get("entry_high", high))
    entry_low = f(event.get("entry_low", low))

    if direction == "Bullish":
        return {
            "trade_type": "PULLBACK_CONTINUATION",
            "direction": "LONG",
            "entry": entry_high,
            "stop": entry_low - (0.1 * rng),
            "invalidation": entry_low,
            "support": levels.get("support", entry_low),
            "resistance": levels.get("resistance", high),
            "target1": entry_high + rng,
            "target2": entry_high + (2 * rng),
            "failure": "Close below seed low",
            "interpretation": "EMA pullback continuation structure"
        }

    if direction == "Bearish":
        return {
            "trade_type": "PULLBACK_CONTINUATION",
            "direction": "SHORT",
            "entry": entry_low,
            "stop": entry_high + (0.1 * rng),
            "invalidation": entry_high,
            "support": levels.get("support", low),
            "resistance": levels.get("resistance", entry_high),
            "target1": entry_low - rng,
            "target2": entry_low - (2 * rng),
            "failure": "Close above seed high",
            "interpretation": "EMA pullback continuation structure"
        }

    return {}


# =========================================================
# ANALYZE (FIXED FLOW ALIGNMENT)
# =========================================================
def analyze_pullback(df, event_store=None):

    latest_pattern = None

    for i in range(len(df) - 1, 1, -1):

        detected = detect_pullback(df.iloc[i], df, i)

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "close": detected["close"],
                "entry_high": detected["entry_high"],
                "entry_low": detected["entry_low"],
                "index": i,
                "date": extract_event_date(df, i),
                "status": "SEED",
                "levels": get_primary_levels(df, i)
            }
            break

    if not latest_pattern:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]
        latest_pattern["days_active"] = i - latest_pattern["index"]

        action = pullback_event_rules(latest_pattern, candle)

        if action == "ENTRY_TRIGGER":
            latest_pattern["status"] = "ENTRY_TRIGGER"

        elif action == "CONFIRM":
            latest_pattern["status"] = "CONFIRMED"
            break

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            break

        elif action == "EXPIRE":
            latest_pattern["status"] = "EXPIRED"
            break

    trade = build_pullback_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "PULLBACK_REGIME"
    }