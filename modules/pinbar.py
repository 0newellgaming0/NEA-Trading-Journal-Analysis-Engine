# =========================================================
# PINBAR MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("pinbar")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_pinbar(candle, f):

    logger.debug("[PINBAR] detect_pinbar() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:
        logger.error(f"[PINBAR] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close]):
        return {"detected": False}

    if high <= low:
        return {"detected": False}

    rng = high - low
    body = abs(close - open_)

    upper = high - max(open_, close)
    lower = min(open_, close) - low

    body_ratio = body / rng
    bull_ratio = lower / max(body, 1e-9)
    bear_ratio = upper / max(body, 1e-9)
    close_position = (close - low) / rng

    bullish_pinbar = (
        bull_ratio >= 2.5 and
        close_position >= 0.70 and
        lower > upper and
        body_ratio <= 0.35
    )

    bearish_pinbar = (
        bear_ratio >= 2.5 and
        close_position <= 0.30 and
        upper > lower and
        body_ratio <= 0.35
    )

    if bullish_pinbar:
        return {
            "detected": True,
            "type": "Pinbar",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if bearish_pinbar:
        return {
            "detected": True,
            "type": "Pinbar",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_pinbar_trade_state(event):

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
            "interpretation": "Bullish pinbar reversal scenario."
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
            "interpretation": "Bearish pinbar reversal scenario."
        }

    logger.warning(f"[PINBAR] Unknown direction in trade builder: {direction}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def pinbar_event_rules(event, candle, close, high, low):

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
# MAIN ANALYZER (CONTEXT REMOVED)
# =========================================================
def analyze_pinbar(df, event_store):

    logger.info("[PINBAR] analyze_pinbar() called")

    latest_pattern = None

    # SEARCH BACKWARD
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]
        detected = detect_pinbar(candle, float)

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
            "index": i,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[PINBAR] Latest pinbar found date={event_date} index={i} type={direction}"
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

        action = pinbar_event_rules(
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

            latest_pattern["status_reason"] = build_pinbar_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_pinbar_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }