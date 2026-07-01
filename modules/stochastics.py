# =========================================================
# STOCHASTICS MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# MIRRORS PINBAR MODULE STRUCTURE
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("stochastics")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# STOCHASTIC CALCULATION
# =========================================================
def get_stoch(df, i, k_period=14, d_period=3):

    try:
        low_min = df["Low"].iloc[max(0, i - k_period + 1): i + 1].min()
        high_max = df["High"].iloc[max(0, i - k_period + 1): i + 1].max()
        close = f(df["Close"].iloc[i])

        if high_max == low_min:
            return 50.0

        k = 100 * (close - low_min) / (high_max - low_min)
        return k

    except:
        return 50.0


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_stoch(candle, df, i):

    logger.debug("[STOCH] detect_stoch() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:
        logger.error(f"[STOCH] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close]):
        return {"detected": False}

    if high <= low:
        return {"detected": False}

    k = get_stoch(df, i)

    prev_k = get_stoch(df, i - 1)

    # =====================================================
    # OVERSOLD / OVERBOUGHT CONDITIONS
    # =====================================================
    oversold = k < 20
    overbought = k > 80

    prev_oversold = prev_k < 20
    prev_overbought = prev_k > 80

    # =====================================================
    # CROSS SIGNALS
    # =====================================================
    bullish_cross = prev_k < 20 and k > 20
    bearish_cross = prev_k > 80 and k < 80

    # =====================================================
    # MOMENTUM SHIFT STRUCTURE
    # =====================================================
    bullish_setup = oversold and close > open_
    bearish_setup = overbought and close < open_

    # =====================================================
    # TYPE RESOLUTION
    # =====================================================
    if bullish_cross or bullish_setup:
        return {
            "detected": True,
            "type": "STOCHASTIC_REVERSAL",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "k": k
        }

    if bearish_cross or bearish_setup:
        return {
            "detected": True,
            "type": "STOCHASTIC_REVERSAL",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close,
            "k": k
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_stoch_trade_state(event):

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
            "failure": "Stochastic drops below oversold reclaim zone",
            "interpretation": "Bullish stochastic reversal from oversold region."
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
            "failure": "Stochastic reclaims overbought zone",
            "interpretation": "Bearish stochastic reversal from overbought region."
        }

    logger.warning(f"[STOCH] Unknown direction in trade builder: {direction}")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def stoch_event_rules(event, close, k):

    status = event.get("status")

    if status == "PENDING":

        if event["direction"] == "Bullish":
            if k > 20:
                return "CONFIRM"
            if k < 10:
                return "FAIL"

        if event["direction"] == "Bearish":
            if k < 80:
                return "CONFIRM"
            if k > 90:
                return "FAIL"

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish" and k < 10:
            return "FAIL"

        if event["direction"] == "Bearish" and k > 90:
            return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_stoch(df, event_store):

    logger.info("[STOCH] analyze_stoch() called")

    latest_pattern = None

    # SEARCH BACKWARD
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]
        detected = detect_stoch(candle, df, i)

        if not detected.get("detected"):
            continue

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],
            "trade_type": "REVERSAL",
            "high": detected["high"],
            "low": detected["low"],
            "index": i,
            "date": extract_event_date(df, i),
            "status": "PENDING",
            "k": detected["k"],
            "days_active": 0
        }

        logger.info(
            f"[STOCH] Signal found date={latest_pattern['date']} index={i} dir={latest_pattern['direction']}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        k = get_stoch(df, i)

        action = stoch_event_rules(latest_pattern, close, k)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":
            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

    trade = build_stoch_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "OSCILLATOR"
    }