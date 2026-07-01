# =========================================================
# EMA50 MODULE (STRATEGY PLUGIN - EVENT / STATE ARCHITECTURE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("ema50")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# EMA / BASE LINES
# =========================================================
def get_ema50(df, i):
    return df["Close"].ewm(span=50, adjust=False).mean().iloc[i]


def get_ema20(df, i):
    return df["Close"].ewm(span=20, adjust=False).mean().iloc[i]


def get_ema200(df, i):
    return df["Close"].ewm(span=200, adjust=False).mean().iloc[i]


def get_sma(df, i, period):
    return df["Close"].rolling(period).mean().iloc[i]


# =========================================================
# STRUCTURE LEVELS
# =========================================================
def get_primary_levels(df, i):

    try:

        lookback = df.iloc[max(0, i - 20):i]

        return {

            "support": f(lookback["Low"].min()),

            "resistance": f(lookback["High"].max()),

            "sma50": f(get_sma(df, i, 50))

        }

    except:

        return {

            "support": 0.0,

            "resistance": 0.0,

            "sma50": 0.0

        }


# =========================================================
# EMA STACK CLASSIFICATION
# =========================================================
def classify_ema_stack(
    ema20,
    ema50,
    ema200,
    close
):

    bullish_stack = (
        ema20 > ema50 > ema200
    )

    bearish_stack = (
        ema20 < ema50 < ema200
    )

    above200 = close > ema200
    below200 = close < ema200

    if bullish_stack:

        return {

            "stack": "BULL_STACK",

            "bias": "Bullish",

            "context": "EXPANSION_READY"

        }

    if bearish_stack:

        return {

            "stack": "BEAR_STACK",

            "bias": "Bearish",

            "context": "DISTRIBUTION_READY"

        }

    if above200 and ema50 > ema200:

        return {

            "stack": "ABOVE_200_BUILDING",

            "bias": "Bullish",

            "context": "LONG_BUILDING"

        }

    if below200 and ema50 < ema200:

        return {

            "stack": "BELOW_200_BUILDING",

            "bias": "Bearish",

            "context": "SHORT_BUILDING"

        }

    return {

        "stack": "TRANSITION",

        "bias": "Neutral",

        "context": "CHOP"

    }


# =========================================================
# EMA50 COMPRESSION STATE
# =========================================================
def detect_ema50_compression(
    ema50,
    ema20,
    ema200,
    close,
    atr=0.0
):

    spread = (
        abs(ema20 - ema50) +
        abs(ema50 - ema200)
    )

    tight = (
        spread < atr * 0.6
        if atr > 0
        else spread < 0.8
    )

    price_near = (

        abs(close - ema50)

        <

        (
            atr * 0.4
            if atr > 0
            else close * 0.005
        )

    )

    if tight and price_near:

        return {

            "state": "EMA50_CRUNCH"

        }

    return {

        "state": "NORMAL"

    }


# =========================================================
# EMA50 EXPANSION STATE
# (STATE ONLY - NEVER CREATES EVENTS)
# =========================================================
def detect_ema50_expansion(
    ema50,
    close,
    atr=0.0
):

    distance = abs(
        close - ema50
    )

    threshold = (
        atr
        if atr > 0
        else close * 0.015
    )

    if distance < threshold:

        return {

            "state": "NEUTRAL",

            "direction": "Neutral"

        }

    return {

        "state":
            "BULLISH_EXPANSION"
            if close > ema50
            else "BEARISH_EXPANSION",

        "direction":
            "Bullish"
            if close > ema50
            else "Bearish"

    }


# =========================================================
# EMA50 RECLAIM EVENT
# =========================================================
def detect_ema50_reclaim(
    prev_close,
    close,
    open_,
    ema50,
    prev_ema50,
    high,
    low
):

    bullish = (

        prev_close < prev_ema50

        and

        close > ema50

        and

        low <= ema50

    )

    bearish = (

        prev_close > prev_ema50

        and

        close < ema50

        and

        high >= ema50

    )

    if bullish:

        return {

            "reclaim": True,

            "direction": "Bullish"

        }

    if bearish:

        return {

            "reclaim": True,

            "direction": "Bearish"

        }

    return {

        "reclaim": False

    }


# =========================================================
# EMA50 FAILURE EVENT
# =========================================================
def detect_ema50_failure(
    prev_close,
    close,
    open_,
    ema50,
    prev_ema50
):

    bullish_break = (

        prev_close > prev_ema50

        and

        close < ema50

        and

        close < open_

    )

    bearish_break = (

        prev_close < prev_ema50

        and

        close > ema50

        and

        close > open_

    )

    if bullish_break:

        return {

            "failure": True,

            "direction": "Bearish"

        }

    if bearish_break:

        return {

            "failure": True,

            "direction": "Bullish"

        }

    return {

        "failure": False

    }


# =========================================================
# EMA50 STATE ENGINE
# (CONTINUOUS MARKET STATE)
# =========================================================
def detect_ema50_state(
    df,
    i
):

    close = f(df["Close"].iloc[i])

    ema20 = f(get_ema20(df, i))
    ema50 = f(get_ema50(df, i))
    ema200 = f(get_ema200(df, i))

    stack = classify_ema_stack(
        ema20,
        ema50,
        ema200,
        close
    )

    compression = detect_ema50_compression(
        ema50,
        ema20,
        ema200,
        close
    )

    expansion = detect_ema50_expansion(
        ema50,
        close
    )

    return {

        "stack": stack,

        "compression": compression,

        "expansion": expansion,

        "ema20": ema20,

        "ema50": ema50,

        "ema200": ema200

    }


# =========================================================
# EMA50 DETECTOR
# (EVENTS ONLY)
# =========================================================
def detect_ema50(candle, df, i):

    logger.debug("[EMA50] detect_ema50() called")

    try:

        high = f(candle["High"])
        low = f(candle["Low"])
        open_ = f(candle["Open"])
        close = f(candle["Close"])

        ema20 = f(get_ema20(df, i))
        ema50 = f(get_ema50(df, i))
        ema200 = f(get_ema200(df, i))

    except Exception as e:

        return {

            "detected": False,

            "error": str(e)

        }

    if high <= low:

        return {

            "detected": False

        }

    # -----------------------------------------------------
    # Previous Values
    # -----------------------------------------------------
    prev_close = f(df["Close"].iloc[max(0, i - 1)])
    prev_ema50 = f(get_ema50(df, max(0, i - 1)))

    # -----------------------------------------------------
    # Institutional Context
    # -----------------------------------------------------
    stack = classify_ema_stack(

        ema20,

        ema50,

        ema200,

        close

    )

    # -----------------------------------------------------
    # TRUE EVENT TRANSITIONS
    # -----------------------------------------------------
    cross_up = (

        prev_close <= prev_ema50

        and

        close > ema50

    )

    cross_down = (

        prev_close >= prev_ema50

        and

        close < ema50

    )

    reclaim = detect_ema50_reclaim(

        prev_close,

        close,

        open_,

        ema50,

        prev_ema50,

        high,

        low

    )

    failure = detect_ema50_failure(

        prev_close,

        close,

        open_,

        ema50,

        prev_ema50

    )

    compression = detect_ema50_compression(

        ema50,

        ema20,

        ema200,

        close

    )

    # -----------------------------------------------------
    # EMA50 CROSS
    # -----------------------------------------------------
    if cross_up:

        return {

            "detected": True,

            "event_type": "EMA50",

            "type": "EMA50_CROSS",

            "trade_type": "REVERSAL",

            "direction": "Bullish",

            "stack": stack["stack"],

            "context": stack["context"],

            "high": high,

            "low": low,

            "open": open_,

            "close": close,

            "ema20": ema20,

            "ema50": ema50,

            "ema200": ema200

        }

    if cross_down:

        return {

            "detected": True,

            "event_type": "EMA50",

            "type": "EMA50_CROSS",

            "trade_type": "REVERSAL",

            "direction": "Bearish",

            "stack": stack["stack"],

            "context": stack["context"],

            "high": high,

            "low": low,

            "open": open_,

            "close": close,

            "ema20": ema20,

            "ema50": ema50,

            "ema200": ema200

        }

    # -----------------------------------------------------
    # EMA50 RECLAIM
    # -----------------------------------------------------
    if reclaim["reclaim"]:

        return {

            "detected": True,

            "event_type": "EMA50",

            "type": "EMA50_RECLAIM",

            "trade_type": "CONTINUATION",

            "direction": reclaim["direction"],

            "stack": stack["stack"],

            "context": stack["context"],

            "high": high,

            "low": low,

            "open": open_,

            "close": close,

            "ema20": ema20,

            "ema50": ema50,

            "ema200": ema200

        }

    # -----------------------------------------------------
    # EMA50 FAILURE
    # -----------------------------------------------------
    if failure["failure"]:

        return {

            "detected": True,

            "event_type": "EMA50",

            "type": "EMA50_FAILURE",

            "trade_type": "REVERSAL",

            "direction": failure["direction"],

            "stack": stack["stack"],

            "context": stack["context"],

            "high": high,

            "low": low,

            "open": open_,

            "close": close,

            "ema20": ema20,

            "ema50": ema50,

            "ema200": ema200

        }

    # -----------------------------------------------------
    # EMA50 CRUNCH
    # -----------------------------------------------------
    if compression["state"] == "EMA50_CRUNCH":

        return {

            "detected": True,

            "event_type": "EMA50",

            "type": "EMA50_CRUNCH",

            "trade_type": "NEUTRAL",

            "direction": stack["bias"],

            "stack": stack["stack"],

            "context": stack["context"],

            "high": high,

            "low": low,

            "open": open_,

            "close": close,

            "ema20": ema20,

            "ema50": ema50,

            "ema200": ema200

        }

    # -----------------------------------------------------
    # EXPANSION / CONTINUATION ARE STATES
    # DO NOT CREATE EVENTS
    # -----------------------------------------------------
    return {

        "detected": False

    }


# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_ema50(event):

    pattern = event.get("type")
    direction = event.get("direction")

    state = event.get("state", {})

    stack = (
        state.get("stack", {})
        .get("stack", "TRANSITION")
    )

    context = (
        state.get("stack", {})
        .get("context", "CHOP")
    )

    compression = (
        state.get("compression", {})
        .get("state", "NORMAL")
    )

    expansion = (
        state.get("expansion", {})
        .get("state", "NEUTRAL")
    )

    status = event.get(
        "status",
        "UNKNOWN"
    )

    out = []

    # =====================================================
    # EVENT
    # =====================================================
    if pattern == "EMA50_CROSS":

        out.append(
            "Price crossed the EMA50, signaling a possible intermediate trend transition."
        )

    elif pattern == "EMA50_RECLAIM":

        out.append(
            "Price successfully reclaimed the EMA50 after testing liquidity."
        )

    elif pattern == "EMA50_FAILURE":

        out.append(
            "Price failed to hold the EMA50, indicating structural weakness."
        )

    elif pattern == "EMA50_CRUNCH":

        out.append(
            "EMA50 compression detected. Volatility has contracted."
        )

    # =====================================================
    # STACK
    # =====================================================
    if stack == "BULL_STACK":

        out.append(
            "EMA20 > EMA50 > EMA200 confirms institutional bullish alignment."
        )

    elif stack == "BEAR_STACK":

        out.append(
            "EMA20 < EMA50 < EMA200 confirms institutional bearish alignment."
        )

    elif stack == "ABOVE_200_BUILDING":

        out.append(
            "Price is building above the EMA200 while developing bullish structure."
        )

    elif stack == "BELOW_200_BUILDING":

        out.append(
            "Price is building below the EMA200 while developing bearish structure."
        )

    else:

        out.append(
            "EMA alignment remains transitional."
        )

    # =====================================================
    # CONTINUOUS STATE
    # =====================================================
    if compression == "EMA50_CRUNCH":

        out.append(
            "Compression remains active."
        )

    if expansion == "BULLISH_EXPANSION":

        out.append(
            "Bullish expansion continues."
        )

    elif expansion == "BEARISH_EXPANSION":

        out.append(
            "Bearish expansion continues."
        )

    # =====================================================
    # CONTEXT
    # =====================================================
    out.append(
        f"Institutional context: {context.replace('_',' ').title()}."
    )

    # =====================================================
    # STATUS
    # =====================================================
    if status == "PENDING":

        out.append(
            "Awaiting confirmation."
        )

    elif status == "CONFIRMED":

        out.append(
            "Structure confirmed."
        )

    elif status == "FAILED":

        out.append(
            "Structure invalidated."
        )

    elif status == "EXPIRED":

        out.append(
            "Setup expired."
        )

    return " | ".join(out)


# =========================================================
# EVENT RULES
# =========================================================
def ema50_event_rules(
    event,
    close,
    ema50
):

    status = event.get("status")
    pattern = event.get("type")

    # =====================================================
    # PENDING
    # =====================================================
    if status == "PENDING":

        # ---------------------------------------------
        # EMA50 CROSS
        # ---------------------------------------------
        if pattern == "EMA50_CROSS":

            if (
                event["direction"] == "Bullish"
                and close > ema50
            ):
                return "CONFIRM"

            if (
                event["direction"] == "Bearish"
                and close < ema50
            ):
                return "CONFIRM"

            if (
                event["direction"] == "Bullish"
                and close < ema50
            ):
                return "FAIL"

            if (
                event["direction"] == "Bearish"
                and close > ema50
            ):
                return "FAIL"

        # ---------------------------------------------
        # EMA50 RECLAIM
        # ---------------------------------------------
        elif pattern == "EMA50_RECLAIM":

            if (
                event["direction"] == "Bullish"
                and close > ema50
            ):
                return "CONFIRM"

            if (
                event["direction"] == "Bearish"
                and close < ema50
            ):
                return "CONFIRM"

            if (
                event["direction"] == "Bullish"
                and close < ema50
            ):
                return "FAIL"

            if (
                event["direction"] == "Bearish"
                and close > ema50
            ):
                return "FAIL"

        # ---------------------------------------------
        # EMA50 FAILURE
        # ---------------------------------------------
        elif pattern == "EMA50_FAILURE":

            return "CONFIRM"

        # ---------------------------------------------
        # EMA50 CRUNCH
        # ---------------------------------------------
        elif pattern == "EMA50_CRUNCH":

            if abs(close - ema50) > (close * 0.015):
                return "CONFIRM"

    # =====================================================
    # CONFIRMED
    # =====================================================
    elif status == "CONFIRMED":

        if (
            event["direction"] == "Bullish"
            and close < ema50
        ):
            return "FAIL"

        if (
            event["direction"] == "Bearish"
            and close > ema50
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
# TRADE BUILDER
# =========================================================
def build_ema50_trade_state(event):

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

    levels = event.get(
        "levels",
        {}
    )

    if direction == "Bullish":

        return {

            "trade_type": trade_type,

            "direction": "LONG",

            "entry": high,

            "stop": low - (0.10 * rng),

            "invalidation": low,

            "support": levels.get(
                "support",
                low
            ),

            "resistance": levels.get(
                "resistance",
                high
            ),

            "target1": high + rng,

            "target2": high + (2 * rng),

            "failure":
                "Close back below the EMA50.",

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

            "support": levels.get(
                "support",
                low
            ),

            "resistance": levels.get(
                "resistance",
                high
            ),

            "target1": low - rng,

            "target2": low - (2 * rng),

            "failure":
                "Close back above the EMA50.",

            "interpretation":
                interpretation

        }

    return {}


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_ema50(df, event_store):

    logger.info("[EMA50] analyze_ema50() called")

    latest_pattern = None

    # =====================================================
    # SEARCH BACKWARD FOR MOST RECENT TRUE EVENT
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_ema50(
            candle,
            df,
            i
        )

        if not detected.get("detected"):
            continue

        latest_pattern = {

            "id": 1,

            "detected": True,

            "event_type": "EMA50",

            "type": detected["type"],

            "trade_type": detected.get(
                "trade_type",
                "CONTINUATION"
            ),

            "direction": detected["direction"],

            "stack": detected["stack"],

            "context": detected["context"],

            "high": detected["high"],

            "low": detected["low"],

            "open": detected["open"],

            "close": detected["close"],

            "ema20": detected["ema20"],

            "ema50": detected["ema50"],

            "ema200": detected["ema200"],

            "index": i,

            "date": extract_event_date(df, i),

            "days_active": 0,

            "status": "PENDING",

            "status_reason":
                "Awaiting EMA50 confirmation.",

            "levels": get_primary_levels(df, i),

            "state": detect_ema50_state(
                df,
                i
            ),

            "interpretation": ""

        }

        logger.info(

            f"[EMA50] Event found "
            f"{latest_pattern['type']} "
            f"on {latest_pattern['date']}"

        )

        break

    # =====================================================
    # NOTHING FOUND
    # =====================================================
    if latest_pattern is None:

        return {

            "event": {},

            "trade": {},

            "regime": "NONE"

        }

    # =====================================================
    # VALIDATION
    # =====================================================
    for i in range(

        latest_pattern["index"] + 1,

        len(df)

    ):

        candle = df.iloc[i]

        close = f(candle["Close"])

        ema50 = f(get_ema50(df, i))

        latest_pattern["days_active"] = (

            i - latest_pattern["index"]

        )

        # ---------------------------------------------
        # Update continuous market state
        # ---------------------------------------------
        latest_pattern["state"] = detect_ema50_state(

            df,

            i

        )

        action = ema50_event_rules(

            latest_pattern,

            close,

            ema50

        )

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = (

                extract_event_date(df, i)

            )

            latest_pattern["status_reason"] = (

                "EMA50 structure confirmed."

            )

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"

            latest_pattern["resolved_date"] = (

                extract_event_date(df, i)

            )

            latest_pattern["status_reason"] = (

                build_ema50_trade_state(

                    latest_pattern

                )["failure"]

            )

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"

            latest_pattern["resolved_date"] = (

                extract_event_date(df, i)

            )

            latest_pattern["status_reason"] = (

                "EMA50 setup expired."

            )

            break

    # =====================================================
    # FINAL STATE UPDATE
    # =====================================================
    latest_pattern["state"] = detect_ema50_state(

        df,

        len(df) - 1

    )

    # =====================================================
    # INTERPRETATION
    # =====================================================
    latest_pattern["interpretation"] = (

        interpret_ema50(

            latest_pattern

        )

    )

    # =====================================================
    # TRADE
    # =====================================================
    trade = build_ema50_trade_state(

        latest_pattern

    )

    # =====================================================
    # MARKET REGIME
    # =====================================================
    final_state = latest_pattern["state"]

    stack = final_state["stack"]["stack"]

    if stack in (

        "BULL_STACK",

        "ABOVE_200_BUILDING"

    ):

        regime = "BULL_TREND"

    elif stack in (

        "BEAR_STACK",

        "BELOW_200_BUILDING"

    ):

        regime = "BEAR_TREND"

    else:

        regime = "TRANSITION"

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime

    }