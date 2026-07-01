# =========================================================
# THRUSTING / DELIBERATION PATTERN MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# PART 1A
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("thrust_deliberation")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0


# =========================================================
# THRUSTING PATTERN DETECTOR
#
# Classical Japanese Candlestick Methodology
#
# Structure
# ---------
# Candle 1
#   • Long bearish real body
#
# Candle 2
#   • Opens below previous close
#   • Bullish recovery candle
#   • Closes inside previous real body
#   • Close remains BELOW midpoint of first body
#
# Psychology
# ----------
# Buyers attempt a reversal but fail to regain sufficient
# ground. Sellers retain control, making this a bearish
# continuation pattern requiring downside confirmation.
# =========================================================
def detect_thrusting_pattern(c1, c2, f):

    logger.debug("[THRUST] detect_thrusting_pattern() called")

    try:

        # ---------------------------------------------
        # First Candle
        # ---------------------------------------------
        o1 = f(c1["Open"])
        h1 = f(c1["High"])
        l1 = f(c1["Low"])
        c1c = f(c1["Close"])

        # ---------------------------------------------
        # Second Candle
        # ---------------------------------------------
        o2 = f(c2["Open"])
        h2 = f(c2["High"])
        l2 = f(c2["Low"])
        c2c = f(c2["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    if any(
        v is None
        for v in [
            o1, h1, l1, c1c,
            o2, h2, l2, c2c
        ]
    ):
        return {"detected": False}

    # -------------------------------------------------
    # Candle Classification
    # -------------------------------------------------

    first_bearish = c1c < o1
    second_bullish = c2c > o2

    body1 = abs(o1 - c1c)
    range1 = max(h1 - l1, 1e-9)

    # Long first candle
    long_first = body1 >= range1 * 0.60

    # -------------------------------------------------
    # Classical Thrusting Conditions
    # -------------------------------------------------

    midpoint = (o1 + c1c) / 2.0

    opens_below_prior_close = o2 < c1c

    closes_inside_body = (
        c2c > c1c and
        c2c < o1
    )

    closes_below_midpoint = (
        c2c < midpoint
    )

    thrusting = (

        first_bearish and

        second_bullish and

        long_first and

        opens_below_prior_close and

        closes_inside_body and

        closes_below_midpoint

    )

    if not thrusting:
        return {"detected": False}

    return {

        "detected": True,

        "type": "Thrusting Pattern",

        "direction": "Bearish",

        "high": max(h1, h2),

        "low": min(l1, l2),

        "trigger": min(l1, l2),

        "invalidation": max(h1, h2),

        "close": c2c,

        "pattern_high": max(h1, h2),

        "pattern_low": min(l1, l2)

    }

# =========================================================
# DELIBERATION PATTERN DETECTOR
#
# Classical Japanese Candlestick Methodology
#
# Structure
# ---------
# Candle 1
#   • Strong bullish advance
#
# Candle 2
#   • Strong bullish continuation
#
# Candle 3
#   • Small bullish body
#   • Opens near prior close
#   • Makes only limited progress
#
# Psychology
# ----------
# Institutions continue marking price higher, but buying
# conviction deteriorates. Momentum weakens and upside
# expansion becomes increasingly difficult, creating an
# exhaustion pattern that requires downside confirmation.
# =========================================================
def detect_deliberation_pattern(c1, c2, c3, f):

    logger.debug("[DELIBERATION] detect_deliberation_pattern() called")

    try:

        # -------------------------------------------------
        # Candle 1
        # -------------------------------------------------
        o1 = f(c1["Open"])
        h1 = f(c1["High"])
        l1 = f(c1["Low"])
        c1c = f(c1["Close"])

        # -------------------------------------------------
        # Candle 2
        # -------------------------------------------------
        o2 = f(c2["Open"])
        h2 = f(c2["High"])
        l2 = f(c2["Low"])
        c2c = f(c2["Close"])

        # -------------------------------------------------
        # Candle 3
        # -------------------------------------------------
        o3 = f(c3["Open"])
        h3 = f(c3["High"])
        l3 = f(c3["Low"])
        c3c = f(c3["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    body1 = abs(c1c - o1)
    body2 = abs(c2c - o2)
    body3 = abs(c3c - o3)

    range1 = max(h1 - l1, 1e-9)
    range2 = max(h2 - l2, 1e-9)
    range3 = max(h3 - l3, 1e-9)

    # -------------------------------------------------
    # Candle Classification
    # -------------------------------------------------

    bull1 = c1c > o1
    bull2 = c2c > o2
    bull3 = c3c > o3

    long1 = body1 >= range1 * 0.60
    long2 = body2 >= range2 * 0.60

    small3 = body3 <= body2 * 0.50

    opens_near_prior_close = abs(o3 - c2c) <= range2 * 0.20

    limited_progress = (
        (c3c - c2c) <= body2 * 0.35
    )

    deliberation = (

        bull1 and
        bull2 and
        bull3 and

        long1 and
        long2 and

        small3 and

        opens_near_prior_close and

        limited_progress

    )

    if not deliberation:
        return {"detected": False}

    return {

        "detected": True,

        "type": "Deliberation Pattern",

        "direction": "Bearish",

        "high": max(h1, h2, h3),

        "low": min(l1, l2, l3),

        "trigger": min(l1, l2, l3),

        "invalidation": max(h1, h2, h3),

        "close": c3c,

        "pattern_high": max(h1, h2, h3),

        "pattern_low": min(l1, l2, l3)

    }


# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_thrust_deliberation(event):

    pattern = event.get("type", "")
    direction = event.get("direction")
    status = event.get("status")

    interpretation = []

    # =====================================================
    # THRUSTING PATTERN
    # =====================================================

    if pattern == "Thrusting Pattern":

        interpretation.append(
            "A long bearish candle was followed by a bullish recovery that penetrated the prior real body but failed to reach its midpoint."
        )

        interpretation.append(
            "The failed recovery indicates that sellers retained control despite an attempt by buyers to reverse the decline."
        )

        interpretation.append(
            "Institutional supply continued to absorb demand, favoring bearish trend continuation after downside confirmation."
        )

    # =====================================================
    # DELIBERATION PATTERN
    # =====================================================

    elif pattern == "Deliberation Pattern":

        interpretation.append(
            "Three advancing bullish candles culminated in a noticeably smaller third real body."
        )

        interpretation.append(
            "Although price continued higher, buying enthusiasm diminished as upward progress became increasingly difficult."
        )

        interpretation.append(
            "Institutional distribution or profit-taking may be emerging following an extended advance."
        )

    # =====================================================
    # STATUS
    # =====================================================

    if status == "PENDING":

        interpretation.append(
            "Pattern has formed but still requires confirmation before becoming actionable."
        )

    elif status == "CONFIRMED":

        if direction == "Bearish":

            interpretation.append(
                "Downside confirmation validated the bearish continuation/reversal thesis."
            )

        elif direction == "Bullish":

            interpretation.append(
                "Upside confirmation validated the bullish continuation thesis."
            )

    elif status == "FAILED":

        interpretation.append(
            "Price invalidated the pattern by violating its structural failure level."
        )

    elif status == "EXPIRED":

        interpretation.append(
            "The pattern failed to produce timely directional expansion and has expired."
        )

    return " | ".join(interpretation)
    
# =========================================================
# EVENT RULES
# =========================================================
def thrust_deliberation_event_rules(event, candle, close, high, low):

    status = event.get("status")
    pattern = event.get("type")
    direction = event.get("direction")

    # =====================================================
    # OPTIONAL EXPIRATION
    # =====================================================

    if event.get("days_active", 0) > 15:
        return "EXPIRE"

    # =====================================================
    # PENDING
    # =====================================================

    if status == "PENDING":

        # -------------------------------------------------
        # THRUSTING PATTERN
        # Bearish continuation
        # -------------------------------------------------

        if pattern == "Thrusting Pattern":

            if close < event["pattern_low"]:
                return "CONFIRM"

            if close > event["pattern_high"]:
                return "FAIL"

        # -------------------------------------------------
        # DELIBERATION PATTERN
        # Bearish exhaustion
        # -------------------------------------------------

        elif pattern == "Deliberation Pattern":

            if close < event["pattern_low"]:
                return "CONFIRM"

            if close > event["pattern_high"]:
                return "FAIL"

    # =====================================================
    # CONFIRMED
    # =====================================================

    elif status == "CONFIRMED":

        if direction == "Bearish":

            if close > event["pattern_high"]:
                return "FAIL"

        elif direction == "Bullish":

            if close < event["pattern_low"]:
                return "FAIL"

    return None


# =========================================================
# TRADE BUILDER
# =========================================================
def build_thrust_deliberation_trade_state(event):

    pattern = event["type"]

    high = event["pattern_high"]
    low = event["pattern_low"]

    rng = max(high - low, 1e-9)

    # =====================================================
    # THRUSTING PATTERN
    # =====================================================

    if pattern == "Thrusting Pattern":

        return {

            "trade_type": "CONTINUATION",

            "direction": "SHORT",

            "entry": low,

            "stop": high + (rng * 0.10),

            "invalidation": high,

            "target1": low - rng,

            "target2": low - (rng * 2),

            "failure": f"Close above {high}",

            "interpretation":
                interpret_thrust_deliberation(event)
        }

    # =====================================================
    # DELIBERATION PATTERN
    # =====================================================

    elif pattern == "Deliberation Pattern":

        return {

            "trade_type": "REVERSAL",

            "direction": "SHORT",

            "entry": low,

            "stop": high + (rng * 0.10),

            "invalidation": high,

            "target1": low - rng,

            "target2": low - (rng * 2),

            "failure": f"Close above {high}",

            "interpretation":
                interpret_thrust_deliberation(event)
        }

    logger.warning(
        "[THRUST/DELIB] Unknown pattern type: %s",
        pattern
    )

    return {}


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_thrust_deliberation(df, event_store, f=float):

    logger.info("[THRUST/DELIB] analyze_thrust_deliberation() called")

    latest_pattern = None

    # =====================================================
    # PASS 1
    # PRIORITIZE 3-CANDLE DELIBERATION
    # =====================================================

    for i in range(len(df) - 1, 1, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        detected = detect_deliberation_pattern(
            c1,
            c2,
            c3,
            f
        )

        if detected.get("detected"):

            latest_pattern = {

                "id": 1,

                "detected": True,

                "type": detected["type"],

                "direction": detected["direction"],

                "high": detected["high"],
                "low": detected["low"],

                "pattern_high": detected["pattern_high"],
                "pattern_low": detected["pattern_low"],

                "trigger": detected["trigger"],
                "invalidation": detected["invalidation"],

                "close": detected["close"],

                "index": i - 2,

                "date": extract_event_date(
                    df,
                    i
                ),

                "days_active": 0,

                "status": "PENDING",

                "status_reason":
                    "Deliberation Pattern detected."
            }

            logger.info(
                "[THRUST/DELIB] Deliberation detected at index=%d",
                i - 2
            )

            break

    # =====================================================
    # PASS 2
    # THRUSTING PATTERN
    # =====================================================

    if latest_pattern is None:

        for i in range(len(df) - 1, 0, -1):

            c1 = df.iloc[i - 1]
            c2 = df.iloc[i]

            detected = detect_thrusting_pattern(
                c1,
                c2,
                f
            )

            if detected.get("detected"):

                latest_pattern = {

                    "id": 1,

                    "detected": True,

                    "type": detected["type"],

                    "direction": detected["direction"],

                    "high": detected["high"],
                    "low": detected["low"],

                    "pattern_high": detected["pattern_high"],
                    "pattern_low": detected["pattern_low"],

                    "trigger": detected["trigger"],
                    "invalidation": detected["invalidation"],

                    "close": detected["close"],

                    "index": i - 1,

                    "date": extract_event_date(
                        df,
                        i
                    ),

                    "days_active": 0,

                    "status": "PENDING",

                    "status_reason":
                        "Thrusting Pattern detected."
                }

                logger.info(
                    "[THRUST/DELIB] Thrusting detected at index=%d",
                    i - 1
                )

                break

    # =====================================================
    # NO PATTERN
    # =====================================================

    if latest_pattern is None:

        return {

            "event": {},

            "trade": {},

            "regime": "NONE"

        }

    # =====================================================
    # VALIDATION LOOP
    # =====================================================

    for i in range(
        latest_pattern["index"] + 1,
        len(df)
    ):

        candle = df.iloc[i]

        close = f(candle["Close"])
        high = f(candle["High"])
        low = f(candle["Low"])

        action = thrust_deliberation_event_rules(

            latest_pattern,

            candle,

            close,

            high,

            low
        )

        latest_pattern["days_active"] = (

            i - latest_pattern["index"]

        )

        # =================================================
        # CONFIRMATION
        # =================================================

        if (
            action == "CONFIRM"
            and latest_pattern["status"] == "PENDING"
        ):

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = (
                extract_event_date(
                    df,
                    i
                )
            )

            latest_pattern["status_reason"] = (
                f"{latest_pattern['type']} confirmed."
            )

        # =================================================
        # FAILURE
        # =================================================

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"

            latest_pattern["resolved_date"] = (
                extract_event_date(
                    df,
                    i
                )
            )

            latest_pattern["status_reason"] = (
                build_thrust_deliberation_trade_state(
                    latest_pattern
                )["failure"]
            )

            break

        # =================================================
        # EXPIRATION
        # =================================================

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"

            latest_pattern["resolved_date"] = (
                extract_event_date(
                    df,
                    i
                )
            )

            latest_pattern["status_reason"] = (
                "Pattern expired before confirmation."
            )

            break

    # =====================================================
    # INTERPRETATION
    # =====================================================

    latest_pattern["interpretation"] = (

        interpret_thrust_deliberation(
            latest_pattern
        )

    )

    # =====================================================
    # TRADE
    # =====================================================

    trade = build_thrust_deliberation_trade_state(
        latest_pattern
    )

    # =====================================================
    # REGIME
    # =====================================================

    if latest_pattern["status"] == "CONFIRMED":

        if latest_pattern["direction"] == "Bearish":

            regime = "BEAR_CONTINUATION"

        else:

            regime = "BULL_CONTINUATION"

    elif latest_pattern["status"] == "FAILED":

        regime = "FAILED"

    elif latest_pattern["status"] == "EXPIRED":

        regime = "EXPIRED"

    else:

        regime = "PENDING"

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime

    }