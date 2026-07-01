# =========================================================
# ENGULFING MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE - PINBAR PARITY FIXED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("engulfing")


# =========================================================
# DETECTOR (PURE - PINBAR STYLE)
# =========================================================
def detect_engulfing(prev_candle, curr_candle, f):

    logger.debug("[ENGULFING] detect_engulfing() called")

    try:
        po = f(prev_candle.get("Open"))
        pc = f(prev_candle.get("Close"))
        ph = f(prev_candle.get("High"))
        pl = f(prev_candle.get("Low"))

        o = f(curr_candle.get("Open"))
        c = f(curr_candle.get("Close"))
        h = f(curr_candle.get("High"))
        l = f(curr_candle.get("Low"))

    except Exception as e:
        logger.error(f"[ENGULFING] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if None in [po, pc, ph, pl, o, c, h, l]:
        return {"detected": False}

    if ph <= pl or h <= l:
        return {"detected": False}

    prev_high = max(po, pc)
    prev_low = min(po, pc)

    curr_high = max(o, c)
    curr_low = min(o, c)

    # =========================================================
    # CORE ENGULFING CONDITION (STRUCTURAL ONLY)
    # =========================================================
    is_engulfing = (
        curr_high >= prev_high and
        curr_low <= prev_low
    )

    if not is_engulfing:
        return {"detected": False}

    # =========================================================
    # DIRECTION (SIMPLE + PINBAR PARITY STYLE)
    # =========================================================
    body_prev = pc - po
    body_curr = c - o

    bullish = body_curr > 0 and c >= max(po, pc)
    bearish = body_curr < 0 and c <= min(po, pc)

    direction = None
    if bullish:
        direction = "Bullish"
    elif bearish:
        direction = "Bearish"
    else:
        direction = "Neutral"

    return {
        "detected": True,
        "type": "Engulfing",
        "direction": direction,

        "high": h,
        "low": l,

        "prev_high": ph,
        "prev_low": pl
    }


# =========================================================
# TRADE BUILDER (PINBAR STRUCTURAL MIRROR)
# =========================================================
def build_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

    if direction == "Bullish":
        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",

            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,

            "target1": high + rng,
            "target2": high + 2 * rng,

            "failure": f"Close below {low}",
            "interpretation": "Bullish engulfing = displacement + control shift"
        }

    if direction == "Bearish":
        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",

            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,

            "target1": low - rng,
            "target2": low - 2 * rng,

            "failure": f"Close above {high}",
            "interpretation": "Bearish engulfing = displacement + control shift"
        }

    return {
        "trade_type": "REVERSAL",
        "direction": "NONE",
        "failure": "No directional confirmation",
        "interpretation": "Neutral engulfing structure"
    }


# =========================================================
# EVENT RULES (PINBAR PARITY)
# =========================================================
def event_rules(event, candle, close, high, low):

    status = event.get("status")

    if status == "PENDING":

        if event["direction"] == "Bullish":
            if close > event["high"]:
                return "CONFIRM"
            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":
            if close < event["low"]:
                return "CONFIRM"
            if close > event["high"]:
                return "FAIL"

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":
            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":
            if close > event["high"]:
                return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (PINBAR STRUCTURE MIRROR)
# =========================================================
def analyze_engulfing(df, event_store):

    logger.info("[ENGULFING] analyze_engulfing() called")

    latest_pattern = None

    for i in range(len(df) - 1, 0, -1):

        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        prev_candle = {
            "Open": prev.get("Open"),
            "High": prev.get("High"),
            "Low": prev.get("Low"),
            "Close": prev.get("Close")
        }

        curr_candle = {
            "Open": curr.get("Open"),
            "High": curr.get("High"),
            "Low": curr.get("Low"),
            "Close": curr.get("Close")
        }

        detected = detect_engulfing(prev_candle, curr_candle, float)

        if not detected.get("detected"):
            continue

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],

            "high": detected["high"],
            "low": detected["low"],

            "index": i,
            "date": extract_event_date(df, i),

            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = event_rules(latest_pattern, candle, close, high, low)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

    trade = build_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }