# =========================================================
# TWEEZER BOTTOM / TOP MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("tweezer")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_tweezer(candle, prev_candle, f):

    logger.debug("[TWEEZER] detect_tweezer() called")

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
        logger.error(f"[TWEEZER] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close, ph, pl, po, pc]):
        return {"detected": False}

    if high <= low or ph <= pl:
        return {"detected": False}

    # =========================================================
    # TOLERANCE FOR EQUAL HIGHS / LOWS (TWEEZER STRUCTURE)
    # =========================================================
    tolerance = (high - low) * 0.001

    same_lows = abs(low - pl) <= tolerance
    same_highs = abs(high - ph) <= tolerance

    curr_bullish = close > open_
    curr_bearish = close < open_
    prev_bullish = pc > po
    prev_bearish = pc < po

    # =========================================================
    # TWEEZER BOTTOM (BULLISH REVERSAL)
    # Two candles forming equal lows after selling pressure
    # =========================================================
    tweezer_bottom = (
        same_lows and
        prev_bearish and
        curr_bullish
    )

    # =========================================================
    # TWEEZER TOP (BEARISH REVERSAL)
    # Two candles forming equal highs after buying pressure
    # =========================================================
    tweezer_top = (
        same_highs and
        prev_bullish and
        curr_bearish
    )

    if tweezer_bottom:
        return {
            "detected": True,
            "type": "Tweezer Bottom",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if tweezer_top:
        return {
            "detected": True,
            "type": "Tweezer Top",
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
def build_tweezer_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

    # =========================================================
    # TWEEZER BOTTOM (LONG REVERSAL)
    # =========================================================
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
            "interpretation": "Tweezer Bottom liquidity rejection and demand absorption reversal."
        }

    # =========================================================
    # TWEEZER TOP (SHORT REVERSAL)
    # =========================================================
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
            "interpretation": "Tweezer Top liquidity rejection and supply absorption reversal."
        }

    logger.warning(f"[TWEEZER] Unknown direction in trade builder: {direction}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def tweezer_event_rules(event, candle, close, high, low):

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
def analyze_tweezer(df, event_store, f=float):

    logger.info("[TWEEZER] analyze_tweezer() called")

    latest_pattern = None

    # SEARCH BACKWARD (PINBAR STYLE)
    for i in range(len(df) - 1, 0, -1):

        candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]

        detected = detect_tweezer(candle, prev_candle, f)

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
            f"[TWEEZER] Found {detected['type']} date={event_date} index={i} direction={direction}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =========================================================
    # VALIDATION LOOP (PINBAR-STYLE LIFECYCLE)
    # =========================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = tweezer_event_rules(
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
            latest_pattern["status_reason"] = "Reversal confirmation validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = build_tweezer_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_tweezer_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }