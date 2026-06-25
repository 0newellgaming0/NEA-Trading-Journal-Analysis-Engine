# =========================================================
# DOJI MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("doji")


# =========================================================
# DETECTOR (PURE - PINBAR ALIGNED)
# =========================================================
def detect_doji(candle, f):

    logger.debug("[DOJI] detect_doji() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:
        logger.error(f"[DOJI] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close]):
        return {"detected": False}

    if high <= low:
        return {"detected": False}

    rng = high - low
    body = abs(close - open_)
    upper = high - max(open_, close)
    lower = min(open_, close) - low

    body_ratio = body / max(rng, 1e-9)

    # =========================================================
    # FOUR PRICE DOJI
    # =========================================================
    if high == low:
        return {
            "detected": True,
            "type": "FOUR_PRICE_DOJI",
            "direction": "NEUTRAL",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    # =========================================================
    # DOJI FAMILY
    # =========================================================
    if body_ratio < 0.05:

        if upper < rng * 0.1 and lower > rng * 0.6:
            return {
                "detected": True,
                "type": "DRAGONFLY_DOJI",
                "direction": "Bullish",
                "high": high,
                "low": low,
                "open": open_,
                "close": close
            }

        if lower < rng * 0.1 and upper > rng * 0.6:
            return {
                "detected": True,
                "type": "GRAVESTONE_DOJI",
                "direction": "Bearish",
                "high": high,
                "low": low,
                "open": open_,
                "close": close
            }

        if upper > rng * 0.3 and lower > rng * 0.3:
            return {
                "detected": True,
                "type": "LONG_LEGGED_DOJI",
                "direction": "Neutral",
                "high": high,
                "low": low,
                "open": open_,
                "close": close
            }

        return {
            "detected": True,
            "type": "DOJI",
            "direction": "Neutral",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    # =========================================================
    # SPINNING TOP
    # =========================================================
    if 0.05 <= body_ratio <= 0.25:
        if upper > rng * 0.2 and lower > rng * 0.2:
            return {
                "detected": True,
                "type": "SPINNING_TOP",
                "direction": "Neutral",
                "high": high,
                "low": low,
                "open": open_,
                "close": close
            }

    # =========================================================
    # HIGH WAVE CANDLE
    # =========================================================
    if body_ratio <= 0.3:
        if upper > rng * 0.35 and lower > rng * 0.35:
            return {
                "detected": True,
                "type": "HIGH_WAVE_CANDLE",
                "direction": "Neutral",
                "high": high,
                "low": low,
                "open": open_,
                "close": close
            }

    # =========================================================
    # RICKSHAW MAN
    # =========================================================
    if body_ratio < 0.05:
        if abs(upper - lower) <= rng * 0.1 and upper > rng * 0.4 and lower > rng * 0.4:
            return {
                "detected": True,
                "type": "RICKSHAW_MAN",
                "direction": "Neutral",
                "high": high,
                "low": low,
                "open": open_,
                "close": close
            }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PINBAR MIRRORED STRUCTURE)
# =========================================================
def build_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction", "Neutral")

    if direction in ["Bullish", "BULLISH"]:
        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + 2 * rng,
            "failure": f"Close below {low}",
            "interpretation": f"{event.get('type')} bullish indecision reversal setup"
        }

    if direction in ["Bearish", "BEARISH"]:
        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - 2 * rng,
            "failure": f"Close above {high}",
            "interpretation": f"{event.get('type')} bearish indecision reversal setup"
        }

    return {}


# =========================================================
# EVENT RULES (PINBAR CONSISTENT)
# =========================================================
def event_rules(event, candle, close, high, low):

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
# MAIN ANALYZER (PINBAR STRUCTURE MIRROR)
# =========================================================
def analyze_doji(df, event_store):

    logger.info("[DOJI] analyze_doji() called")

    latest_pattern = None

    # SEARCH BACKWARD
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]
        detected = detect_doji(candle, float)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],
            "trade_type": "REVERSAL",
            "high": detected["high"],
            "low": detected["low"],
            "index": i,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(f"[DOJI] Pattern found {detected['type']} at index={i}")
        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = event_rules(latest_pattern, candle, close, high, low)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Entry trigger validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern invalidated"
            break

    trade = build_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }