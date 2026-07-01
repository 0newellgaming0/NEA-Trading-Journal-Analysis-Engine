# =========================================================
# CANDLE OVER CANDLE MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("candle_over_candle")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_candle_over_candle(candle, prev_candle, f):

    logger.debug("[CANDLE OVER CANDLE] detect_candle_over_candle() called")

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
        logger.error(f"[CANDLE OVER CANDLE] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close, ph, pl, po, pc]):
        return {"detected": False}

    if high <= low or ph <= pl:
        return {"detected": False}

    # ---------------------------------------------------------
    # OUTSIDE BAR (CANDLE OVER CANDLE RANGE EXPANSION)
    # ---------------------------------------------------------
    full_over = (high > ph) and (low < pl)

    if not full_over:
        return {"detected": False}

    # ---------------------------------------------------------
    # BODY CONTEXT
    # ---------------------------------------------------------
    prev_body_high = max(po, pc)
    prev_body_low = min(po, pc)

    curr_body_high = max(open_, close)
    curr_body_low = min(open_, close)

    body_over = (curr_body_high > prev_body_high) and (curr_body_low < prev_body_low)

    # Directional pressure
    prev_bullish = pc > po
    prev_bearish = pc < po

    curr_bullish = close > open_
    curr_bearish = close < open_

    body = abs(close - open_)
    rng = max(high - low, 1e-9)
    body_ratio = body / rng

    is_strong_expansion = body_ratio > 0.6

    # ---------------------------------------------------------
    # BULLISH OVER BAR
    # ---------------------------------------------------------
    if curr_bullish and (prev_bearish or body_over):

        return {
            "detected": True,
            "type": "Candle Over Candle",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "strength": "EXPANSION" if is_strong_expansion else "MODERATE"
        }

    # ---------------------------------------------------------
    # BEARISH OVER BAR
    # ---------------------------------------------------------
    if curr_bearish and (prev_bullish or body_over):

        return {
            "detected": True,
            "type": "Candle Over Candle",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "strength": "EXPANSION" if is_strong_expansion else "MODERATE"
        }

    # ---------------------------------------------------------
    # NEUTRAL OUTSIDE BAR (FULL RANGE EXPANSION / EQUILIBRIUM BREAK)
    # ---------------------------------------------------------
    return {
        "detected": True,
        "type": "Candle Over Candle",
        "direction": "Neutral",
        "high": high,
        "low": low,
        "open": open_,
        "close": close,
        "strength": "RANGE_EXPANSION"
    }


# =========================================================
# TRADE BUILDER (BIGALOW PROGRESSIVE)
# =========================================================
def build_candle_over_candle_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction", "Neutral")
    status = event.get("status", "PENDING")

    # ==================================================
    # NEUTRAL EXPANSION (OUTSIDE BAR COMPRESSION BREAK)
    # ==================================================
    if direction == "Neutral" and status == "PENDING":

        return {

            "trade_type": "COMPRESSION_BREAK",
            "direction": "BOTH",
            "active": True,

            "entry_long": high,
            "entry_short": low,

            "stop_long": low,
            "stop_short": high,

            "target1_long": high + rng,
            "target2_long": high + 2 * rng,

            "target1_short": low - rng,
            "target2_short": low - 2 * rng,

            "failure_long": f"Close below {low}",
            "failure_short": f"Close above {high}",

            "interpretation": (
                "Candle Over Candle (Outside Bar) represents volatility expansion "
                "where price fully engulfs the prior candle range. This signals "
                "liquidity sweep conditions and institutional participation. "
                "Direction is not confirmed until price breaks and closes beyond "
                "the expansion extremes."
            ),

            "state": "EXPANSION_ACTIVE"
        }

    # ==================================================
    # BULLISH EXPANSION
    # ==================================================
    if direction == "Bullish":

        return {

            "trade_type": "REVERSAL",
            "direction": "LONG",
            "active": status != "FAILED",

            "entry": high,
            "stop": low - rng * 0.10,
            "invalidation": low,

            "target1": high + rng,
            "target2": high + 2 * rng,

            "failure": f"Close below {low}",

            "interpretation": (
                "Bullish Candle Over Candle signals aggressive buyer dominance "
                "through full range expansion above prior structure. This reflects "
                "liquidity absorption on the downside and strong institutional "
                "accumulation behavior. Continuation is expected if price holds "
                "above the expansion low."
            ),

            "state": "BULLISH_ACTIVE"
        }

    # ==================================================
    # BEARISH EXPANSION
    # ==================================================
    if direction == "Bearish":

        return {

            "trade_type": "REVERSAL",
            "direction": "SHORT",
            "active": status != "FAILED",

            "entry": low,
            "stop": high + rng * 0.10,
            "invalidation": high,

            "target1": low - rng,
            "target2": low - 2 * rng,

            "failure": f"Close above {high}",

            "interpretation": (
                "Bearish Candle Over Candle signals aggressive seller dominance "
                "through full range breakdown below prior structure. This reflects "
                "liquidity rejection and institutional distribution behavior. "
                "Continuation is expected if price holds below the expansion high."
            ),

            "state": "BEARISH_ACTIVE"
        }

    return {

        "trade_type": "NONE",
        "direction": "NEUTRAL",
        "active": False,

        "entry": 0.0,
        "stop": 0.0,
        "invalidation": 0.0,

        "target1": 0.0,
        "target2": 0.0,

        "failure": "",

        "interpretation": "No active Candle Over Candle trade.",

        "state": "INVALID"
    }


# =========================================================
# EVENT RULES
# =========================================================
def candle_over_candle_event_rules(event, candle, close, high, low):

    status = event["status"]

    # ---------------------------------------------
    # Pending Expansion
    # ---------------------------------------------
    if status == "PENDING":

        if event["direction"] == "Neutral":

            if close > event["high"]:
                event["direction"] = "Bullish"
                return "CONFIRM"

            if close < event["low"]:
                event["direction"] = "Bearish"
                return "CONFIRM"

            return None

        elif event["direction"] == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # ---------------------------------------------
    # Confirmed State
    # ---------------------------------------------
    elif status == "CONFIRMED":

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
def analyze_candle_over_candle(df, event_store, f=float):

    logger.info("[CANDLE OVER CANDLE] analyze_candle_over_candle() called")

    latest_pattern = None

    # ==================================================
    # DETECTION PASS
    # ==================================================
    for i in range(len(df) - 1, 0, -1):

        candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]

        detected = detect_candle_over_candle(candle, prev_candle, f)

        if not detected.get("detected"):
            continue

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],
            "strength": detected.get("strength", "UNKNOWN"),

            "trade_type": (
                "COMPRESSION_BREAK"
                if detected["direction"] == "Neutral"
                else "REVERSAL"
            ),

            "high": detected["high"],
            "low": detected["low"],
            "close": detected["close"],

            "index": i,
            "date": extract_event_date(df, i),

            "status": "PENDING",
            "days_active": 0,
            "status_reason": "Awaiting expansion confirmation"
        }

        logger.info(
            f"[CANDLE OVER CANDLE] Pattern found "
            f"date={latest_pattern['date']} "
            f"type={latest_pattern['type']} "
            f"direction={latest_pattern['direction']}"
        )

        break

    if latest_pattern is None:
        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # ==================================================
    # INITIAL TRADE
    # ==================================================
    trade = build_candle_over_candle_trade_state(latest_pattern)

    # ==================================================
    # PROGRESSIVE STATE MACHINE
    # ==================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        latest_pattern["days_active"] = i - latest_pattern["index"]

        action = candle_over_candle_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["trade_type"] = "REVERSAL"

            if latest_pattern["direction"] == "Bullish":
                latest_pattern["status_reason"] = "Bullish expansion confirmed."

            elif latest_pattern["direction"] == "Bearish":
                latest_pattern["status_reason"] = "Bearish expansion confirmed."

            trade = build_candle_over_candle_trade_state(latest_pattern)

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Expansion failed."

            trade = build_candle_over_candle_trade_state(latest_pattern)
            break

    trade = build_candle_over_candle_trade_state(latest_pattern)

    # ==================================================
    # REGIME ENGINE
    # ==================================================
    if latest_pattern["status"] == "CONFIRMED":

        if latest_pattern["direction"] == "Bullish":
            regime = "COC_BULL_EXPANSION"

        elif latest_pattern["direction"] == "Bearish":
            regime = "COC_BEAR_EXPANSION"

        else:
            regime = "COC_NEUTRAL_EXPANSION"

    elif latest_pattern["status"] == "FAILED":
        regime = "FAILED"

    else:
        regime = "COC_COMPRESSION"

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": regime
    }