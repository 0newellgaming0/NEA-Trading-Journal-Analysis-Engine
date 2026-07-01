# =========================================================
# INSIDE BAR MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# ENHANCED - DOJI SANDWICH STRUCTURE PARITY
# PART 1
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("insidebar")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# DETECTOR
# =========================================================
def detect_inside_bar(candle, prev_candle, f):

    logger.debug("[INSIDE BAR] detect_inside_bar() called")

    try:

        high = f(candle["High"])
        low = f(candle["Low"])

        mother_high = f(prev_candle["High"])
        mother_low = f(prev_candle["Low"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    if any(
        v is None
        for v in [
            high,
            low,
            mother_high,
            mother_low
        ]
    ):
        return {"detected": False}

    if (
        high < mother_high and
        low > mother_low
    ):

        rng = mother_high - mother_low

        return {

            "detected": True,

            "type": "Inside Bar",

            # Direction intentionally unresolved until breakout
            "direction": None,

            "high": high,
            "low": low,

            "mother_high": mother_high,
            "mother_low": mother_low,

            "range": rng
        }

    return {"detected": False}


# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_inside_bar(event):

    direction = event.get("direction")
    status = event.get("status")

    text = []

    # =====================================================
    # STRUCTURE
    # =====================================================

    text.append(
        "Inside Bar detected: price compressed completely within the previous mother bar."
    )

    text.append(
        "Compression represents temporary equilibrium as institutions absorb liquidity before expansion."
    )

    # =====================================================
    # DIRECTION
    # =====================================================

    if direction == "Bullish":

        text.append(
            "Bullish breakout confirmed through a closing price above the mother-bar high."
        )

        text.append(
            "Buy-side acceptance suggests institutional accumulation and continuation."
        )

    elif direction == "Bearish":

        text.append(
            "Bearish breakout confirmed through a closing price below the mother-bar low."
        )

        text.append(
            "Sell-side acceptance suggests institutional distribution and continuation."
        )

    else:

        text.append(
            "Directional confirmation remains pending while price continues to compress."
        )

    # =====================================================
    # EVENT STATUS
    # =====================================================

    if status == "PENDING":

        text.append(
            "Awaiting directional acceptance beyond the mother bar."
        )

    elif status == "CONFIRMED":

        text.append(
            "Expansion has been confirmed through a valid breakout close."
        )

    elif status == "FAILED":

        text.append(
            "Breakout failed after price lost acceptance and closed back inside the mother bar."
        )

    elif status == "EXPIRED":

        text.append(
            "Compression persisted too long without directional expansion."
        )

    return " | ".join(text)


# =========================================================
# TRADE BUILDER
# =========================================================
def build_insidebar_trade_state(event):

    mother_high = event["mother_high"]
    mother_low = event["mother_low"]

    rng = max(
        mother_high - mother_low,
        1e-9
    )

    direction = event.get("direction")

    # =====================================================
    # BULLISH
    # =====================================================

    if direction == "Bullish":

        return {

            "trade_type": "BREAKOUT",

            "direction": "LONG",

            "entry": mother_high,

            "stop": mother_low - rng * 0.10,

            "invalidation": mother_low,

            "target1": mother_high + rng,

            "target2": mother_high + rng * 2,

            "failure": f"Close below {mother_low}",

            "interpretation": interpret_inside_bar(event)
        }

    # =====================================================
    # BEARISH
    # =====================================================

    if direction == "Bearish":

        return {

            "trade_type": "BREAKDOWN",

            "direction": "SHORT",

            "entry": mother_low,

            "stop": mother_high + rng * 0.10,

            "invalidation": mother_high,

            "target1": mother_low - rng,

            "target2": mother_low - rng * 2,

            "failure": f"Close above {mother_high}",

            "interpretation": interpret_inside_bar(event)
        }

    # =====================================================
    # PENDING SETUP
    # =====================================================

    return {

        "trade_type": "BREAKOUT SETUP",

        "direction": "PENDING",

        "entry": f"Above {mother_high} / Below {mother_low}",

        "stop": None,

        "invalidation": None,

        "target1": None,

        "target2": None,

        "failure": "Breakout fails after confirmation closes back inside the mother bar.",

        "interpretation": interpret_inside_bar(event)
    }


# =========================================================
# EVENT RULES
# =========================================================
def insidebar_event_rules(event, candle, close, high, low):

    status = event.get("status")

    # =====================================================
    # OPTIONAL EXPIRATION
    # =====================================================

    if event.get("days_active", 0) > 15:
        return "EXPIRE"

    # =====================================================
    # PENDING
    # =====================================================

    if status == "PENDING":

        # ---------------------------------------------
        # Bullish Confirmation
        # Close MUST finish above the mother-bar high
        # ---------------------------------------------

        if close > event["mother_high"]:

            event["direction"] = "Bullish"

            return "CONFIRM"

        # ---------------------------------------------
        # Bearish Confirmation
        # Close MUST finish below the mother-bar low
        # ---------------------------------------------

        if close < event["mother_low"]:

            event["direction"] = "Bearish"

            return "CONFIRM"

    # =====================================================
    # CONFIRMED
    # =====================================================

    elif status == "CONFIRMED":

        # Bullish failure

        if (
            event["direction"] == "Bullish"
            and close < event["mother_high"]
        ):

            return "FAIL"

        # Bearish failure

        if (
            event["direction"] == "Bearish"
            and close > event["mother_low"]
        ):

            return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_insidebar(df, event_store, f=float):

    logger.info("[INSIDE BAR] analyze_insidebar() called")

    latest_pattern = None

    # =====================================================
    # DETECTION
    # =====================================================

    for i in range(len(df) - 1, 0, -1):

        candle = df.iloc[i]
        mother = df.iloc[i - 1]

        detected = detect_inside_bar(
            candle,
            mother,
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

                "mother_high": detected["mother_high"],
                "mother_low": detected["mother_low"],

                "range": detected["range"],

                "index": i,

                "date": extract_event_date(
                    df,
                    i
                ),

                "status": "PENDING",

                "status_reason":
                    "Inside Bar compression detected."
            }

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

        action = insidebar_event_rules(

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

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = (
                extract_event_date(
                    df,
                    i
                )
            )

            latest_pattern["status_reason"] = (

                f"{latest_pattern['direction']} "
                "Inside Bar breakout confirmed."

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

                "Breakout failed after "
                "closing back inside the mother bar."

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

                "Inside Bar expired without "
                "directional resolution."

            )

            break

    # =====================================================
    # INTERPRETATION
    # =====================================================

    latest_pattern["interpretation"] = (

        interpret_inside_bar(
            latest_pattern
        )

    )

    # =====================================================
    # TRADE BUILD
    # =====================================================

    trade = build_insidebar_trade_state(
        latest_pattern
    )

    # =====================================================
    # REGIME
    # =====================================================

    if latest_pattern["status"] == "CONFIRMED":

        if latest_pattern["direction"] == "Bullish":

            regime = "BULL_EXPANSION"

        else:

            regime = "BEAR_EXPANSION"

    elif latest_pattern["status"] == "FAILED":

        regime = "FAILED"

    elif latest_pattern["status"] == "EXPIRED":

        regime = "EXPIRED"

    else:

        regime = "COMPRESSION"

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime
    }