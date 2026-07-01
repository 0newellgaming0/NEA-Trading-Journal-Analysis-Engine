# =========================================================
# MACD MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("macd")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# MACD CALCULATION
# =========================================================
def get_macd(df, i, fast=12, slow=26, signal=9):

    try:

        if i < max(slow, signal):
            return {
                "macd": 0.0,
                "signal": 0.0,
                "histogram": 0.0
            }

        closes = df["Close"].astype(float)

        ema_fast = closes.ewm(
            span=fast,
            adjust=False
        ).mean()

        ema_slow = closes.ewm(
            span=slow,
            adjust=False
        ).mean()

        macd_line = ema_fast - ema_slow

        signal_line = macd_line.ewm(
            span=signal,
            adjust=False
        ).mean()

        histogram = macd_line - signal_line

        return {

            "macd": f(macd_line.iloc[i]),

            "signal": f(signal_line.iloc[i]),

            "histogram": f(histogram.iloc[i])

        }

    except Exception as e:

        logger.warning(
            f"[MACD] Failed to calculate MACD: {e}"
        )

        return {

            "macd": 0.0,
            "signal": 0.0,
            "histogram": 0.0

        }
        
# =========================================================
# MOMENTUM EXPANSION STATE
# =========================================================
def detect_macd_expansion(df, i):

    current = get_macd(df, i)
    previous = get_macd(df, i - 1)

    histogram = current["histogram"]
    prev_histogram = previous["histogram"]

    if histogram > 0:

        if histogram > prev_histogram:

            return {

                "state": "BULLISH_EXPANSION",

                "direction": "Bullish",

                "strength": abs(histogram)

            }

        elif histogram < prev_histogram:

            return {

                "state": "BULLISH_CONTRACTION",

                "direction": "Bullish",

                "strength": abs(histogram)

            }

    elif histogram < 0:

        if histogram < prev_histogram:

            return {

                "state": "BEARISH_EXPANSION",

                "direction": "Bearish",

                "strength": abs(histogram)

            }

        elif histogram > prev_histogram:

            return {

                "state": "BEARISH_CONTRACTION",

                "direction": "Bearish",

                "strength": abs(histogram)

            }

    return {

        "state": "NEUTRAL",

        "direction": "Neutral",

        "strength": 0.0

    }        

# =========================================================
# MOMENTUM ACCELERATION
# =========================================================
def detect_macd_acceleration(df, i):

    current = get_macd(df, i)
    prev = get_macd(df, i - 1)
    prev2 = get_macd(df, i - 2)

    velocity_now = (
        current["histogram"] -
        prev["histogram"]
    )

    velocity_prev = (
        prev["histogram"] -
        prev2["histogram"]
    )

    acceleration = (
        velocity_now -
        velocity_prev
    )

    if acceleration > 0:

        return {

            "state": "ACCELERATING",

            "value": acceleration

        }

    if acceleration < 0:

        return {

            "state": "DECELERATING",

            "value": acceleration

        }

    return {

        "state": "STABLE",

        "value": 0.0

    }
    
# =========================================================
# MACD STATE ENGINE
# =========================================================
def detect_macd_state(df, i):

    values = get_macd(df, i)

    expansion = detect_macd_expansion(df, i)

    acceleration = detect_macd_acceleration(df, i)

    macd = values["macd"]
    signal = values["signal"]

    if macd > signal:

        momentum = "POSITIVE"

    elif macd < signal:

        momentum = "NEGATIVE"

    else:

        momentum = "NEUTRAL"

    if macd > 0:

        regime = "BULL_TREND"

    elif macd < 0:

        regime = "BEAR_TREND"

    else:

        regime = "TRANSITION"

    return {

        "momentum": momentum,

        "regime": regime,

        "expansion": expansion,

        "acceleration": acceleration,

        "macd": macd,

        "signal": signal,

        "histogram": values["histogram"]

    }    

# =========================================================
# MACD DETECTOR (EVENTS ONLY)
# =========================================================
def detect_macd(candle, df, i):

    logger.debug("[MACD] detect_macd() called")

    try:

        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:

        logger.error(
            f"[MACD] OHLC extraction failed: {e}"
        )

        return {

            "detected": False,

            "error": str(e)

        }

    if high <= low:

        return {

            "detected": False

        }

    current = get_macd(df, i)
    previous = get_macd(df, i - 1)

    macd = current["macd"]
    signal = current["signal"]

    prev_macd = previous["macd"]
    prev_signal = previous["signal"]

    # -----------------------------------------------------
    # TRUE EVENT TRANSITIONS
    # -----------------------------------------------------
    bullish_cross = (

        prev_macd <= prev_signal and

        macd > signal

    )

    bearish_cross = (

        prev_macd >= prev_signal and

        macd < signal

    )

    bullish_zero = (

        prev_macd <= 0 and

        macd > 0

    )

    bearish_zero = (

        prev_macd >= 0 and

        macd < 0

    )

    # -----------------------------------------------------
    # FUTURE:
    # Divergence events plug in here
    # -----------------------------------------------------

    if bullish_cross:

        return {

            "detected": True,

            "event_type": "MACD",

            "type": "MACD_BULLISH_CROSS",

            "trade_type": "REVERSAL",

            "direction": "Bullish",

            "high": high,

            "low": low,

            "close": close,

            "macd": macd,

            "signal": signal,

            "histogram": current["histogram"]

        }

    elif bearish_cross:

        return {

            "detected": True,

            "event_type": "MACD",

            "type": "MACD_BEARISH_CROSS",

            "trade_type": "REVERSAL",

            "direction": "Bearish",

            "high": high,

            "low": low,

            "close": close,

            "macd": macd,

            "signal": signal,

            "histogram": current["histogram"]

        }

    elif bullish_zero:

        return {

            "detected": True,

            "event_type": "MACD",

            "type": "MACD_ZERO_LINE_RECLAIM",

            "trade_type": "CONTINUATION",

            "direction": "Bullish",

            "high": high,

            "low": low,

            "close": close,

            "macd": macd,

            "signal": signal,

            "histogram": current["histogram"]

        }

    elif bearish_zero:

        return {

            "detected": True,

            "event_type": "MACD",

            "type": "MACD_ZERO_LINE_BREAKDOWN",

            "trade_type": "CONTINUATION",

            "direction": "Bearish",

            "high": high,

            "low": low,

            "close": close,

            "macd": macd,

            "signal": signal,

            "histogram": current["histogram"]

        }

    # -----------------------------------------------------
    # Expansion/Contraction are STATE, not EVENTS.
    # Do NOT emit an event.
    # -----------------------------------------------------
    return {

        "detected": False

    }

# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_macd(event):

    pattern = event.get("type")
    direction = event.get("direction")

    state = event.get("state", {})

    expansion = (
        state.get("expansion", {})
        .get("state", "UNKNOWN")
    )

    acceleration = (
        state.get("acceleration", {})
        .get("state", "UNKNOWN")
    )

    regime = state.get(
        "regime",
        "UNKNOWN"
    )

    status = event.get(
        "status",
        "UNKNOWN"
    )

    text = []

    # =====================================================
    # EVENT
    # =====================================================
    if pattern == "MACD_BULLISH_CROSS":

        text.append(
            "Bullish MACD crossover detected."
        )

    elif pattern == "MACD_BEARISH_CROSS":

        text.append(
            "Bearish MACD crossover detected."
        )

    elif pattern == "MACD_ZERO_LINE_RECLAIM":

        text.append(
            "MACD reclaimed the zero line."
        )

    elif pattern == "MACD_ZERO_LINE_BREAKDOWN":

        text.append(
            "MACD broke below the zero line."
        )

    elif pattern == "MACD_BULLISH_DIVERGENCE":

        text.append(
            "Bullish momentum divergence detected."
        )

    elif pattern == "MACD_BEARISH_DIVERGENCE":

        text.append(
            "Bearish momentum divergence detected."
        )

    # =====================================================
    # STATE
    # =====================================================
    if expansion == "BULLISH_EXPANSION":

        text.append(
            "Bullish momentum is expanding."
        )

    elif expansion == "BULLISH_CONTRACTION":

        text.append(
            "Bullish momentum is contracting."
        )

    elif expansion == "BEARISH_EXPANSION":

        text.append(
            "Bearish momentum is expanding."
        )

    elif expansion == "BEARISH_CONTRACTION":

        text.append(
            "Bearish momentum is contracting."
        )

    # =====================================================
    # ACCELERATION
    # =====================================================
    if acceleration == "ACCELERATING":

        text.append(
            "Momentum acceleration is increasing."
        )

    elif acceleration == "DECELERATING":

        text.append(
            "Momentum is slowing."
        )

    # =====================================================
    # REGIME
    # =====================================================
    if regime == "BULL_TREND":

        text.append(
            "MACD remains above the zero line."
        )

    elif regime == "BEAR_TREND":

        text.append(
            "MACD remains below the zero line."
        )

    # =====================================================
    # STATUS
    # =====================================================
    if status == "PENDING":

        text.append(
            "Awaiting confirmation."
        )

    elif status == "CONFIRMED":

        text.append(
            "Momentum confirmation completed."
        )

    elif status == "FAILED":

        text.append(
            "Momentum confirmation failed."
        )

    elif status == "EXPIRED":

        text.append(
            "Signal expired."
        )

    return " | ".join(text)
    

# =========================================================
# TRADE BUILDER
# =========================================================
def build_macd_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(
        high - low,
        1e-9
    )

    direction = event["direction"]

    trade_type = event.get(
        "trade_type",
        "CONTINUATION"
    )

    interpretation = event.get(
        "interpretation",
        ""
    )

    if direction == "Bullish":

        return {

            "trade_type": trade_type,

            "direction": "LONG",

            "entry": high,

            "stop": low - (0.10 * rng),

            "invalidation": low,

            "target1": high + rng,

            "target2": high + (2 * rng),

            "failure":
                "MACD loses bullish momentum.",

            "interpretation":
                interpretation
        }

    elif direction == "Bearish":

        return {

            "trade_type": trade_type,

            "direction": "SHORT",

            "entry": low,

            "stop": high + (0.10 * rng),

            "invalidation": high,

            "target1": low - rng,

            "target2": low - (2 * rng),

            "failure":
                "MACD loses bearish momentum.",

            "interpretation":
                interpretation
        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def macd_event_rules(
    event,
    close,
    macd,
    signal,
    histogram
):

    status = event.get("status")
    pattern = event.get("type")

    # =====================================================
    # PENDING
    # =====================================================
    if status == "PENDING":

        # ---------------------------------------------
        # Bullish Cross
        # ---------------------------------------------
        if pattern == "MACD_BULLISH_CROSS":

            if (
                macd > signal and
                histogram > 0
            ):
                return "CONFIRM"

            if (
                macd < signal
            ):
                return "FAIL"

        # ---------------------------------------------
        # Bearish Cross
        # ---------------------------------------------
        elif pattern == "MACD_BEARISH_CROSS":

            if (
                macd < signal and
                histogram < 0
            ):
                return "CONFIRM"

            if (
                macd > signal
            ):
                return "FAIL"

        # ---------------------------------------------
        # Zero Line Reclaim
        # ---------------------------------------------
        elif pattern == "MACD_ZERO_LINE_RECLAIM":

            if (
                macd > 0 and
                histogram > 0
            ):
                return "CONFIRM"

            if (
                macd < 0
            ):
                return "FAIL"

        # ---------------------------------------------
        # Zero Line Breakdown
        # ---------------------------------------------
        elif pattern == "MACD_ZERO_LINE_BREAKDOWN":

            if (
                macd < 0 and
                histogram < 0
            ):
                return "CONFIRM"

            if (
                macd > 0
            ):
                return "FAIL"

    # =====================================================
    # CONFIRMED
    # =====================================================
    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":

            if (
                macd < signal or
                histogram < 0
            ):
                return "FAIL"

        elif event["direction"] == "Bearish":

            if (
                macd > signal or
                histogram > 0
            ):
                return "FAIL"

    # =====================================================
    # EXPIRATION
    # =====================================================
    if (

        status == "PENDING"

        and

        event.get(
            "days_active",
            0
        ) > 10

    ):

        return "EXPIRE"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_macd(df, event_store):

    logger.info("[MACD] analyze_macd() called")

    latest_pattern = None

    # =====================================================
    # STEP 1
    # Locate the most recent TRUE EVENT
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_macd(
            candle,
            df,
            i
        )

        if not detected.get("detected"):
            continue

        state = detect_macd_state(df, i)

        latest_pattern = {

            "id": 1,

            "detected": True,

            "event_type": "MACD",

            "type": detected["type"],

            "trade_type": detected["trade_type"],

            "direction": detected["direction"],

            "high": detected["high"],

            "low": detected["low"],

            "close": detected["close"],

            "macd": detected["macd"],

            "signal": detected["signal"],

            "histogram": detected["histogram"],

            "state": state,

            "index": i,

            "date": extract_event_date(df, i),

            "days_active": 0,

            "status": "PENDING",

            "status_reason":
                "Awaiting momentum confirmation."

        }

        logger.info(

            f"[MACD] Event located "

            f"{latest_pattern['type']} "

            f"index={i}"

        )

        break

    # =====================================================
    # No event found
    # =====================================================
    if latest_pattern is None:

        return {

            "event": {},

            "trade": {},

            "regime": "NONE"

        }

    # =====================================================
    # STEP 2
    # Immediate confirmation on event candle
    # =====================================================
    action = macd_event_rules(

        latest_pattern,

        latest_pattern["close"],

        latest_pattern["macd"],

        latest_pattern["signal"],

        latest_pattern["histogram"]

    )

    if action == "CONFIRM":

        latest_pattern["status"] = "CONFIRMED"

        latest_pattern["resolved_date"] = (
            latest_pattern["date"]
        )

        latest_pattern["status_reason"] = (
            "Confirmation occurred on the event candle."
        )

    elif action == "FAIL":

        latest_pattern["status"] = "FAILED"

        latest_pattern["resolved_date"] = (
            latest_pattern["date"]
        )

        latest_pattern["status_reason"] = (
            "Signal failed on the event candle."
        )

    # =====================================================
    # STEP 3
    # Replay all future candles
    # =====================================================
    for i in range(
        latest_pattern["index"] + 1,
        len(df)
    ):

        candle = df.iloc[i]

        values = get_macd(df, i)

        latest_pattern["days_active"] = (

            i -

            latest_pattern["index"]

        )

        latest_pattern["state"] = (
            detect_macd_state(df, i)
        )

        latest_pattern["macd"] = values["macd"]

        latest_pattern["signal"] = values["signal"]

        latest_pattern["histogram"] = (
            values["histogram"]
        )

        latest_pattern["close"] = (
            f(candle["Close"])
        )

        action = macd_event_rules(

            latest_pattern,

            latest_pattern["close"],

            values["macd"],

            values["signal"],

            values["histogram"]

        )

        if (

            action == "CONFIRM"

            and

            latest_pattern["status"] == "PENDING"

        ):

            latest_pattern["status"] = (
                "CONFIRMED"
            )

            latest_pattern["resolved_date"] = (
                extract_event_date(df, i)
            )

            latest_pattern["status_reason"] = (
                "Momentum confirmed."
            )

        elif action == "FAIL":

            latest_pattern["status"] = (
                "FAILED"
            )

            latest_pattern["resolved_date"] = (
                extract_event_date(df, i)
            )

            latest_pattern["status_reason"] = (
                build_macd_trade_state(
                    latest_pattern
                )["failure"]
            )

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = (
                "EXPIRED"
            )

            latest_pattern["resolved_date"] = (
                extract_event_date(df, i)
            )

            latest_pattern["status_reason"] = (
                "MACD event expired."
            )

            break

    # =====================================================
    # STEP 4
    # Interpretation
    # =====================================================
    latest_pattern["interpretation"] = (
        interpret_macd(
            latest_pattern
        )
    )

    # =====================================================
    # STEP 5
    # Trade
    # =====================================================
    trade = build_macd_trade_state(
        latest_pattern
    )

    # =====================================================
    # STEP 6
    # Regime
    # =====================================================
    regime = (
        latest_pattern["state"]
        .get("regime", "UNKNOWN")
    )

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime

    }