import logging
import pandas as pd
import numpy as np
from modules.eventEngine import extract_event_date

logger = logging.getLogger("rsi_50")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# RSI CALCULATION
# =========================================================
def get_rsi(df, i, period=14, price_col="Close"):

    try:

        if i < period:
            return 50.0

        closes = df[price_col].astype(float)

        delta = closes.diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        rsi_line = 100 - (100 / (1 + rs))

        return f(rsi_line.iloc[i])

    except Exception as e:

        logger.warning(f"[RSI] Failed to calculate RSI: {e}")

        return 50.0


# =========================================================
# RSI DETECTOR (PURE)
# =========================================================
def detect_rsi(candle, df, i):

    logger.debug("[RSI] detect_rsi() called")

    try:

        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:

        logger.error(f"[RSI] OHLC extraction failed: {e}")

        return {
            "detected": False,
            "error": str(e)
        }

    if high <= low:
        return {
            "detected": False
        }

    current_rsi = get_rsi(df, i)
    prev_rsi = get_rsi(df, i - 1)

    # =====================================================
    # RSI 50 CROSS CONDITIONS
    # =====================================================
    bullish_cross = (
        prev_rsi <= 50 and current_rsi > 50
    )

    bearish_cross = (
        prev_rsi >= 50 and current_rsi < 50
    )

    # =====================================================
    # CONTINUATION CONDITIONS
    # =====================================================
    bullish_continuation = (
        current_rsi > 50
    )

    bearish_continuation = (
        current_rsi < 50
    )

    # =====================================================
    # BALANCE ZONE
    # =====================================================
    balance_zone = (
        48 <= current_rsi <= 52
    )

    # =====================================================
    # BULLISH CROSS
    # =====================================================
    if bullish_cross:

        return {
            "detected": True,
            "type": "RSI_50_CROSS_UP",
            "trade_type": "CONTINUATION",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "close": close,
            "rsi": current_rsi
        }

    # =====================================================
    # BEARISH CROSS
    # =====================================================
    if bearish_cross:

        return {
            "detected": True,
            "type": "RSI_50_CROSS_DOWN",
            "trade_type": "CONTINUATION",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "close": close,
            "rsi": current_rsi
        }

    # =====================================================
    # RSI ABOVE 50 CONTINUATION
    # =====================================================
    if bullish_continuation and not balance_zone:

        return {
            "detected": True,
            "type": "RSI_ABOVE_50_CONTINUATION",
            "trade_type": "CONTINUATION",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "close": close,
            "rsi": current_rsi
        }

    # =====================================================
    # RSI BELOW 50 CONTINUATION
    # =====================================================
    if bearish_continuation and not balance_zone:

        return {
            "detected": True,
            "type": "RSI_BELOW_50_CONTINUATION",
            "trade_type": "CONTINUATION",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "close": close,
            "rsi": current_rsi
        }

    # =====================================================
    # BALANCE / COMPRESSION
    # =====================================================
    if balance_zone:

        return {
            "detected": True,
            "type": "RSI_50_COMPRESSION",
            "trade_type": "CONTINUATION",
            "direction": "Neutral",
            "high": high,
            "low": low,
            "close": close,
            "rsi": current_rsi
        }

    return {
        "detected": False
    }


# =========================================================
# INTERPRETATION ENGINE (PURE)
# =========================================================
def interpret_rsi(event):

    pattern = event.get("type")
    direction = event.get("direction")

    text = []

    # =====================================================
    # CROSS UP
    # =====================================================
    if pattern == "RSI_50_CROSS_UP":

        text.append(
            "RSI has crossed above 50, indicating buyers are gaining control."
        )

        text.append(
            "Momentum is shifting into bullish territory."
        )

    # =====================================================
    # CROSS DOWN
    # =====================================================
    elif pattern == "RSI_50_CROSS_DOWN":

        text.append(
            "RSI has crossed below 50, indicating sellers are gaining control."
        )

        text.append(
            "Momentum is shifting into bearish territory."
        )

    # =====================================================
    # ABOVE 50 CONTINUATION
    # =====================================================
    elif pattern == "RSI_ABOVE_50_CONTINUATION":

        text.append(
            "RSI remains above 50, confirming bullish momentum dominance."
        )

        text.append(
            "Trend continuation is supported."
        )

    # =====================================================
    # BELOW 50 CONTINUATION
    # =====================================================
    elif pattern == "RSI_BELOW_50_CONTINUATION":

        text.append(
            "RSI remains below 50, confirming bearish momentum dominance."
        )

        text.append(
            "Downtrend continuation is supported."
        )

    # =====================================================
    # COMPRESSION
    # =====================================================
    elif pattern == "RSI_50_COMPRESSION":

        text.append(
            "RSI is compressing around the 50 level."
        )

        text.append(
            "Market is in equilibrium between buyers and sellers."
        )

    # =====================================================
    # DIRECTIONAL SUMMARY
    # =====================================================
    if direction == "Bullish":

        text.append(
            "Bullish momentum remains in control above the 50 level."
        )

    elif direction == "Bearish":

        text.append(
            "Bearish momentum remains in control below the 50 level."
        )

    return " | ".join(text)


# =========================================================
# TRADE BUILDER
# =========================================================
def build_rsi_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    trade_type = event.get("trade_type", "CONTINUATION")

    # =====================================================
    # LONG
    # =====================================================
    if direction == "Bullish":

        return {

            "trade_type": trade_type,

            "direction": "LONG",

            "entry": high,

            "stop": low - rng * 0.10,

            "invalidation": low,

            "target1": high + rng,

            "target2": high + (2 * rng),

            "failure": (
                "RSI loses strength and drops below 50."
            ),

            "interpretation": event.get("interpretation", "")
        }

    # =====================================================
    # SHORT
    # =====================================================
    if direction == "Bearish":

        return {

            "trade_type": trade_type,

            "direction": "SHORT",

            "entry": low,

            "stop": high + rng * 0.10,

            "invalidation": high,

            "target1": low - rng,

            "target2": low - (2 * rng),

            "failure": (
                "RSI loses bearish control and moves above 50."
            ),

            "interpretation": event.get("interpretation", "")
        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def rsi_event_rules(event, close, rsi):

    status = event.get("status")

    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------
    if status == "PENDING":

        if event["direction"] == "Bullish":

            if rsi > 50:
                return "CONFIRM"

            if rsi < 50:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if rsi < 50:
                return "CONFIRM"

            if rsi > 50:
                return "FAIL"

    # -----------------------------------------------------
    # CONFIRMED
    # -----------------------------------------------------
    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":

            if rsi < 50:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if rsi > 50:
                return "FAIL"

    # -----------------------------------------------------
    # EXPIRATION
    # -----------------------------------------------------
    if (
        status == "PENDING"
        and event.get("days_active", 0) > 10
    ):
        return "EXPIRE"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_rsi(df, event_store):

    logger.info("[RSI] analyze_rsi() called")

    latest_pattern = None

    # =====================================================
    # SEARCH BACKWARD
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_rsi(candle, df, i)

        if not detected.get("detected"):
            continue

        latest_pattern = {

            "id": 1,
            "detected": True,
            "event_type": "RSI",
            "type": detected["type"],
            "trade_type": detected["trade_type"],
            "direction": detected["direction"],
            "high": detected["high"],
            "low": detected["low"],
            "close": detected["close"],
            "rsi": detected["rsi"],
            "index": i,
            "date": extract_event_date(df, i),
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting RSI 50 confirmation.",
            "interpretation": ""
        }

        logger.info(
            f"[RSI] Signal found date={latest_pattern['date']} "
            f"index={i} type={latest_pattern['type']}"
        )

        break

    if latest_pattern is None:

        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # =====================================================
    # VALIDATION LOOP
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        rsi = get_rsi(df, i)

        action = rsi_event_rules(
            latest_pattern,
            f(candle["Close"]),
            rsi
        )

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "RSI momentum confirmed."

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = (
                build_rsi_trade_state(latest_pattern)["failure"]
            )
            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "RSI setup expired."
            break

    # =====================================================
    # INTERPRETATION
    # =====================================================
    latest_pattern["interpretation"] = interpret_rsi(latest_pattern)

    # =====================================================
    # TRADE
    # =====================================================
    trade = build_rsi_trade_state(latest_pattern)

    return {

        "event": latest_pattern,
        "trade": trade,
        "regime": "MOMENTUM"
    }