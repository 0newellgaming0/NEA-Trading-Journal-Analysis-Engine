# =========================================================
# RISING / FALLING THREE METHODS MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("three_methods")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_three_methods(c1, c2, c3, c4, c5, f):

    logger.debug("[3-METHODS] detect_three_methods() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
        o4, h4, l4, c4c = f(c4["Open"]), f(c4["High"]), f(c4["Low"]), f(c4["Close"])
        o5, h5, l5, c5c = f(c5["Open"]), f(c5["High"]), f(c5["Low"]), f(c5["Close"])

    except Exception as e:
        logger.error(f"[3-METHODS] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1,h1,l1,c1c,o2,h2,l2,c2c,o3,h3,l3,c3c,o4,h4,l4,c4c,o5,h5,l5,c5c]):
        return {"detected": False}

    # =========================================================
    # BASE STRUCTURE FLAGS
    # =========================================================
    bull1, bull5 = c1c > o1, c5c > o5
    bear1, bear5 = c1c < o1, c5c < o5

    range3 = h3 - l3

    # =========================================================
    # RISING THREE METHODS (BULLISH CONTINUATION)
    # Structure:
    # 1 bearish strong
    # 2-4 small bearish consolidation inside range
    # 5 strong bullish breakout
    # =========================================================
    rising_three_methods = (
        bear1 and bull5 and
        c2c < c1c and c3c < c2c and c4c < c3c and
        max(h2, h3, h4) <= h1 and
        min(l2, l3, l4) >= l1 and
        c5c > h1
    )

    # =========================================================
    # FALLING THREE METHODS (BEARISH CONTINUATION)
    # Structure:
    # 1 bullish strong
    # 2-4 small bullish consolidation inside range
    # 5 strong bearish breakout
    # =========================================================
    falling_three_methods = (
        bull1 and bear5 and
        c2c > c1c and c3c > c2c and c4c > c3c and
        max(h2, h3, h4) <= h1 and
        min(l2, l3, l4) >= l1 and
        c5c < l1
    )

    # =========================================================
    # RETURN
    # =========================================================
    if rising_three_methods:
        return {
            "detected": True,
            "type": "Rising Three Methods",
            "direction": "Bullish",
            "high": h5,
            "low": l5,
            "close": c5c
        }

    if falling_three_methods:
        return {
            "detected": True,
            "type": "Falling Three Methods",
            "direction": "Bearish",
            "high": h5,
            "low": l5,
            "close": c5c
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_three_methods_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    pattern = event.get("type")

    # =========================================================
    # CONTINUATION ONLY (HIGH-CONVICTION STRUCTURE)
    # =========================================================
    if direction == "Bullish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng * 1.5,
            "target2": high + rng * 3.0,
            "failure": f"Close below {low}",
            "interpretation": "Rising Three Methods bullish continuation expansion structure."
        }

    if direction == "Bearish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng * 1.5,
            "target2": low - rng * 3.0,
            "failure": f"Close above {high}",
            "interpretation": "Falling Three Methods bearish continuation expansion structure."
        }

    logger.warning(f"[3-METHODS] Unknown direction in trade builder")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def three_methods_event_rules(event, candle, close, high, low):

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
# MAIN ANALYZER (PINBAR-MIRRORED ARCHITECTURE)
# =========================================================
def analyze_three_methods(df, event_store, f=float):

    logger.info("[3-METHODS] analyze_three_methods() called")

    latest_pattern = None

    # BACKWARD SCAN (5-CANDLE WINDOW)
    for i in range(len(df) - 1, 3, -1):

        c1 = df.iloc[i - 4]
        c2 = df.iloc[i - 3]
        c3 = df.iloc[i - 2]
        c4 = df.iloc[i - 1]
        c5 = df.iloc[i]

        detected = detect_three_methods(c1, c2, c3, c4, c5, f)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)
        direction = detected["direction"]

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": direction,
            "trade_type": "CONTINUATION",
            "high": detected["high"],
            "low": detected["low"],
            "index": i - 4,   # anchor = first candle
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[3-METHODS] Found {detected['type']} at index={i-4}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = three_methods_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "5-candle continuation confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_three_methods_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_three_methods_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }