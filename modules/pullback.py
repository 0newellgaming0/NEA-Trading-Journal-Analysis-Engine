# =========================================================
# PULLBACK MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date
from modules.signalEngine import (
    evaluate_pullback_setup,
)
logger = logging.getLogger("pullback")

# =========================================================
# FAILED PULLBACK -> ABC INITIALIZATION
# =========================================================
def initialize_abc_correction(event, close):
    """
    DO NOT USE FAILURE AS WAVE A START.

    This function is now SAFE INITIALIZER ONLY.
    It does NOT assign wave structure.
    """

    return {
        "active": True,
        "phase": "SEARCHING_FOR_B",
        "wave": "UNKNOWN",

        # anchor points will be filled later
        "wave_a_seed": event["date"],
        "wave_b_index": None,
        "wave_b_price": None,
        "wave_c_active": False,

        "projection100": None,
        "projection127": None,
        "projection161": None
    }
    
# =========================================================
# ABC CORRECTION RULES
# =========================================================
def abc_correction_rules(event, candle, f=float):
    """
    Monitors an active ABC correction.

    Returns:
        None | WAVE_B | WAVE_C | COMPLETE
    """

    correction = event.get("correction")

    if correction is None:
        return None

    close = f(candle["Close"])
    direction = event["direction"]

    # -------------------------
    # Wave A -> Wave B
    # -------------------------
    if correction["wave"] == "A":

        a = correction["a_length"]

        if direction == "Bullish":
            retrace = (close - correction["a_end"]) / max(a, 1e-9)
        else:
            retrace = (correction["a_end"] - close) / max(a, 1e-9)

        if 0.382 <= retrace <= 0.618:

            correction["wave"] = "B"
            correction["b_complete"] = True
            correction["b_end"] = close

            return "WAVE_B"

    # -------------------------
    # Wave B -> Wave C
    # -------------------------
    elif correction["wave"] == "B":

        if direction == "Bullish":
            extension = correction["b_end"] - close
        else:
            extension = close - correction["b_end"]

        if extension >= correction["projection100"]:

            correction["wave"] = "C"
            return "WAVE_C"

    # -------------------------
    # Completion
    # -------------------------
    elif correction["wave"] == "C":

        correction["active"] = False
        correction["c_complete"] = True

        return "COMPLETE"

    return None
# =========================================================
# UPDATE FAILED EVENT
# =========================================================
def update_failed_pullback(event, candle, df, i, f=float):
    """
    Correct architecture:

    FAILED does NOT create Wave A.

    It triggers:
    - backward scan
    - locate Wave B swing
    - activate Wave C
    """

    if event["status"] != "FAILED":
        return

    # -----------------------------------------------------
    # STEP 1: find Wave B (swing high after seed)
    # -----------------------------------------------------
    history = df.iloc[:i]

    window = history.tail(30)

    if event["direction"] == "Bullish":
        b_index = window["High"].idxmax()
        b_price = window.loc[b_index]["High"]
    else:
        b_index = window["Low"].idxmin()
        b_price = window.loc[b_index]["Low"]

    # -----------------------------------------------------
    # STEP 2: initialize correction properly
    # -----------------------------------------------------
    event["correction"] = {
        "active": True,
        "phase": "WAVE_C",

        "wave_b_index": int(b_index),
        "wave_b_price": float(b_price),

        "wave_a_seed": event["date"],

        "projection100": abs(event["high"] - event["low"]),
        "projection127": abs(event["high"] - event["low"]) * 1.272,
        "projection161": abs(event["high"] - event["low"]) * 1.618,

        "wave_c_complete": False
    }

        
# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_pullback(candle, signal, f):
    """
    Full continuation pullback detector.

    Requires:
        • Established trend
        • Valid pullback
        • Structure support/resistance
        • Momentum continuation
        • Fibonacci agreement
    """

    logger.debug("[PULLBACK] detect_pullback() called")

    try:

        high = f(candle["High"])
        low = f(candle["Low"])
        close = f(candle["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    trend = signal["trend"]["trend"]
    structure = signal["structure"]["label"]
    fib = signal["fibonacci"]["label"]
    pullback = signal["pullback"]["fib_zone"]
    ema = signal["ema"]["aligned"]
    momentum = signal["momentum"]["direction"]

    # -----------------------------------------------------
    # Bullish Pullback
    # -----------------------------------------------------

    if (
        trend == "Bullish"
        and structure == "Near Support"
        and pullback in ["Optimal", "Shallow"]
        and ema
        and momentum == "Bullish"
    ):

        return {

            "detected": True,
            "type": "Bullish Pullback",

            "direction": "Bullish",

            "high": high,

            "low": low,

            "interpretation":
                "Healthy pullback within an established uptrend."
        }

    # -----------------------------------------------------
    # Bearish Pullback
    # -----------------------------------------------------

    if (
        trend == "Bearish"
        and structure == "Near Resistance"
        and pullback in ["Optimal", "Shallow"]
        and ema
        and momentum == "Bearish"
    ):

        return {

            "detected": True,
            "type": "Bearish Pullback",

            "direction": "Bearish",

            "high": high,

            "low": low,

            "interpretation":
                "Healthy pullback within an established downtrend."
        }

    return {"detected": False}

def detect_pullback_seed(candle, signal, f):

    """
    Early pullback detector.

    Trend exists.

    Pullback has started.

    Continuation confirmation not yet complete.
    """

    logger.debug("[PULLBACK] detect_pullback_seed() called")

    try:

        high = f(candle["High"])
        low = f(candle["Low"])

    except Exception:

        return {"detected": False}

    trend = signal["trend"]["trend"]
    pullback = signal["pullback"]["fib_zone"]

    if trend == "Bullish":

        if pullback in ["Shallow", "Optimal"]:

            return {

                "detected": True,

                "type": "Bullish Pullback Seed",

                "direction": "Bullish",

                "high": high,

                "low": low,

                "stage": "SEED"
            }

    if trend == "Bearish":

        if pullback in ["Shallow", "Optimal"]:

            return {

                "detected": True,

                "type": "Bearish Pullback Seed",

                "direction": "Bearish",

                "high": high,

                "low": low,

                "stage": "SEED"
            }

    return {"detected": False}
    
# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_pullback_trade_state(event):

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

            "target2": high + rng * 2,

            "failure": f"Close below {low}",

            "interpretation":
                "Bullish trend continuation after pullback."
        }

    if event["direction"] == "Bearish":

        return {

            "trade_type": "CONTINUATION",

            "direction": "SHORT",

            "entry": low,

            "stop": high + rng * 0.10,

            "invalidation": high,

            "target1": low - rng,

            "target2": low - rng * 2,

            "failure": f"Close above {high}",

            "interpretation":
                "Bearish trend continuation after pullback."
        }

    return {}


def pullback_event_rules(event, candle, close, high, low):

    status = event["status"]

    # -----------------------------------------------------
    # Seed
    # -----------------------------------------------------

    if status == "SEED":

        if event["direction"] == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        if event["direction"] == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # -----------------------------------------------------
    # Pending
    # -----------------------------------------------------

    elif status == "PENDING":

        if event["direction"] == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        if event["direction"] == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # -----------------------------------------------------
    # Confirmed
    # -----------------------------------------------------

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":

            if close < event["low"]:
                return "FAIL"

        if event["direction"] == "Bearish":

            if close > event["high"]:
                return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (SEED IS REQUIRED PATH)
# =========================================================
# =========================================================
# MAIN ANALYZER (SEED IS REQUIRED PATH)
# =========================================================
def analyze_pullback(df, event_store, f=float):

    logger.info("[PULLBACK] analyze_pullback() called")

    latest_pattern = None

    # =========================================================
    # PASS 1 : FULL PULLBACK DETECTION
    # =========================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        # ----------------------------------------------
        # Historical evaluation only
        # ----------------------------------------------
        history = df.iloc[:i + 1]

        signal = evaluate_pullback_setup(
            history,
            f
        )

        detected = detect_pullback(
            candle,
            signal,
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

                "index": i,

                "date": extract_event_date(df, i),

                "days_active": 0,

                "status": "PENDING",

                "status_reason":
                    "Confirmed pullback structure detected"

            }

            logger.info(

                f"[PULLBACK] Full pullback detected "
                f"date={latest_pattern['date']} "
                f"index={i}"

            )

            break

    # =========================================================
    # PASS 2 : REQUIRED SEED DETECTION
    # =========================================================
    if latest_pattern is None:

        for i in range(len(df) - 1, -1, -1):

            candle = df.iloc[i]

            # ----------------------------------------------
            # Historical evaluation only
            # ----------------------------------------------
            history = df.iloc[:i + 1]

            signal = evaluate_pullback_setup(
                history,
                f
            )

            seed = detect_pullback_seed(
                candle,
                signal,
                f
            )

            if seed.get("detected"):

                latest_pattern = {

                    "id": 1,

                    "detected": True,

                    "type": seed["type"],

                    "direction": seed["direction"],

                    "high": seed["high"],

                    "low": seed["low"],

                    "index": i,

                    "date": extract_event_date(df, i),

                    "days_active": 0,

                    "status": "SEED",

                    "status_reason":
                        "Early pullback structure forming"

                }

                logger.info(

                    f"[PULLBACK] Seed detected "
                    f"date={latest_pattern['date']} "
                    f"index={i}"

                )

                break

    # =========================================================
    # NO PATTERN FOUND
    # =========================================================
    if latest_pattern is None:

        return {

            "event": {},

            "trade": {},

            "regime": "NONE"

        }

    # =========================================================
    # VALIDATION LOOP
    # =========================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        high = f(candle["High"])
        low = f(candle["Low"])

        latest_pattern["days_active"] = (
            i - latest_pattern["index"]
        )

        # -----------------------------------------------------
        # Continue monitoring failed pullbacks
        # -----------------------------------------------------
        if latest_pattern["status"] == "FAILED":

            update_failed_pullback(
                latest_pattern,
                candle,
                f
            )

            # Once failed, the ABC lifecycle owns the event
            continue

        action = pullback_event_rules(

            latest_pattern,

            candle,

            close,

            high,

            low

        )

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = (
                extract_event_date(df, i)
            )

            latest_pattern["status_reason"] = (
                "Pullback continuation confirmed"
            )

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"

            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = (
                build_pullback_trade_state(latest_pattern)["failure"]
            )

            continue

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"

            latest_pattern["resolved_date"] = (
                extract_event_date(df, i)
            )

            latest_pattern["status_reason"] = (
                "Pullback opportunity expired"
            )

            break

    # =========================================================
    # BUILD TRADE
    # =========================================================
    trade = build_pullback_trade_state(
        latest_pattern
    )

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": "UNKNOWN"

    }