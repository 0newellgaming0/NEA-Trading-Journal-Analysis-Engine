# =========================================================
# HARAMI FAMILY MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("harami")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_harami(candle, prev_candle, f):

    logger.debug("[HARAMI] detect_harami() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

        ph = f(prev_candle.get("High"))
        pl = f(prev_candle.get("Low"))
        po = f(prev_candle.get("Open"))
        pc = f(prev_candle.get("Close"))

    except Exception as e:
        logger.error(f"[HARAMI] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close, ph, pl, po, pc]):
        return {"detected": False}

    if high <= low or ph <= pl:
        return {"detected": False}

    # ---------------------------------------------------------
    # BODY CALCULATIONS
    # ---------------------------------------------------------
    prev_body_high = max(po, pc)
    prev_body_low = min(po, pc)

    curr_body_high = max(open_, close)
    curr_body_low = min(open_, close)

    inside_body = (
        curr_body_high < prev_body_high and
        curr_body_low > prev_body_low
    )

    if not inside_body:
        return {"detected": False}

    prev_bullish = pc > po
    prev_bearish = pc < po

    curr_bullish = close > open_
    curr_bearish = close < open_

    body = abs(close - open_)
    rng = max(high - low, 1e-9)
    body_ratio = body / rng

    # Harami Cross (doji-like compression)
    is_doji = body_ratio < 0.1

    # ---------------------------------------------------------
    # BULLISH HARAMI
    # ---------------------------------------------------------
    if prev_bearish and curr_bullish:
        return {
            "detected": True,
            "type": "Harami",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    # ---------------------------------------------------------
    # BEARISH HARAMI
    # ---------------------------------------------------------
    if prev_bullish and curr_bearish:
        return {
            "detected": True,
            "type": "Harami",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    # ---------------------------------------------------------
    # HARAMI CROSS (neutral compression)
    # ---------------------------------------------------------
    if is_doji:
        return {
            "detected": True,
            "type": "Harami Cross",
            "direction": "Neutral",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_harami_trade_state(event):

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
            "interpretation": "Bullish Harami reversal inside prior bearish expansion candle."
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
            "interpretation": "Bearish Harami reversal inside prior bullish expansion candle."
        }

    logger.warning(f"[HARAMI] Unknown direction in trade builder: {direction}")
    return {
        "trade_type": "NONE",
        "direction": "NEUTRAL",
        "entry": 0.0,
        "stop": 0.0,
        "invalidation": 0.0,
        "target1": 0.0,
        "target2": 0.0,
        "failure": "No directional edge",
        "interpretation": "Harami Cross / compression state"
    }


# =========================================================
# EVENT RULES
# =========================================================
def harami_event_rules(event, candle, close, high, low):

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
def analyze_harami(df, event_store, f=float):

    logger.info("[HARAMI] analyze_harami() called")

    latest_pattern = None

    # SEARCH BACKWARD (PINBAR STYLE)
    for i in range(len(df) - 1, 0, -1):

        candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]

        detected = detect_harami(candle, prev_candle, f)

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
            f"[HARAMI] Latest harami found date={event_date} index={i} type={direction}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP (PINBAR IDENTICAL STRUCTURE)
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = harami_event_rules(
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

            latest_pattern["status_reason"] = build_harami_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_harami_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }