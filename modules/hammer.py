# =========================================================
# HAMMER MODULE (STRUCTURE-BASED FAMILY DETECTOR)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("hammer")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_hammer(candle, f):

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in (high, low, open_, close)):
        return {"detected": False}

    if high <= low:
        return {"detected": False}

    rng = high - low
    body = abs(close - open_)

    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    body_pct = body / max(rng, 1e-9)

    # =========================================================
    # STRUCTURAL CONDITIONS
    # =========================================================

    is_lower_rejection = (
        lower_wick >= body * 2 and
        upper_wick <= rng * 0.25 and
        body_pct <= 0.35
    )

    is_upper_rejection = (
        upper_wick >= body * 2 and
        lower_wick <= rng * 0.25 and
        body_pct <= 0.35
    )

    lazy_lower = (
        lower_wick / max(body, 1e-9) >= 1.25 and
        upper_wick <= body and
        body_pct <= 0.55
    )

    lazy_upper = (
        upper_wick / max(body, 1e-9) >= 1.25 and
        lower_wick <= body and
        body_pct <= 0.55
    )

    # =========================================================
    # PATTERN CLASSIFICATION (FAMILY → TYPE)
    # =========================================================

    if is_lower_rejection or lazy_lower:

        direction = "Bullish" if close >= open_ else "Bearish"

        pattern_type = (
            "Hammer" if direction == "Bullish"
            else "Hanging Man"
        )

        classification = "INSTITUTIONAL" if is_lower_rejection else "LAZY"

        return {
            "detected": True,
            "type": pattern_type,
            "direction": direction,
            "classification": classification,
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if is_upper_rejection or lazy_upper:

        direction = "Bearish" if close <= open_ else "Bullish"

        pattern_type = (
            "Shooting Star" if direction == "Bearish"
            else "Inverted Hammer"
        )

        classification = "INSTITUTIONAL" if is_upper_rejection else "LAZY"

        return {
            "detected": True,
            "type": pattern_type,
            "direction": direction,
            "classification": classification,
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER
# =========================================================
def build_hammer_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

    if direction == "Bullish":

        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",
            "entry": high,
            "stop": low - (rng * 0.1),
            "invalidation": low,
            "target1": high + rng,
            "target2": high + (2 * rng),
            "failure": f"Close below {low}",
            "interpretation": f"{event['type']} bullish rejection setup."
        }

    elif direction == "Bearish":

        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",
            "entry": low,
            "stop": high + (rng * 0.1),
            "invalidation": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": f"Close above {high}",
            "interpretation": f"{event['type']} bearish rejection setup."
        }

    logger.warning(f"[HAMMER] Unknown direction: {direction}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def hammer_event_rules(event, candle, close, high, low):

    if event.get("status") == "PENDING":

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

    elif event.get("status") == "CONFIRMED":

        if event["direction"] == "Bullish":
            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":
            if close > event["high"]:
                return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_hammer(df, event_store):

    logger.info("[HAMMER] analyze_hammer() called")

    latest_pattern = None

    # SEARCH BACKWARD
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]
        detected = detect_hammer(candle, float)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],
            "trade_type": "REVERSAL",
            "classification": detected.get("classification", ""),
            "high": detected["high"],
            "low": detected["low"],
            "index": i,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = hammer_event_rules(
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
            latest_pattern["status_reason"] = "Entry trigger validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_hammer_trade_state(
                latest_pattern
            )["failure"]

            break

    trade = build_hammer_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }