# =========================================================
# TASUKI GAP FAMILY MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# PROGRESSIVE EVENT VERSION (SEED REQUIRED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("tasuki_gap")


# =========================================================
# FULL PATTERN DETECTOR (CONFIRMATION)
# =========================================================
def detect_tasuki_gap(c1, c2, c3, f):

    logger.debug("[TASUKI] detect_tasuki_gap() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1,h1,l1,c1c,o2,h2,l2,c2c,o3,h3,l3,c3c]):
        return {"detected": False}

    # ---------------------------
    # Rising Tasuki Gap
    # ---------------------------
    rising = (
        c1c > o1 and
        o2 > c1c and
        c2c > o2 and
        o3 < c2c and
        c3c < c2c and
        c3c > c1c
    )

    # ---------------------------
    # Falling Tasuki Gap
    # ---------------------------
    falling = (
        c1c < o1 and
        o2 < c1c and
        c2c < o2 and
        o3 > c2c and
        c3c > c2c and
        c3c < c1c
    )

    if rising:
        return {
            "detected": True,
            "type": "Rising Tasuki Gap",
            "direction": "Bullish",
            "high": h2,
            "low": l2,
            "close": c2c
        }

    if falling:
        return {
            "detected": True,
            "type": "Falling Tasuki Gap",
            "direction": "Bearish",
            "high": h2,
            "low": l2,
            "close": c2c
        }

    return {"detected": False}


# =========================================================
# REQUIRED SEED DETECTOR (MANDATORY EARLY STRUCTURE)
# =========================================================
def detect_tasuki_seed(c1, c2, c3, f):

    logger.debug("[TASUKI] seed detection called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except Exception:
        return {"detected": False}

    if any(v is None for v in [o1,h1,l1,c1c,o2,h2,l2,c2c,o3,h3,l3,c3c]):
        return {"detected": False}

    bull1 = c1c > o1
    bear1 = c1c < o1

    # ---------------------------
    # EARLY STRUCTURE ONLY (NO GAP REQUIREMENT YET)
    # ---------------------------

    rising_seed = (
        bull1 and
        o2 > c1c and
        c2c > o2 and
        o3 < c2c and
        c3c < c2c
    )

    falling_seed = (
        bear1 and
        o2 < c1c and
        c2c < o2 and
        o3 > c2c and
        c3c > c2c
    )

    if rising_seed:
        return {
            "detected": True,
            "type": "Rising Tasuki Gap (Seed)",
            "direction": "Bullish",
            "high": h1,
            "low": l1,
            "stage": "SEED"
        }

    if falling_seed:
        return {
            "detected": True,
            "type": "Falling Tasuki Gap (Seed)",
            "direction": "Bearish",
            "high": h1,
            "low": l1,
            "stage": "SEED"
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER
# =========================================================
def build_tasuki_gap_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    if event["direction"] == "Bullish":
        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + rng * 2,
            "failure": f"Close below {low}",
            "interpretation": "Rising Tasuki Gap continuation expansion."
        }

    if event["direction"] == "Bearish":
        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - rng * 2,
            "failure": f"Close above {high}",
            "interpretation": "Falling Tasuki Gap continuation expansion."
        }

    return {}


# =========================================================
# EVENT RULES (SEED IS NOT OPTIONAL)
# =========================================================
def tasuki_gap_event_rules(event, candle, close, high, low):

    status = event.get("status")

    # ---------------------------
    # SEED STATE (FORCED LIFECYCLE ENTRY POINT)
    # ---------------------------
    if status == "SEED":

        if event["direction"] == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        if event["direction"] == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # ---------------------------
    # PENDING STATE
    # ---------------------------
    elif status == "PENDING":

        if event["direction"] == "Bullish":
            if close > event["high"]:
                return "CONFIRM"
            if close < event["low"]:
                return "FAIL"

        if event["direction"] == "Bearish":
            if close < event["low"]:
                return "CONFIRM"
            if close > event["high"]:
                return "FAIL"

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish" and close < event["low"]:
            return "FAIL"

        if event["direction"] == "Bearish" and close > event["high"]:
            return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (SEED IS REQUIRED PATH)
# =========================================================
def analyze_tasuki_gap(df, event_store, f=float):

    logger.info("[TASUKI] analyze_tasuki_gap() called")

    latest_pattern = None

    # =========================================================
    # PASS 1: FULL CONFIRMATION
    # =========================================================
    for i in range(len(df) - 1, 1, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        detected = detect_tasuki_gap(c1, c2, c3, f)

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "index": i - 2,
                "date": extract_event_date(df, i),
                "status": "PENDING",
                "status_reason": "Full Tasuki Gap detected"
            }
            break

    # =========================================================
    # PASS 2: REQUIRED SEED DETECTION (NOT OPTIONAL)
    # =========================================================
    if latest_pattern is None:

        for i in range(len(df) - 1, 1, -1):

            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            seed = detect_tasuki_seed(c1, c2, c3, f)

            if seed.get("detected"):

                latest_pattern = {
                    "id": 1,
                    "detected": True,
                    "type": seed["type"],
                    "direction": seed["direction"],
                    "high": seed["high"],
                    "low": seed["low"],
                    "index": i - 2,
                    "date": extract_event_date(df, i),
                    "status": "SEED",
                    "status_reason": "Early Tasuki structure forming"
                }
                break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =========================================================
    # VALIDATION LOOP
    # =========================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = tasuki_gap_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Tasuki structure confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Tasuki invalidated"

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Expired"

            break

    trade = build_tasuki_gap_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }