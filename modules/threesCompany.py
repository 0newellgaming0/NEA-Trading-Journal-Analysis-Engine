# =========================================================
# THREE CANDLE FAMILY MODULE (FIXED - STRUCTURAL PARITY)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("three_candle_family")


# =========================================================
# FULL PATTERN DETECTOR (STRUCTURAL FIX)
# =========================================================
def detect_three_candle_pattern(c1, c2, c3, f):

    logger.debug("[3-CANDLE] detect_three_candle_pattern() called")

    try:
        o1,h1,l1,c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2,h2,l2,c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3,h3,l3,c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except:
        return {"detected": False}

    if None in [o1,h1,l1,c1c,o2,h2,l2,c2c,o3,h3,l3,c3c]:
        return {"detected": False}

    # =====================================================
    # BASIC STRUCTURE
    # =====================================================
    bull1, bull2, bull3 = c1c > o1, c2c > o2, c3c > o3
    bear1, bear2, bear3 = c1c < o1, c2c < o2, c3c < o3

    # =====================================================
    # STRUCTURAL DISPLACEMENT CHECK (FIX #1)
    # =====================================================
    range1 = h1 - l1
    range2 = h2 - l2
    range3 = h3 - l3

    expansion = range3 >= max(range1, range2)

    # =====================================================
    # CLASSIFICATIONS (FIXED LOGIC)
    # =====================================================

    three_white_soldiers = bull1 and bull2 and bull3 and c3c > c2c and expansion
    three_black_crows = bear1 and bear2 and bear3 and c3c < c2c and expansion

    three_inside_up = bear1 and (l2 >= l1 and h2 <= h1) and bull3 and c3c > h1
    three_inside_down = bull1 and (l2 >= l1 and h2 <= h1) and bear3 and c3c < l1

    three_outside_up = bear1 and bull2 and (h2 > h1 and l2 < l1) and bull3 and c3c > h2
    three_outside_down = bull1 and bear2 and (h2 > h1 and l2 < l1) and bear3 and c3c < l2

    if three_white_soldiers:
        return {"detected": True, "type": "Three White Soldiers", "direction": "Bullish", "high": h3, "low": l3}

    if three_black_crows:
        return {"detected": True, "type": "Three Black Crows", "direction": "Bearish", "high": h3, "low": l3}

    if three_inside_up:
        return {"detected": True, "type": "Three Inside Up", "direction": "Bullish", "high": h3, "low": l3}

    if three_inside_down:
        return {"detected": True, "type": "Three Inside Down", "direction": "Bearish", "high": h3, "low": l3}

    if three_outside_up:
        return {"detected": True, "type": "Three Outside Up", "direction": "Bullish", "high": h3, "low": l3}

    if three_outside_down:
        return {"detected": True, "type": "Three Outside Down", "direction": "Bearish", "high": h3, "low": l3}

    return {"detected": False}


# =========================================================
# SEED DETECTOR (FIXED - NO FALSE EARLY FULL MATCH)
# =========================================================
def detect_three_candle_seed(c1, c2, c3, f):

    try:
        o1,h1,l1,c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2,h2,l2,c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3,h3,l3,c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except:
        return {"detected": False}

    bull1, bull2, bull3 = c1c > o1, c2c > o2, c3c > o3
    bear1, bear2, bear3 = c1c < o1, c2c < o2, c3c < o3

    # FIX: seed must NOT include full displacement confirmation
    rising_seed = bull1 and bull2 and c3c >= c2c
    falling_seed = bear1 and bear2 and c3c <= c2c

    if rising_seed:
        return {"detected": True, "type": "Three Candle Seed (Bullish)", "direction": "Bullish", "high": h3, "low": l3}

    if falling_seed:
        return {"detected": True, "type": "Three Candle Seed (Bearish)", "direction": "Bearish", "high": h3, "low": l3}

    return {"detected": False}


# =========================================================
# TRADE BUILDER (UNCHANGED STRUCTURALLY)
# =========================================================
def build_three_candle_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    pattern = event.get("type", "")

    if direction == "Bullish":
        return {
            "trade_type": "REVERSAL" if "Inside" in pattern or "Outside" in pattern else "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + 2 * rng,
            "failure": f"Close below {low}",
            "interpretation": f"{pattern} bullish structure"
        }

    if direction == "Bearish":
        return {
            "trade_type": "REVERSAL" if "Inside" in pattern or "Outside" in pattern else "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - 2 * rng,
            "failure": f"Close above {high}",
            "interpretation": f"{pattern} bearish structure"
        }

    return {}


# =========================================================
# EVENT RULES (FIXED: NO SEED POLLUTION)
# =========================================================
def three_candle_event_rules(event, candle, close, high, low):

    status = event.get("status")

    if status == "SEED":
        # seed cannot confirm, only upgrade or fail
        if close > event["high"] or close < event["low"]:
            return "CONFIRM"

    elif status == "PENDING":

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

        if event["direction"] == "Bullish" and close < event["low"]:
            return "FAIL"

        if event["direction"] == "Bearish" and close > event["high"]:
            return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (FIXED INDEXING + LIFECYCLE)
# =========================================================
def analyze_three_candle_patterns(df, event_store, f=float):

    logger.info("[3-CANDLE] analyze_three_candle_patterns() called")

    latest_pattern = None

    # PASS 1: FULL PATTERN
    for i in range(len(df) - 1, 1, -1):

        c1, c2, c3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]

        detected = detect_three_candle_pattern(c1, c2, c3, f)

        if detected.get("detected"):
            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "index": i,   # FIX: anchor at actual pattern end candle
                "date": extract_event_date(df, i),
                "status": "PENDING",
                "status_reason": "Full pattern detected"
            }
            break

    # PASS 2: SEED
    if latest_pattern is None:

        for i in range(len(df) - 1, 1, -1):

            c1, c2, c3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
            seed = detect_three_candle_seed(c1, c2, c3, f)

            if seed.get("detected"):
                latest_pattern = {
                    "id": 1,
                    "detected": True,
                    "type": seed["type"],
                    "direction": seed["direction"],
                    "high": seed["high"],
                    "low": seed["low"],
                    "index": i,   # FIX
                    "date": extract_event_date(df, i),
                    "status": "SEED",
                    "status_reason": "Early structure forming"
                }
                break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP (FIXED START POINT)
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]
        close, high, low = float(candle["Close"]), float(candle["High"]), float(candle["Low"])

        action = three_candle_event_rules(latest_pattern, candle, close, high, low)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM" and latest_pattern["status"] in ["SEED", "PENDING"]:
            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Invalidated"
            break

    trade = build_three_candle_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }