# =========================================================
# PIERCING LINE / DARK CLOUD COVER MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("piercing_dcc")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_piercing_dcc(candle, prev_candle, f):

    logger.debug("[PIERCING/DCC] detect_piercing_dcc() called")

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
        logger.error(f"[PIERCING/DCC] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close, ph, pl, po, pc]):
        return {"detected": False}

    if high <= low or ph <= pl:
        return {"detected": False}

    # =========================================================
    # PREVIOUS CANDLE CONTEXT (MOTHER CANDLE)
    # =========================================================
    prev_range = ph - pl
    if prev_range == 0:
        return {"detected": False}

    prev_mid = (po + pc) / 2.0

    curr_range = high - low
    if curr_range == 0:
        return {"detected": False}

    # =========================================================
    # PIERCING LINE (BULLISH REVERSAL)
    # =========================================================
    piercing_line = (
        pc < po and  # previous bearish candle
        close > open_ and  # current bullish candle
        close > prev_mid and  # closes above midpoint of previous candle
        open_ < pc and  # opens below previous close
        close < po  # does not fully engulf (filters fakeouts)
    )

    # =========================================================
    # DARK CLOUD COVER (BEARISH REVERSAL)
    # =========================================================
    dark_cloud = (
        pc > po and  # previous bullish candle
        close < open_ and  # current bearish candle
        close < prev_mid and  # closes below midpoint of previous candle
        open_ > pc and  # opens above previous close
        close > po  # does not fully engulf
    )

    if piercing_line:
        return {
            "detected": True,
            "type": "Piercing Line",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if dark_cloud:
        return {
            "detected": True,
            "type": "Dark Cloud Cover",
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
def build_piercing_dcc_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

    # =========================================================
    # PIERCING LINE (LONG REVERSAL)
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
            "interpretation": "Piercing Line bullish reversal reclaiming prior bearish pressure."
        }

    # =========================================================
    # DARK CLOUD COVER (SHORT REVERSAL)
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
            "interpretation": "Dark Cloud Cover bearish reversal rejecting prior bullish expansion."
        }

    logger.warning(f"[PIERCING/DCC] Unknown direction in trade builder: {direction}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def piercing_dcc_event_rules(event, candle, close, high, low):

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
def analyze_piercing_dcc(df, event_store, f=float):

    logger.info("[PIERCING/DCC] analyze_piercing_dcc() called")

    latest_pattern = None

    # SEARCH BACKWARD (PINBAR STYLE)
    for i in range(len(df) - 1, 0, -1):

        candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]

        detected = detect_piercing_dcc(candle, prev_candle, f)

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
            f"[PIERCING/DCC] Found {detected['type']} date={event_date} index={i} direction={direction}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =========================================================
    # VALIDATION LOOP (IDENTICAL PINBAR ARCHITECTURE)
    # =========================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = piercing_dcc_event_rules(
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

            latest_pattern["status_reason"] = build_piercing_dcc_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_piercing_dcc_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }