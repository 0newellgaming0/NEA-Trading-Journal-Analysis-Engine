# =========================================================
# BIGALOW MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# STANDARDIZED EVENT ARCHITECTURE (DOJI PARITY FIXED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("bigalow")


# =========================================================
# BEST FRIEND DETECTOR
# =========================================================
def detect_best_friend(c1, c2, f):

    logger.debug("[BIGALOW] detect_best_friend() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1, h1, l1, c1c, o2, h2, l2, c2c]):
        return {"detected": False}

    body1 = abs(c1c - o1)
    range1 = max(h1 - l1, 1e-9)

    body2 = abs(c2c - o2)
    range2 = max(h2 - l2, 1e-9)

    bull1 = c1c > o1
    bear1 = c1c < o1

    strong1 = body1 >= range1 * 0.65
    small2 = body2 <= range2 * 0.35

    bullish = bull1 and strong1 and small2 and l2 >= (c1c - range1 * 0.25)
    bearish = bear1 and strong1 and small2 and h2 <= (c1c + range1 * 0.25)

    if bullish:
        return {
            "detected": True,
            "type": "Best Friend",
            "direction": "Bullish",
            "high": max(h1, h2),
            "low": min(l1, l2),
            "close": c2c
        }

    if bearish:
        return {
            "detected": True,
            "type": "Best Friend",
            "direction": "Bearish",
            "high": max(h1, h2),
            "low": min(l1, l2),
            "close": c2c
        }

    return {"detected": False}


# =========================================================
# LEFT / RIGHT COMBO
# =========================================================
def detect_left_right_combo(c1, c2, f):

    logger.debug("[BIGALOW] detect_left_right_combo() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1, h1, l1, c1c, o2, h2, l2, c2c]):
        return {"detected": False}

    body1 = abs(c1c - o1)
    body2 = abs(c2c - o2)

    range1 = max(h1 - l1, 1e-9)

    bull1 = c1c > o1
    bear1 = c1c < o1

    bull2 = c2c > o2
    bear2 = c2c < o2

    strong1 = body1 >= range1 * 0.60

    inside = (h2 <= h1 and l2 >= l1)
    smaller = body2 <= body1 * 0.60

    bullish = bull1 and bear2 and strong1 and inside and smaller
    bearish = bear1 and bull2 and strong1 and inside and smaller

    if bullish:
        return {
            "detected": True,
            "type": "Left Right Combo",
            "direction": "Bullish",
            "high": max(h1, h2),
            "low": min(l1, l2),
            "close": c2c
        }

    if bearish:
        return {
            "detected": True,
            "type": "Left Right Combo",
            "direction": "Bearish",
            "high": max(h1, h2),
            "low": min(l1, l2),
            "close": c2c
        }

    return {"detected": False}


# =========================================================
# KICKER DETECTOR
# =========================================================
def detect_kicker(c1, c2, f):

    logger.debug("[BIGALOW] detect_kicker() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1, h1, l1, c1c, o2, h2, l2, c2c]):
        return {"detected": False}

    body1 = abs(c1c - o1)
    body2 = abs(c2c - o2)

    range1 = max(h1 - l1, 1e-9)
    range2 = max(h2 - l2, 1e-9)

    bull1 = c1c > o1
    bear1 = c1c < o1

    bull2 = c2c > o2
    bear2 = c2c < o2

    strong1 = body1 >= range1 * 0.60
    strong2 = body2 >= range2 * 0.60

    gap_up = l2 > h1
    gap_down = h2 < l1

    bullish = bear1 and bull2 and gap_up and strong1 and strong2
    bearish = bull1 and bear2 and gap_down and strong1 and strong2

    if bullish:
        return {
            "detected": True,
            "type": "Kicker",
            "direction": "Bullish",
            "high": max(h1, h2),
            "low": min(l1, l2),
            "close": c2c
        }

    if bearish:
        return {
            "detected": True,
            "type": "Kicker",
            "direction": "Bearish",
            "high": max(h1, h2),
            "low": min(l1, l2),
            "close": c2c
        }

    return {"detected": False}


# =========================================================
# INTERPRETATION ENGINE (EVENT-OWNED)
# =========================================================
def interpret_bigalow(event):

    pattern = event.get("type")
    direction = event.get("direction")

    text = []

    if pattern == "Best Friend":
        text.append("Sequential candles show sustained directional conviction.")
        text.append("Follow-through participation suggests institutional interest.")

    elif pattern == "Left Right Combo":
        text.append("Impulse → pause → continuation structure detected.")
        text.append("Controlled consolidation suggests trend continuation.")

    elif pattern == "Kicker":
        text.append("Aggressive gap-driven sentiment shift detected.")
        text.append("Institutional repricing overwhelmed prior session positioning.")

    if direction == "Bullish":
        text.append("Bullish bias remains valid while pattern low holds.")

    elif direction == "Bearish":
        text.append("Bearish bias remains valid while pattern high holds.")

    return " | ".join(text)


# =========================================================
# TRADE BUILDER (EVENT-CONSUMING ONLY)
# =========================================================
def build_bigalow_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    pattern = event.get("type", "Bigalow")

    is_reversal = pattern == "Best Friend"

    if direction == "Bullish":

        return {
            "trade_type": "REVERSAL" if is_reversal else "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.10,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + (2 * rng),
            "failure": f"Close below {low}",
            "interpretation": event.get("interpretation")
        }

    if direction == "Bearish":

        return {
            "trade_type": "REVERSAL" if is_reversal else "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.10,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": f"Close above {high}",
            "interpretation": event.get("interpretation")
        }

    logger.warning(f"[BIGALOW] Unknown direction: {direction}")
    return {}


# =========================================================
# EVENT RULES (LIFECYCLE ENGINE)
# =========================================================
def bigalow_event_rules(event, candle, close, high, low):

    status = event.get("status")

    if status == "PENDING":

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

    if event.get("days_active", 0) > 10 and status == "PENDING":
        return "EXPIRE"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_kickers(df, event_store, f=float):

    logger.info("[BIGALOW] analyze_kickers() called")

    latest_pattern = None

    # -----------------------------------------------------
    # DETECTION PASS
    # -----------------------------------------------------
    for i in range(len(df) - 1, 0, -1):

        c1 = df.iloc[i - 1]
        c2 = df.iloc[i]

        detected = detect_best_friend(c1, c2, f)
        if not detected.get("detected"):
            detected = detect_left_right_combo(c1, c2, f)
        if not detected.get("detected"):
            detected = detect_kicker(c1, c2, f)

        if not detected.get("detected"):
            continue

        latest_pattern = {
            "id": 1,
            "detected": True,
            "event_type": "BIGALOW",
            "type": detected["type"],
            "direction": detected["direction"],
            "high": detected["high"],
            "low": detected["low"],
            "close": detected["close"],
            "index": i,
            "date": extract_event_date(df, i),
            "days_active": 0,
            "status": "PENDING",
            "status_reason": f'{detected["type"]} detected'
        }

        # ATTACH INTERPRETATION (DOJI PARITY FIX)
        latest_pattern["interpretation"] = interpret_bigalow(latest_pattern)

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # -----------------------------------------------------
    # VALIDATION LOOP
    # -----------------------------------------------------
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = bigalow_event_rules(latest_pattern, candle, close, high, low)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM":
            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern confirmed"

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_bigalow_trade_state(latest_pattern)["failure"]
            break

        elif action == "EXPIRE":
            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_bigalow_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }