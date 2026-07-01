# =========================================================
# RISING / FALLING THREE METHODS MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("three_methods")


# =========================================================
# FULL PATTERN DETECTOR (CONFIRMATION)
# =========================================================
# =========================================================
# FULL PATTERN DETECTOR (CONFIRMATION) - FIXED
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
        return {"detected": False, "error": str(e)}

    # =====================================================
    # IMPULSE CANDLE QUALITY (FIRST CANDLE)
    # =====================================================
    body1 = abs(c1c - o1)
    range1 = max(h1 - l1, 1e-9)

    strong_bull = c1c > o1 and body1 > range1 * 0.6
    strong_bear = c1c < o1 and body1 > range1 * 0.6

    # =====================================================
    # MIDDLE CONSOLIDATION VALIDATION
    # =====================================================
    mid_candles = [(h2, l2, o2, c2c), (h3, l3, o3, c3c), (h4, l4, o4, c4c)]

    mid_high = max(h2, h3, h4)
    mid_low = min(l2, l3, l4)

    # Allow wick violations but enforce structure compression
    compression_inside = (
        mid_high <= h1 * 1.01 and
        mid_low >= l1 * 0.99
    )

    # Require reduced volatility vs impulse candle
    avg_mid_range = sum([h2-l2, h3-l3, h4-l4]) / 3
    compression_strength = avg_mid_range < (range1 * 0.6)

    # =====================================================
    # BREAKOUT CANDLE VALIDATION
    # =====================================================
    body5 = abs(c5c - o5)
    range5 = max(h5 - l5, 1e-9)

    bullish_breakout = (
        c5c > h1 and
        c5c > o5 and
        body5 > range5 * 0.5
    )

    bearish_breakdown = (
        c5c < l1 and
        c5c < o5 and
        body5 > range5 * 0.5
    )

    # =====================================================
    # RISING THREE METHODS
    # =====================================================
    rising = (
        strong_bull and
        compression_inside and
        compression_strength and
        bullish_breakout
    )

    # =====================================================
    # FALLING THREE METHODS
    # =====================================================
    falling = (
        strong_bear and
        compression_inside and
        compression_strength and
        bearish_breakdown
    )

    # =====================================================
    # RESULT
    # =====================================================
    if rising:
        return {
            "detected": True,
            "type": "Rising Three Methods",
            "direction": "Bullish",
            "high": h5,
            "low": l5
        }

    if falling:
        return {
            "detected": True,
            "type": "Falling Three Methods",
            "direction": "Bearish",
            "high": h5,
            "low": l5
        }

    return {"detected": False}

# =========================================================
# REQUIRED SEED DETECTOR
# =========================================================
def detect_three_methods_seed(c1, c2, c3, f):

    logger.debug("[3-METHODS] seed detection called")

    try:

        o1,h1,l1,c1c = f(c1["Open"]),f(c1["High"]),f(c1["Low"]),f(c1["Close"])
        o2,h2,l2,c2c = f(c2["Open"]),f(c2["High"]),f(c2["Low"]),f(c2["Close"])
        o3,h3,l3,c3c = f(c3["Open"]),f(c3["High"]),f(c3["Low"]),f(c3["Close"])

    except Exception:
        return {"detected": False}

    rising_seed = (
        c1c > o1 and
        max(h2, h3) <= h1 and
        min(l2, l3) >= l1 and
        c2c < c1c and
        c3c < c2c
    )

    falling_seed = (
        c1c < o1 and
        max(h2, h3) <= h1 and
        min(l2, l3) >= l1 and
        c2c > c1c and
        c3c > c2c
    )

    if rising_seed:
        return {
            "detected": True,
            "type": "Rising Three Methods (Seed)",
            "direction": "Bullish",
            "high": h1,
            "low": l1,
            "stage": "SEED"
        }

    if falling_seed:
        return {
            "detected": True,
            "type": "Falling Three Methods (Seed)",
            "direction": "Bearish",
            "high": h1,
            "low": l1,
            "stage": "SEED"
        }

    return {"detected": False}

def interpret_three_methods(event):

    direction = event.get("direction")
    ptype = event.get("type", "")

    interpretations = []

    if "Rising" in ptype:

        interpretations.append(
            "Bullish continuation structure with compression phase followed by breakout expansion."
        )

        interpretations.append(
            "Institutional accumulation behavior suggested by controlled retracement candles."
        )

    elif "Falling" in ptype:

        interpretations.append(
            "Bearish continuation structure with controlled distribution phase before breakdown."
        )

        interpretations.append(
            "Institutional distribution behavior suggested by failed bullish recovery attempts."
        )

    else:

        interpretations.append(
            "Neutral continuation structure forming with consolidation-based compression."
        )

    status = event.get("status")

    if status == "SEED":
        interpretations.append(
            "Early structure detected; breakout confirmation not yet established."
        )

    elif status == "CONFIRMED":
        interpretations.append(
            "Breakout confirmed with directional acceptance by market participants."
        )

    elif status == "FAILED":
        interpretations.append(
            "Structure invalidated due to rejection of continuation direction."
        )

    return " | ".join(interpretations)
    
# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_three_methods_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

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
            "interpretation": interpret_three_methods(event)
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
            "interpretation": interpret_three_methods(event)
        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def three_methods_event_rules(event, candle, close, high, low):

    status = event.get("status")

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

        if event["direction"] == "Bullish":
            if close < event["low"]:
                return "FAIL"

        if event["direction"] == "Bearish":
            if close > event["high"]:
                return "FAIL"

    return None

# =========================================================
# MAIN ANALYZER
# REQUIRED SEED ARCHITECTURE
# =========================================================
def analyze_three_methods(df, event_store, f=float):

    logger.info("[3-METHODS] analyze_three_methods() called")

    latest_pattern = None

    # =====================================================
    # PASS 1 - FULL PATTERN
    # =====================================================
    for i in range(len(df) - 1, 3, -1):

        c1 = df.iloc[i - 4]
        c2 = df.iloc[i - 3]
        c3 = df.iloc[i - 2]
        c4 = df.iloc[i - 1]
        c5 = df.iloc[i]

        detected = detect_three_methods(c1, c2, c3, c4, c5, f)

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "index": i - 4,
                "last_index": i,
                "date": extract_event_date(df, i),
                "status": "PENDING",
                "status_reason": "Full Three Methods detected"
            }

            break

    # =====================================================
    # PASS 2 - SEED
    # =====================================================
    if latest_pattern is None:

        for i in range(len(df) - 1, 2, -1):

            c1 = df.iloc[i - 3]
            c2 = df.iloc[i - 2]
            c3 = df.iloc[i - 1]
            c4 = df.iloc[i]

            seed = detect_three_methods_seed(c1, c2, c3, f)

            if seed.get("detected"):

                latest_pattern = {
                    "id": 1,
                    "detected": True,
                    "type": seed["type"],
                    "direction": seed["direction"],
                    "high": seed["high"],
                    "low": seed["low"],
                    "index": i - 3,
                    "last_index": i,
                    "date": extract_event_date(df, i),
                    "status": "SEED",
                    "status_reason": "Three Methods structure forming"
                }

                break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =====================================================
    # VALIDATION LOOP
    # =====================================================
    for i in range(latest_pattern["last_index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        high = f(candle["High"])
        low = f(candle["Low"])

        action = three_methods_event_rules(latest_pattern, candle, close, high, low)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Three Methods confirmed"
            break

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Three Methods failed"
            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Expired"
            break

    trade = build_three_methods_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }