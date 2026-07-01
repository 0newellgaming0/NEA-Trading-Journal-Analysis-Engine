# =========================================================
# DOJI MODULE (BIGALOW PROGRESSIVE VERSION)
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("doji")


# =========================================================
# DETECTOR (UNCHANGED CORE LOGIC)
# =========================================================
def detect_doji(candle, f):

    logger.debug("[DOJI] detect_doji() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))
    except Exception as e:
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

    # =====================================================
    # DOJI FAMILY
    # =====================================================
    if body_ratio < 0.05:

        if upper < rng * 0.1 and lower > rng * 0.6:
            return {
                "detected": True,
                "type": "DRAGONFLY_DOJI",
                "direction": "Bullish",
                "high": high,
                "low": low,
                "close": close
            }

        if lower < rng * 0.1 and upper > rng * 0.6:
            return {
                "detected": True,
                "type": "GRAVESTONE_DOJI",
                "direction": "Bearish",
                "high": high,
                "low": low,
                "close": close
            }

        return {
            "detected": True,
            "type": "DOJI",
            "direction": "Neutral",
            "high": high,
            "low": low,
            "close": close
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (UNCHANGED STRUCTURE)
# =========================================================
def build_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction", "Neutral")
    status = event.get("status", "PENDING")

    trade = {
        "trade_type": "REVERSAL",
        "direction": direction,
        "active": status != "FAILED",

        # ==================================================
        # UNIFIED FIELDS (MATCH PINBAR + RENDERER)
        # ==================================================
        "entry": high if direction == "Bullish" else low,
        "stop": low if direction == "Bullish" else high,

        "invalidation": low if direction == "Bullish" else high,

        "target1": (high + rng) if direction == "Bullish" else (low - rng),
        "target2": (high + 2 * rng) if direction == "Bullish" else (low - 2 * rng),

        "failure": f"Close below {low}" if direction == "Bullish"
                   else f"Close above {high}",

        "interpretation": "Doji expansion reversal setup"
    }

    # ==================================================
    # STATE DISPLAY FIX
    # ==================================================
    if status == "PENDING":
        trade["state"] = "WAITING_BIAS"
    elif status == "CONFIRMED":
        trade["state"] = "ACTIVE"
    elif status == "FAILED":
        trade["state"] = "INVALIDATED"

    return trade


# =========================================================
# BIGALOW EVENT RULES (PROGRESSIVE LIFECYCLE)
# =========================================================
def event_rules(event, candle, close, high, low):

    status = event.get("status")

    # ==================================================
    # STEP 1: DETERMINE BIAS (ONLY ONCE)
    # ==================================================
    if status == "PENDING":

        if close > event["high"]:
            event["direction"] = "Bullish"
            return "CONFIRM_BIAS"

        if close < event["low"]:
            event["direction"] = "Bearish"
            return "CONFIRM_BIAS"

        return None

    # ==================================================
    # STEP 2: AFTER BIAS IS SET → ONLY FAILURE CHECK
    # ==================================================
    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":
            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":
            if close > event["high"]:
                return "FAIL"

    return None
    
# =========================================================
# MAIN ANALYZER (PROGRESSIVE BIGALOW FLOW)
# =========================================================
def analyze_doji(df, event_store):

    logger.info("[DOJI] analyze_doji() called")

    latest_pattern = None

    # ==================================================
    # DETECTION PASS
    # ==================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]
        detected = detect_doji(candle, float)

        if not detected.get("detected"):
            continue

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],

            # ALWAYS NEUTRAL ON CREATION
            "direction": "Neutral",

            "high": detected["high"],
            "low": detected["low"],
            "close": detected["close"],

            "index": i,
            "date": extract_event_date(df, i),

            "status": "PENDING",
            "days_active": 0,
            "status_reason": "Doji detected → awaiting bias candle"
        }

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # ==================================================
    # TRADE ALWAYS EXISTS
    # ==================================================
    trade = build_trade_state(latest_pattern)

    # ==================================================
    # STATE MACHINE
    # ==================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = event_rules(latest_pattern, candle, close, high, low)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM_BIAS":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

    # ==================================================
    # FINAL TRADE UPDATE
    # ==================================================
    trade = build_trade_state(latest_pattern)

    # ==================================================
    # REGIME (CLEAN + PINBAR PARITY STYLE)
    # ==================================================
    if latest_pattern["status"] == "CONFIRMED":

        if latest_pattern["direction"] == "Bullish":
            regime = "DOJI_BULL_EXPANSION"
        else:
            regime = "DOJI_BEAR_EXPANSION"

    elif latest_pattern["status"] == "FAILED":
        regime = "FAILED"

    else:
        regime = "DOJI_COMPRESSION"

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": regime
    }