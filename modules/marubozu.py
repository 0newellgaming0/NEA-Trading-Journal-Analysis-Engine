# =========================================================
# MARUBOZU FAMILY MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("marubozu")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_marubozu(candle, f):

    logger.debug("[MARUBOZU] detect_marubozu() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:
        logger.error(f"[MARUBOZU] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close]):
        return {"detected": False}

    if high <= low:
        return {"detected": False}

    rng = high - low
    body = abs(close - open_)

    if rng == 0:
        return {"detected": False}

    body_ratio = body / rng

    # wick calculations
    upper_wick = high - max(open_, close)
    lower_wick = min(open_, close) - low

    # Marubozu conditions (strict institutional definition relaxed slightly for liquidity noise)
    is_full_bull = (
        close > open_ and
        body_ratio >= 0.85 and
        upper_wick <= rng * 0.05 and
        lower_wick <= rng * 0.05
    )

    is_full_bear = (
        close < open_ and
        body_ratio >= 0.85 and
        upper_wick <= rng * 0.05 and
        lower_wick <= rng * 0.05
    )

    if is_full_bull:
        return {
            "detected": True,
            "type": "Marubozu",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if is_full_bear:
        return {
            "detected": True,
            "type": "Marubozu",
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
def build_marubozu_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

    # ---------------------------------------------------------
    # BULLISH MARUBOZU
    # ---------------------------------------------------------
    if direction == "Bullish":
        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng * 1.2,
            "target2": high + rng * 2.5,
            "failure": f"Close below {low}",
            "interpretation": "Bullish Marubozu strong momentum expansion candle."
        }

    # ---------------------------------------------------------
    # BEARISH MARUBOZU
    # ---------------------------------------------------------
    if direction == "Bearish":
        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng * 1.2,
            "target2": low - rng * 2.5,
            "failure": f"Close above {high}",
            "interpretation": "Bearish Marubozu strong momentum expansion candle."
        }

    logger.warning(f"[MARUBOZU] Unknown direction in trade builder: {direction}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def marubozu_event_rules(event, candle, close, high, low):

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
# MAIN ANALYZER (CONTEXT REMOVED - PINBAR MIRROR)
# =========================================================
def analyze_marubozu(df, event_store, f=float):

    logger.info("[MARUBOZU] analyze_marubozu() called")

    latest_pattern = None

    # SEARCH BACKWARD (PINBAR-STYLE STRUCTURE)
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]
        detected = detect_marubozu(candle, f)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)
        direction = detected["direction"]

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": direction,
            "trade_type": "CONTINUATION",
            "high": detected["high"],
            "low": detected["low"],
            "index": i,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[MARUBOZU] Latest marubozu found date={event_date} index={i} type={direction}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP (IDENTICAL TO PINBAR)
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = marubozu_event_rules(
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
            latest_pattern["status_reason"] = "Momentum continuation validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = build_marubozu_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_marubozu_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }