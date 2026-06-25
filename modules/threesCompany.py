# =========================================================
# THREE CANDLE FAMILY MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("three_candle_family")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_three_candle_pattern(c1, c2, c3, f):

    logger.debug("[3-CANDLE] detect_three_candle_pattern() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except Exception as e:
        logger.error(f"[3-CANDLE] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1,h1,l1,c1c,o2,h2,l2,c2c,o3,h3,l3,c3c]):
        return {"detected": False}

    # =========================================================
    # HELPER FLAGS
    # =========================================================
    bull1, bull2, bull3 = c1c > o1, c2c > o2, c3c > o3
    bear1, bear2, bear3 = c1c < o1, c2c < o2, c3c < o3

    range1 = h1 - l1
    range2 = h2 - l2
    range3 = h3 - l3

    mid1 = (h1 + l1) / 2
    mid3 = (h3 + l3) / 2

    # =========================================================
    # THREE WHITE SOLDIERS (BULLISH CONTINUATION)
    # =========================================================
    three_white_soldiers = (
        bull1 and bull2 and bull3 and
        c2c > c1c and
        c3c > c2c and
        c2c > mid1
    )

    # =========================================================
    # THREE BLACK CROWS (BEARISH CONTINUATION)
    # =========================================================
    three_black_crows = (
        bear1 and bear2 and bear3 and
        c2c < c1c and
        c3c < c2c and
        c2c < mid1
    )

    # =========================================================
    # THREE INSIDE UP (BULLISH REVERSAL)
    # c2 inside c1, c3 breaks up
    # =========================================================
    three_inside_up = (
        bear1 and
        l2 >= l1 and h2 <= h1 and
        bull3 and
        c3c > h1
    )

    # =========================================================
    # THREE INSIDE DOWN (BEARISH REVERSAL)
    # c2 inside c1, c3 breaks down
    # =========================================================
    three_inside_down = (
        bull1 and
        l2 >= l1 and h2 <= h1 and
        bear3 and
        c3c < l1
    )

    # =========================================================
    # THREE OUTSIDE UP (ENGULF THEN BREAK HIGH)
    # =========================================================
    three_outside_up = (
        bear1 and bull2 and
        h2 > h1 and l2 < l1 and
        bull3 and
        c3c > h2
    )

    # =========================================================
    # THREE OUTSIDE DOWN (ENGULF THEN BREAK LOW)
    # =========================================================
    three_outside_down = (
        bull1 and bear2 and
        h2 > h1 and l2 < l1 and
        bear3 and
        c3c < l2
    )

    # =========================================================
    # RETURN STRUCTURE
    # =========================================================
    if three_white_soldiers:
        return {
            "detected": True,
            "type": "Three White Soldiers",
            "direction": "Bullish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    if three_black_crows:
        return {
            "detected": True,
            "type": "Three Black Crows",
            "direction": "Bearish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    if three_inside_up:
        return {
            "detected": True,
            "type": "Three Inside Up",
            "direction": "Bullish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    if three_inside_down:
        return {
            "detected": True,
            "type": "Three Inside Down",
            "direction": "Bearish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    if three_outside_up:
        return {
            "detected": True,
            "type": "Three Outside Up",
            "direction": "Bullish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    if three_outside_down:
        return {
            "detected": True,
            "type": "Three Outside Down",
            "direction": "Bearish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_three_candle_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    pattern = event.get("type")

    # =========================================================
    # CONTINUATION PATTERNS
    # =========================================================
    if pattern in ["Three White Soldiers"]:

        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + 2 * rng,
            "failure": f"Close below {low}",
            "interpretation": "Strong bullish continuation momentum expansion."
        }

    if pattern in ["Three Black Crows"]:

        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - 2 * rng,
            "failure": f"Close above {high}",
            "interpretation": "Strong bearish continuation momentum expansion."
        }

    # =========================================================
    # REVERSAL PATTERNS
    # =========================================================
    if pattern in ["Three Inside Up", "Three Outside Up"]:

        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + 2 * rng,
            "failure": f"Close below {low}",
            "interpretation": f"{pattern} bullish reversal structure."
        }

    if pattern in ["Three Inside Down", "Three Outside Down"]:

        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - 2 * rng,
            "failure": f"Close above {high}",
            "interpretation": f"{pattern} bearish reversal structure."
        }

    logger.warning(f"[3-CANDLE] Unknown pattern type: {pattern}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def three_candle_event_rules(event, candle, close, high, low):

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
def analyze_three_candle_patterns(df, event_store, f=float):

    logger.info("[3-CANDLE] analyze_three_candle_patterns() called")

    latest_pattern = None

    # BACKWARD SCAN (ANCHOR AT CANDLE 1 = i-2)
    for i in range(len(df) - 1, 1, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        detected = detect_three_candle_pattern(c1, c2, c3, f)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)
        direction = detected["direction"]

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": direction,
            "trade_type": "REVERSAL",
            "high": detected["high"],
            "low": detected["low"],
            "index": i - 2,   # anchor candle (IMPORTANT)
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[3-CANDLE] Found {detected['type']} at index={i-2}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP (UNCHANGED ENGINE STYLE)
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = three_candle_event_rules(
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
            latest_pattern["status_reason"] = "3-candle structure confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_three_candle_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_three_candle_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }