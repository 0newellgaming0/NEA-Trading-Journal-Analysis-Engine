# =========================================================
# THRUSTING / DELIBERATION PATTERN MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("thrust_deliberation")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_thrust_deliberation(candle, prev_candle, f):

    logger.debug("[THRUST/DELIB] detect_thrust_deliberation() called")

    try:
        # CURRENT
        o2 = f(candle["Open"])
        h2 = f(candle["High"])
        l2 = f(candle["Low"])
        c2 = f(candle["Close"])

        # PREVIOUS
        o1 = f(prev_candle["Open"])
        h1 = f(prev_candle["High"])
        l1 = f(prev_candle["Low"])
        c1 = f(prev_candle["Close"])

    except Exception as e:
        logger.error(f"[THRUST/DELIB] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1, h1, l1, c1, o2, h2, l2, c2]):
        return {"detected": False}

    if h1 <= l1 or h2 <= l2:
        return {"detected": False}

    prev_bull = c1 > o1
    prev_bear = c1 < o1
    curr_bull = c2 > o2
    curr_bear = c2 < o2

    prev_body = abs(c1 - o1)
    curr_body = abs(c2 - o2)

    prev_range = max(h1 - l1, 1e-9)
    curr_range = max(h2 - l2, 1e-9)

    # =========================================================
    # THRUSTING PATTERN (BEARISH CONTINUATION WEAKNESS)
    # Structure:
    # strong bearish candle that partially retraces into prior bullish candle
    # but fails to close above midpoint (rejection of demand)
    # =========================================================
    thrusting_pattern = (
        prev_bear and
        curr_bear and
        c2 > l1 and                      # thrusts upward into prior range
        c2 < (o1 + c1) / 2              # fails to reach midpoint
    )

    # =========================================================
    # DELIBERATION PATTERN (INDECISION / HESITATION)
    # Structure:
    # small body after strong move, reduced volatility, equilibrium
    # =========================================================
    deliberation_pattern = (
        curr_body < prev_body * 0.6 and
        curr_range < prev_range * 0.7 and
        abs(c2 - o2) <= (h2 - l2) * 0.3
    )

    # =========================================================
    # OUTPUT
    # =========================================================
    if thrusting_pattern:
        return {
            "detected": True,
            "type": "Thrusting Pattern",
            "direction": "Bearish",
            "high": h2,
            "low": l2,
            "open": o2,
            "close": c2
        }

    if deliberation_pattern:
        return {
            "detected": True,
            "type": "Deliberation Pattern",
            "direction": "Neutral",
            "high": h2,
            "low": l2,
            "open": o2,
            "close": c2
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_thrust_deliberation_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    pattern = event.get("type")
    direction = event.get("direction")

    # =========================================================
    # THRUSTING PATTERN (BEARISH CONTINUATION / WEAK REJECTION)
    # =========================================================
    if pattern == "Thrusting Pattern":

        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - rng * 2,
            "failure": f"Close above {high}",
            "interpretation": "Thrusting Pattern shows failed bullish retracement and bearish continuation pressure."
        }

    # =========================================================
    # DELIBERATION PATTERN (NO DIRECT EDGE — STRUCTURAL SIGNAL)
    # =========================================================
    if pattern == "Deliberation Pattern":

        return {
            "trade_type": "NEUTRAL",
            "direction": "NONE",
            "entry": 0.0,
            "stop": 0.0,
            "invalidation": 0.0,
            "target1": 0.0,
            "target2": 0.0,
            "failure": "No directional failure condition",
            "interpretation": "Deliberation indicates market hesitation and potential transition zone."
        }

    logger.warning(f"[THRUST/DELIB] Unknown pattern type")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def thrust_deliberation_event_rules(event, candle, close, high, low):

    status = event.get("status")

    if status == "PENDING":

        if event["direction"] == "Bearish":
            if close < event["low"]:
                return "CONFIRM"
            if close > event["high"]:
                return "FAIL"

        elif event["direction"] == "Neutral":
            # deliberation does not confirm direction
            if close > event["high"] or close < event["low"]:
                return "CONFIRM"

    elif status == "CONFIRMED":

        if event["direction"] == "Bearish":
            if close > event["high"]:
                return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (PINBAR-MIRRORED ARCHITECTURE)
# =========================================================
def analyze_thrust_deliberation(df, event_store, f=float):

    logger.info("[THRUST/DELIB] analyze_thrust_deliberation() called")

    latest_pattern = None

    # BACKWARD SCAN (2-CANDLE STRUCTURE)
    for i in range(len(df) - 1, 0, -1):

        prev_candle = df.iloc[i - 1]
        candle = df.iloc[i]

        detected = detect_thrust_deliberation(candle, prev_candle, f)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)
        direction = detected["direction"]

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": direction,
            "trade_type": "MIXED",
            "high": detected["high"],
            "low": detected["low"],
            "index": i - 1,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[THRUST/DELIB] Found {detected['type']} at index={i-1}"
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

        action = thrust_deliberation_event_rules(
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
            latest_pattern["status_reason"] = "Structure validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_thrust_deliberation_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_thrust_deliberation_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }