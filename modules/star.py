import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("star_patterns")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_star_pattern(c1, c2, c3, f):

    logger.debug("[STAR] detect_star_pattern() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])

    except Exception as e:
        logger.error(f"[STAR] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1,h1,l1,c1c,o2,h2,l2,c2c,o3,h3,l3,c3c]):
        return {"detected": False}

    # =========================================================
    # CONTEXT FLAGS
    # =========================================================
    bull1 = c1c > o1
    bear1 = c1c < o1

    bull3 = c3c > o3
    bear3 = c3c < o3

    body2 = abs(c2c - o2)
    range2 = max(h2 - l2, 1e-9)

    small_body = body2 <= range2 * 0.3

    mid1 = (h1 + l1) / 2
    mid3 = (h3 + l3) / 2

    # =========================================================
    # MORNING STAR (BULLISH REVERSAL)
    # Structure:
    # 1 bearish candle
    # 2 small indecision (star)
    # 3 strong bullish close
    # =========================================================
    morning_star = (
        bear1 and
        small_body and
        bull3 and
        c3c > mid1 and
        c3c > c1c
    )

    # =========================================================
    # EVENING STAR (BEARISH REVERSAL)
    # Structure:
    # 1 bullish candle
    # 2 small indecision (star)
    # 3 strong bearish close
    # =========================================================
    evening_star = (
        bull1 and
        small_body and
        bear3 and
        c3c < mid1 and
        c3c < c1c
    )

    if morning_star:
        return {
            "detected": True,
            "type": "Morning Star",
            "direction": "Bullish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    if evening_star:
        return {
            "detected": True,
            "type": "Evening Star",
            "direction": "Bearish",
            "high": h3,
            "low": l3,
            "close": c3c
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER
# =========================================================
def build_star_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    pattern = event.get("type")

    if direction == "Bullish":

        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + rng * 2,
            "failure": f"Close below {low}",
            "interpretation": "Morning Star bullish reversal expansion structure."
        }

    if direction == "Bearish":

        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - rng * 2,
            "failure": f"Close above {high}",
            "interpretation": "Evening Star bearish reversal expansion structure."
        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def star_event_rules(event, candle, close, high, low):

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

    return None


# =========================================================
# MAIN ANALYZER (PINBAR-MIRRORED BACKWARD ENGINE)
# =========================================================
def analyze_star_patterns(df, event_store, f=float):

    logger.info("[STAR] analyze_star_patterns() called")

    latest_pattern = None

    # BACKWARD SCAN (3 CANDLE WINDOW)
    for i in range(len(df) - 1, 1, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        detected = detect_star_pattern(c1, c2, c3, f)

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
            "index": i - 2,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[STAR] Found {detected['type']} at index={i-2}"
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

        action = star_event_rules(
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
            latest_pattern["status_reason"] = "Star pattern confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_star_trade_state(latest_pattern)["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_star_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }