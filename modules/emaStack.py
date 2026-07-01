import logging
import pandas as pd
import numpy as np
from modules.eventEngine import extract_event_date

logger = logging.getLogger("EMA STACK")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0

def get_ema(c1, key):
    """
    Safe EMA getter for inconsistent dataframe schemas.
    """
    val = c1.get(key, None)

    if val is not None:
        return f(val)

    # fallback schema variants
    alt_keys = [
        key.lower(),
        key.upper(),
        key.replace("EMA", "ema"),
        key.replace("EMA", "EMA_"),
        key.replace("EMA", "ema_"),
    ]

    for k in alt_keys:
        val = c1.get(k, None)
        if val is not None:
            return f(val)

    return 0.0
    
# =========================================================
# EMA20 SUPPORT DETECTOR
# =========================================================
def detect_ema20_support(c1, f):

    logger.debug("[EMA20] detect_ema20_support() called")

    try:

        ema20 = get_ema(c1, "EMA20")
        ema50 = get_ema(c1, "EMA50")
        ema200 = get_ema(c1, "EMA200")

        open_ = f(c1["Open"])
        high = f(c1["High"])
        low = f(c1["Low"])
        close = f(c1["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    bullish_stack = (
        ema20 > ema50 > ema200
    )

    rejection = (

        low <= ema20 and
        close > ema20 and
        close > open_

    )

    if bullish_stack and rejection:

        return {
            "detected": True,
            "type": "EMA20 Support Rejection",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "ema": 20,
            "ema_price": ema20
        }

    return {"detected": False}
    
# =========================================================
# EMA50 SUPPORT DETECTOR
# =========================================================
def detect_ema50_support(c1, f):

    logger.debug("[EMA STACK] detect_ema50_support() called")

    try:

        ema20 = get_ema(c1, "EMA20")
        ema50 = get_ema(c1, "EMA50")
        ema200 = get_ema(c1, "EMA200")

        o = f(c1["Open"])
        h = f(c1["High"])
        l = f(c1["Low"])
        c = f(c1["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    # =====================================================
    # TREND FILTER
    # =====================================================

    if not (ema20 > ema50 > ema200):

        return {
            "detected": False
        }

    # =====================================================
    # SUPPORT TEST
    # =====================================================

    touched = (
        l <= ema50 and
        h >= ema50
    )

    rejected = (
        c > ema50 and
        c > o
    )

    if touched and rejected:

        return {
            "detected": True,
            "type": "EMA50 Support Bounce",
            "direction": "Bullish",
            "high": h,
            "low": l,
            "ema": ema50,
            "close": c
        }

    return {
        "detected": False
    }

# =========================================================
# EMA200 SUPPORT DETECTOR
# LONG-TERM INSTITUTIONAL SUPPORT
# =========================================================
def detect_ema200_support(c1, f):

    logger.debug("[EMA STACK] detect_ema200_support() called")

    try:

        ema200 = get_ema(c1, "EMA200")

        open_ = f(c1["Open"])
        high = f(c1["High"])
        low = f(c1["Low"])
        close = f(c1["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    rng = max(high - low, 1e-9)

    # =====================================================
    # EMA200 TEST
    # =====================================================

    touched = (
        low <= ema200 and
        high >= ema200
    )

    # =====================================================
    # STRONG REJECTION
    # =====================================================

    bullish_rejection = (

        touched and
        close > ema200 and
        close > open_ and
        (close - low) >= (rng * 0.60)

    )

    if bullish_rejection:

        return {

            "detected": True,
            "type": "EMA200 Support",

            "direction": "Bullish",

            "ema": 200,
            "ema_value": ema200,

            "high": high,
            "low": low,
            "close": close

        }

    return {
        "detected": False
    }

def detect_ema20_resistance(c1, f):

    logger.debug("[EMA STACK] detect_ema20_resistance() called")

    try:

        ema20 = get_ema(c1, "EMA20")
        ema50 = get_ema(c1, "EMA50")
        ema200 = get_ema(c1, "EMA200")

        open_ = f(c1["Open"])
        high = f(c1["High"])
        low = f(c1["Low"])
        close = f(c1["Close"])

    except Exception:
        return {"detected": False}

    bearish_stack = (
        ema20 < ema50 < ema200
    )

    body = abs(close - open_)
    upper_wick = high - max(open_, close)

    rejection = (

        high >= ema20 and
        close < ema20 and
        close < open_ and
        upper_wick > body

    )

    if bearish_stack and rejection:

        return {
            "detected": True,
            "event": "EMA20_RESISTANCE",
            "bias": "BEARISH",
            "state": "SEED",
            "level": ema20,
            "interpretation": "Bearish rejection from EMA20 resistance."
        }

    return {"detected": False}


def detect_ema50_resistance(c1, f):

    logger.debug("[EMA STACK] detect_ema50_resistance() called")

    try:

        ema20 = get_ema(c1, "EMA20")
        ema50 = get_ema(c1, "EMA50")
        ema200 = get_ema(c1, "EMA200")

        open_ = f(c1["Open"])
        high = f(c1["High"])
        low = f(c1["Low"])
        close = f(c1["Close"])

    except Exception:
        return {"detected": False}

    bearish_stack = (
        ema20 < ema50 < ema200
    )

    body = abs(close - open_)
    upper_wick = high - max(open_, close)

    rejection = (

        high >= ema50 and
        close < ema50 and
        close < open_ and
        upper_wick > body

    )

    if bearish_stack and rejection:

        return {
            "detected": True,
            "event": "EMA50_RESISTANCE",
            "bias": "BEARISH",
            "state": "SEED",
            "level": ema50,
            "interpretation": "Bearish rejection from EMA50 resistance."
        }

    return {"detected": False}


def detect_ema200_resistance(c1, f):

    logger.debug("[EMA STACK] detect_ema200_resistance() called")

    try:

        ema200 = get_ema(c1, "EMA200")

        open_ = f(c1["Open"])
        high = f(c1["High"])
        low = f(c1["Low"])
        close = f(c1["Close"])

    except Exception:
        return {"detected": False}

    body = abs(close - open_)
    upper_wick = high - max(open_, close)

    rejection = (

        high >= ema200 and
        close < ema200 and
        close < open_ and
        upper_wick > body

    )

    if rejection:

        return {
            "detected": True,
            "event": "EMA200_RESISTANCE",
            "bias": "BEARISH",
            "state": "SEED",
            "level": ema200,
            "interpretation": "Bearish rejection from EMA200 resistance."
        }

    return {"detected": False}


def detect_ema_reclaim(price, prev_price, ema20):

    logger.debug("[EMA STACK] detect_ema_reclaim() called")

    try:
        price = float(price)
        prev_price = float(prev_price)
        ema20 = float(ema20)
    except:
        return {"detected": False}

    reclaimed = (
        prev_price < ema20 and
        price > ema20
    )

    if reclaimed:

        return {
            "detected": True,
            "event": "EMA_RECLAIM",
            "bias": "BULLISH",
            "state": "SEED",
            "interpretation": "Price reclaimed EMA20 after breakdown and regained dynamic support"
        }

    return {"detected": False}

# =========================================================
# EMA FAILURE (TREND WEAKENING)
# =========================================================
def detect_ema_failure(price, prev_price, ema20, ema50):

    logger.debug("[EMA STACK] detect_ema_failure() called")

    try:
        price = float(price)
        prev_price = float(prev_price)
        ema20 = float(ema20)
        ema50 = float(ema50)
    except:
        return {"detected": False}

    failure = (
        prev_price > ema20 and
        price < ema20 and
        price < ema50
    )

    if failure:

        return {
            "detected": True,
            "event": "EMA_FAILURE",
            "bias": "BEARISH",
            "state": "FAILED",
            "interpretation": "Price lost EMA20 and EMA50 confirming structural trend failure"
        }

    return {"detected": False}


# =========================================================
# EMA COMPRESSION (PRE-BREAKOUT STATE)
# =========================================================
def detect_ema_compression(ema20, ema50, ema200, atr=None):

    logger.debug("[EMA STACK] detect_ema_compression() called")

    try:
        ema20 = float(ema20)
        ema50 = float(ema50)
        ema200 = float(ema200)
    except:
        return {"detected": False}

    spread1 = abs(ema20 - ema50)
    spread2 = abs(ema50 - ema200)

    compression = (
        spread1 < ema20 * 0.003 and
        spread2 < ema50 * 0.003
    )

    volatility_ok = atr is None or float(atr) < ema50 * 0.01

    if compression and volatility_ok:

        return {
            "detected": True,
            "event": "EMA_COMPRESSION",
            "bias": "NEUTRAL",
            "state": "SEED",
            "interpretation": "EMA structure compressed indicating pre-expansion equilibrium"
        }

    return {"detected": False}


# =========================================================
# EMA EXPANSION (BREAKOUT CONFIRMATION)
# =========================================================
def detect_ema_expansion(ema20, ema50, ema200, price):

    logger.debug("[EMA STACK] detect_ema_expansion() called")

    try:
        ema20 = float(ema20)
        ema50 = float(ema50)
        ema200 = float(ema200)
        price = float(price)
    except:
        return {"detected": False}

    spread1 = abs(ema20 - ema50)
    spread2 = abs(ema50 - ema200)

    expanded = (
        spread1 > ema20 * 0.01 and
        spread2 > ema50 * 0.01
    )

    bullish = price > ema20 > ema50 > ema200
    bearish = price < ema20 < ema50 < ema200

    if expanded and bullish:
        return {
            "detected": True,
            "event": "EMA_EXPANSION",
            "bias": "BULLISH",
            "state": "CONFIRMED",
            "interpretation": "Bullish EMA expansion with momentum acceleration and trend continuation"
        }

    if expanded and bearish:
        return {
            "detected": True,
            "event": "EMA_EXPANSION",
            "bias": "BEARISH",
            "state": "CONFIRMED",
            "interpretation": "Bearish EMA expansion with momentum acceleration and distribution phase"
        }

    return {"detected": False}

    
# =========================================================
# FULL PATTERN DETECTOR (CONFIRMATION)
# =========================================================
def detect_ema_stack(c1, prev, f):

    logger.debug("[EMA STACK] detect_ema_stack() called")

    try:

        ema20 = get_ema(c1, "EMA20")
        ema50 = get_ema(c1, "EMA50")
        ema200 = get_ema(c1, "EMA200")

        prev20 = get_ema(prev, "EMA20")
        prev50 = get_ema(prev, "EMA50")
        prev200 = get_ema(prev, "EMA200")

        close = f(c1.get("Close"))
        high = f(c1.get("High"))
        low = f(c1.get("Low"))

    except Exception:
        return {"detected": False}

    bullish = (

        ema20 > ema50 > ema200 and
        close > ema20 and
        ema20 > prev20 and
        ema50 > prev50 and
        ema200 >= prev200

    )

    bearish = (

        ema20 < ema50 < ema200 and
        close < ema20 and
        ema20 < prev20 and
        ema50 < prev50 and
        ema200 <= prev200

    )

    if bullish:

        return {
            "detected": True,
            "type": "Bullish EMA Stack",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "close": close
        }

    if bearish:

        return {
            "detected": True,
            "type": "Bearish EMA Stack",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "close": close
        }

    return {"detected": False}


# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_ema_stack(event):

    direction = event.get("direction")
    ptype = event.get("type", "")

    interpretations = []

    # =====================================================
    # EMA STRUCTURE
    # =====================================================

    if direction == "Bullish":

        interpretations.append(
            "Bullish EMA stack detected with the 20 EMA positioned above the 50 EMA and the 50 EMA above the 200 EMA."
        )

        interpretations.append(
            "Short-, intermediate-, and long-term trend alignment indicates institutional accumulation."
        )

        interpretations.append(
            "Price is trading above the 20 EMA, confirming continued momentum within the established trend."
        )

    elif direction == "Bearish":

        interpretations.append(
            "Bearish EMA stack detected with the 20 EMA positioned below the 50 EMA and the 50 EMA below the 200 EMA."
        )

        interpretations.append(
            "Short-, intermediate-, and long-term trend alignment indicates institutional distribution."
        )

        interpretations.append(
            "Price is trading below the 20 EMA, confirming continued downside momentum."
        )

    # =====================================================
    # PATTERN CONTEXT
    # =====================================================

    interpretations.append(
        "EMA stacking represents trend continuation rather than a reversal signal."
    )

    interpretations.append(
        "The greater the separation between the moving averages, the stronger the trend conviction."
    )

    # =====================================================
    # EVENT STATUS
    # =====================================================

    status = event.get("status")

    if status == "SEED":

        interpretations.append(
            "Early EMA alignment detected. Full trend confirmation remains pending."
        )

    elif status == "CONFIRMED":

        interpretations.append(
            "Trend alignment has been confirmed through continued price acceptance."
        )

    elif status == "FAILED":

        interpretations.append(
            "Price lost alignment with the EMA stack, invalidating the continuation setup."
        )

    elif status == "EXPIRED":

        interpretations.append(
            "The setup expired before producing a valid continuation signal."
        )

    return " | ".join(interpretations)


# =========================================================
# TRADE BUILDER
# =========================================================
def build_ema_stack_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(high - low, 1e-9)

    if event["direction"] == "Bullish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.10,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + (rng * 2),
            "failure": f"Close below {low}",
            "interpretation": interpret_ema_stack(event)
        }

    if event["direction"] == "Bearish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.10,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - (rng * 2),
            "failure": f"Close above {high}",
            "interpretation": interpret_ema_stack(event)
        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def ema_stack_event_rules(
    event,
    candle,
    close,
    high,
    low
):

    status = event.get("status")

    # =====================================================
    # EXPIRE
    # =====================================================

    if event.get("days_active", 0) > 30:
        return "EXPIRE"

    # =====================================================
    # SEED
    # =====================================================

    if status == "SEED":

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

    # =====================================================
    # PENDING
    # =====================================================

    elif status == "PENDING":

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

    # =====================================================
    # CONFIRMED
    # =====================================================

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":

            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if close > event["high"]:
                return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (EVENT PRIORITY + FULL LIFECYCLE)
# =========================================================
def analyze_ema_stack(df, event_store, f=float):

    logger.info("[EMA STACK] analyze_ema_stack() called")

    latest_pattern = None

    # =====================================================
    # PASS 1 : EVENT DETECTION
    # =====================================================

    for i in range(len(df) - 1, -1, -1):

        c1 = df.iloc[i]
        prev = df.iloc[i - 1] if i > 0 else c1

        close = f(c1.get("Close"))

        ema20 = get_ema(c1, "EMA20")
        ema50 = get_ema(c1, "EMA50")
        ema200 = get_ema(c1, "EMA200")

        detectors = [

            detect_ema_expansion(
                ema20,
                ema50,
                ema200,
                close
            ),

            detect_ema_failure(
                close,
                f(prev.get("Close")),
                ema20,
                ema50
            ),

            detect_ema_reclaim(
                close,
                f(prev.get("Close")),
                ema20
            ),

            detect_ema20_support(c1, f),

            detect_ema20_resistance(c1, f),

            detect_ema50_support(c1, f),

            detect_ema50_resistance(c1, f),

            detect_ema200_support(c1, f),

            detect_ema200_resistance(c1, f),

            detect_ema_compression(
                ema20,
                ema50,
                ema200
            )

        ]

        signal = next(
            (d for d in detectors if d.get("detected")),
            None
        )

        if signal:

            latest_pattern = {

                "id": 1,
                "detected": True,

                "type": signal.get(
                    "type",
                    signal.get("event")
                ),

                "direction": signal.get(
                    "direction",
                    signal.get("bias")
                ),

                "high": f(c1.get("High")),
                "low": f(c1.get("Low")),

                "index": i,
                "date": extract_event_date(df, i),

                "days_active": 0,

                "status": signal.get(
                    "state",
                    "SEED"
                ),

                "status_reason": signal.get(
                    "interpretation",
                    ""
                )

            }

            break

    # =====================================================
    # PASS 2 : EMA STACK (TREND CONTEXT ONLY)
    # =====================================================

    if latest_pattern is None:

        for i in range(len(df) - 1, -1, -1):

            c1 = df.iloc[i]
            prev = df.iloc[i - 1] if i > 0 else c1

            stack = detect_ema_stack(
                c1,
                prev,
                f
            )

            if not stack.get("detected"):
                continue

            latest_pattern = {

                "id": 1,
                "detected": True,

                "type": stack["type"],
                "direction": stack["direction"],

                "high": stack["high"],
                "low": stack["low"],

                "index": i,
                "date": extract_event_date(df, i),

                "days_active": 0,

                "status": "SEED",
                "status_reason": "EMA trend alignment detected"

            }

            break

    # =====================================================
    # NO SIGNAL
    # =====================================================

    if latest_pattern is None:

        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # =====================================================
    # EVENT LIFECYCLE
    # =====================================================

    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        high = f(candle["High"])
        low = f(candle["Low"])

        latest_pattern["days_active"] = (
            i - latest_pattern["index"]
        )

        action = ema_stack_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Entry trigger validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = build_ema_stack_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"

            break

    trade = build_ema_stack_trade_state(latest_pattern)

    return {

        "event": latest_pattern,
        "trade": trade,
        "regime": "TREND"

    }