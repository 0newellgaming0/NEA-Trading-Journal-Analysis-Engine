# =========================================================
# ENGULFING MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("engulfing")

# =========================================================
# DETECTOR (PINBAR + INSTITUTIONAL HYBRID CORE)
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

    if any(v is None for v in [po, pc, ph, pl, o, c, h, l]):
        return {"detected": False}

    if ph <= pl or h <= l:
        return {"detected": False}

    # =========================================================
    # STRUCTURE BASELINES
    # =========================================================
    prev_high = max(po, pc)
    prev_low = min(po, pc)

    curr_high = max(o, c)
    curr_low = min(o, c)

    prev_body = abs(pc - po)
    curr_body = abs(c - o)

    # avoid divide errors
    if prev_body <= 1e-9 or curr_body <= 1e-9:
        return {"detected": False}

    engulf_ratio = curr_body / max(prev_body, 1e-9)

    true_engulf = (
        curr_high >= prev_high and
        curr_low <= prev_low
    )

    # =========================================================
    # 🔥 INSTITUTIONAL FILTER LAYER (NEW CORE)
    # =========================================================

    # 1. Must be real displacement engulfing
    if not true_engulf:
        return {"detected": False}

    # 2. Minimum displacement threshold (institutional strength gate)
    if engulf_ratio < 1.25:
        return {"detected": False}

    # 3. Directional pressure validation (STRICT)
    bullish_pressure = (
        pc < po and
        c > o and
        c > ph   # closes above previous high (key upgrade)
    )

    bearish_pressure = (
        pc > po and
        c < o and
        c < pl   # closes below previous low (key upgrade)
    )

    # =========================================================
    # OUTSIDE BAR (INSTITUTIONAL VERSION)
    # =========================================================
    outside_bar = (h > ph and l < pl)

    # =========================================================
    # STRENGTH CLASSIFICATION
    # =========================================================
    if engulf_ratio >= 2.0:
        strength = "INSTITUTIONAL"
    elif engulf_ratio >= 1.5:
        strength = "STRONG"
    else:
        strength = "STANDARD"

    # =========================================================
    # FINAL CLASSIFICATION
    # =========================================================
    if bullish_pressure:
        return {
            "detected": True,
            "type": "BULLISH_ENGULFING",
            "direction": "Bullish",
            "strength": strength,
            "engulf_ratio": round(engulf_ratio, 2),
            "high": h,
            "low": l,
            "open": o,
            "close": c
        }

    if bearish_pressure:
        return {
            "detected": True,
            "type": "BEARISH_ENGULFING",
            "direction": "Bearish",
            "strength": strength,
            "engulf_ratio": round(engulf_ratio, 2),
            "high": h,
            "low": l,
            "open": o,
            "close": c
        }

    if outside_bar and (bullish_pressure or bearish_pressure):
        return {
            "detected": True,
            "type": "OUTSIDE_BAR_ENGULFING",
            "direction": "Bullish" if c > o else "Bearish",
            "strength": strength,
            "engulf_ratio": round(engulf_ratio, 2),
            "high": h,
            "low": l,
            "open": o,
            "close": c
        }

    return {"detected": False}


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
            "interpretation": "Bullish engulfing structural reversal setup"
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
            "interpretation": "Bearish engulfing structural reversal setup"
        }

    return {}


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

        event_date = extract_event_date(df, i)

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],
            "trade_type": "REVERSAL",
            "high": detected["high"],
            "low": detected["low"],
            "index": i,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(f"[ENGULFING] Found {detected['type']} at index={i}")
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