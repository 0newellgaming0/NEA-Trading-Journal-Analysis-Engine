# =========================================================
# EMA20 MODULE (STRATEGY PLUGIN - EVENT / STATE ARCHITECTURE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("ema20")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# EMA20 / SMA
# =========================================================
def get_ema20(df, i):
    return df["Close"].ewm(span=20, adjust=False).mean().iloc[i]


def get_sma(df, i, period):
    return df["Close"].rolling(period).mean().iloc[i]


# =========================================================
# PRIMARY STRUCTURE LEVELS
# =========================================================
def get_primary_levels(df, i):

    try:

        lookback = df.iloc[max(0, i - 10):i]

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
# EMA20 COMPRESSION STATE
# =========================================================
def detect_ema20_compression(
    ema20,
    sma50,
    sma200,
    close,
    atr=0.0
):

    spread = (
        abs(ema20 - sma50) +
        abs(sma50 - sma200)
    )

    if atr > 0:

        threshold = atr * 0.60

    else:

        threshold = close * 0.015

    return {

        "compression": spread <= threshold,

        "spread": spread

    }


# =========================================================
# EMA20 DISTANCE STATE
# =========================================================
def detect_ema20_distance(
    ema20,
    close,
    atr=0.0
):

    distance = abs(close - ema20)

    if atr > 0:

        extended = distance > atr

    else:

        extended = distance > close * 0.01

    if close > ema20:

        direction = "Bullish"

    elif close < ema20:

        direction = "Bearish"

    else:

        direction = "Neutral"

    return {

        "extended": extended,

        "distance": distance,

        "direction": direction

    }


# =========================================================
# EMA20 ACCEPTANCE STATE
# =========================================================
def detect_ema20_acceptance(
    close,
    ema20
):

    if close > ema20:

        return {

            "accepted": True,

            "side": "ABOVE"

        }

    elif close < ema20:

        return {

            "accepted": True,

            "side": "BELOW"

        }

    return {

        "accepted": False,

        "side": "AT_LINE"

    }


# =========================================================
# EMA20 SLOPE
# =========================================================
def detect_ema20_slope(
    df,
    i
):

    ema_now = get_ema20(df, i)

    ema_prev = get_ema20(
        df,
        max(0, i - 1)
    )

    slope = ema_now - ema_prev

    if slope > 0:

        trend = "RISING"

    elif slope < 0:

        trend = "FALLING"

    else:

        trend = "FLAT"

    return {

        "trend": trend,

        "slope": slope

    }


# =========================================================
# EMA20 MOMENTUM STATE
# =========================================================
def detect_ema20_momentum(
    df,
    i
):

    ema_now = get_ema20(df, i)

    ema_prev = get_ema20(
        df,
        max(0, i - 1)
    )

    ema_prev2 = get_ema20(
        df,
        max(0, i - 2)
    )

    velocity_now = (
        ema_now -
        ema_prev
    )

    velocity_prev = (
        ema_prev -
        ema_prev2
    )

    acceleration = (
        velocity_now -
        velocity_prev
    )

    if acceleration > 0:

        state = "ACCELERATING"

    elif acceleration < 0:

        state = "DECELERATING"

    else:

        state = "STABLE"

    return {

        "state": state,

        "acceleration": acceleration

    }


# =========================================================
# EMA20 STATE ENGINE
# =========================================================
def detect_ema20_state(
    df,
    i
):

    close = f(df["Close"].iloc[i])

    ema20 = f(get_ema20(df, i))

    sma50 = f(get_sma(df, i, 50))

    sma200 = f(get_sma(df, i, 200))

    compression = detect_ema20_compression(

        ema20,

        sma50,

        sma200,

        close

    )

    distance = detect_ema20_distance(

        ema20,

        close

    )

    slope = detect_ema20_slope(

        df,

        i

    )

    momentum = detect_ema20_momentum(

        df,

        i

    )

    acceptance = detect_ema20_acceptance(

        close,

        ema20

    )

    if sma50 > sma200:

        regime = "BULL_TREND"

    elif sma50 < sma200:

        regime = "BEAR_TREND"

    else:

        regime = "TRANSITION"

    return {

        "regime": regime,

        "compression": compression,

        "distance": distance,

        "slope": slope,

        "momentum": momentum,

        "acceptance": acceptance,

        "ema20": ema20,

        "sma50": sma50,

        "sma200": sma200

    }


# =========================================================
# EMA20 RECLAIM EVENT
# =========================================================
def detect_ema20_reclaim(
    prev_close,
    close,
    open_,
    ema20,
    prev_ema20,
    high,
    low
):

    bullish = (

        prev_close < prev_ema20 and

        close > ema20 and

        low <= ema20

    )

    bearish = (

        prev_close > prev_ema20 and

        close < ema20 and

        high >= ema20

    )

    if bullish:

        return {

            "reclaim": True,

            "direction": "Bullish"

        }

    elif bearish:

        return {

            "reclaim": True,

            "direction": "Bearish"

        }

    return {

        "reclaim": False

    }


# =========================================================
# EMA20 FAILURE EVENT
# =========================================================
def detect_ema20_failure(
    prev_close,
    close,
    open_,
    ema20,
    prev_ema20
):

    bullish_break = (

        prev_close > prev_ema20 and

        close < ema20

    )

    bearish_break = (

        prev_close < prev_ema20 and

        close > ema20

    )

    if bullish_break:

        return {

            "failure": True,

            "direction": "Bearish"

        }

    elif bearish_break:

        return {

            "failure": True,

            "direction": "Bullish"

        }

    return {

        "failure": False

    }


# =========================================================
# EMA20 DETECTOR (EVENTS ONLY)
# =========================================================
def detect_ema20(
    candle,
    df,
    i
):

    logger.debug("[EMA20] detect_ema20()")

    try:

        high = f(candle["High"])
        low = f(candle["Low"])
        open_ = f(candle["Open"])
        close = f(candle["Close"])

        ema20 = f(get_ema20(df, i))

    except Exception as e:

        return {

            "detected": False,

            "error": str(e)

        }

    if high <= low:

        return {

            "detected": False

        }

    prev_close = f(
        df["Close"].iloc[
            max(0, i - 1)
        ]
    )

    prev_ema20 = f(
        get_ema20(
            df,
            max(0, i - 1)
        )
    )

    cross_up = (

        prev_close <= prev_ema20 and

        close > ema20

    )

    cross_down = (

        prev_close >= prev_ema20 and

        close < ema20

    )

    reclaim = detect_ema20_reclaim(

        prev_close,

        close,

        open_,

        ema20,

        prev_ema20,

        high,

        low

    )

    failure = detect_ema20_failure(

        prev_close,

        close,

        open_,

        ema20,

        prev_ema20

    )

    # -----------------------------------------------------
    # TRUE STRUCTURAL EVENTS ONLY
    # -----------------------------------------------------
    if cross_up:

        return {

            "detected": True,

            "event_type": "EMA20",

            "type": "EMA20_CROSS",

            "direction": "Bullish",

            "high": high,

            "low": low,

            "close": close,

            "ema20": ema20

        }

    elif cross_down:

        return {

            "detected": True,

            "event_type": "EMA20",

            "type": "EMA20_CROSS",

            "direction": "Bearish",

            "high": high,

            "low": low,

            "close": close,

            "ema20": ema20

        }

    elif reclaim["reclaim"]:

        return {

            "detected": True,

            "event_type": "EMA20",

            "type": "EMA20_RECLAIM",

            "direction": reclaim["direction"],

            "high": high,

            "low": low,

            "close": close,

            "ema20": ema20

        }

    elif failure["failure"]:

        return {

            "detected": True,

            "event_type": "EMA20",

            "type": "EMA20_FAILURE",

            "direction": failure["direction"],

            "high": high,

            "low": low,

            "close": close,

            "ema20": ema20

        }

    # -----------------------------------------------------
    # Compression, Expansion, Distance, Acceptance,
    # Momentum and Trend are STATES, not EVENTS.
    # -----------------------------------------------------
    return {

        "detected": False

    }

# =========================================================
# INTERPRETATION ENGINE (EVENT + STATE ARCHITECTURE)
# =========================================================
def interpret_ema20(event):

    pattern = event.get("type", "")
    direction = event.get("direction", "Neutral")
    status = event.get("status", "UNKNOWN")

    state = event.get("state", {})

    regime = state.get(
        "regime",
        "UNKNOWN"
    )

    compression = (
        state.get("compression", {})
        .get("compression", False)
    )

    distance = (
        state.get("distance", {})
        .get("extended", False)
    )

    acceptance = (
        state.get("acceptance", {})
        .get("side", "UNKNOWN")
    )

    slope = (
        state.get("slope", {})
        .get("trend", "UNKNOWN")
    )

    momentum = (
        state.get("momentum", {})
        .get("state", "UNKNOWN")
    )

    out = []

    # =====================================================
    # EVENT
    # =====================================================
    if pattern == "EMA20_CROSS":

        out.append(
            "Price crossed the EMA20, indicating a structural trend transition."
        )

    elif pattern == "EMA20_RECLAIM":

        out.append(
            "Price reclaimed the EMA20 following a prior loss of control."
        )

    elif pattern == "EMA20_FAILURE":

        out.append(
            "Price failed at the EMA20, indicating structural weakness."
        )

    # =====================================================
    # DIRECTION
    # =====================================================
    if direction == "Bullish":

        out.append(
            "Bullish control remains favored."
        )

    elif direction == "Bearish":

        out.append(
            "Bearish control remains favored."
        )

    # =====================================================
    # ACCEPTANCE STATE
    # =====================================================
    if acceptance == "ABOVE":

        out.append(
            "Price is currently being accepted above the EMA20."
        )

    elif acceptance == "BELOW":

        out.append(
            "Price is currently being accepted below the EMA20."
        )

    elif acceptance == "AT_LINE":

        out.append(
            "Price is testing the EMA20 equilibrium."
        )

    # =====================================================
    # COMPRESSION
    # =====================================================
    if compression:

        out.append(
            "Moving averages remain compressed."
        )

    # =====================================================
    # DISTANCE
    # =====================================================
    if distance:

        out.append(
            "Price is extended away from the EMA20."
        )

    # =====================================================
    # EMA SLOPE
    # =====================================================
    if slope == "RISING":

        out.append(
            "EMA20 slope is rising."
        )

    elif slope == "FALLING":

        out.append(
            "EMA20 slope is falling."
        )

    else:

        out.append(
            "EMA20 slope is flat."
        )

    # =====================================================
    # MOMENTUM
    # =====================================================
    if momentum == "ACCELERATING":

        out.append(
            "Trend acceleration is increasing."
        )

    elif momentum == "DECELERATING":

        out.append(
            "Trend momentum is slowing."
        )

    # =====================================================
    # REGIME
    # =====================================================
    if regime == "BULL_TREND":

        out.append(
            "Higher timeframe trend remains bullish."
        )

    elif regime == "BEAR_TREND":

        out.append(
            "Higher timeframe trend remains bearish."
        )

    else:

        out.append(
            "Higher timeframe trend is transitioning."
        )

    # =====================================================
    # STATUS
    # =====================================================
    if status == "PENDING":

        out.append(
            "Awaiting structural confirmation."
        )

    elif status == "CONFIRMED":

        out.append(
            "Structure has been confirmed."
        )

    elif status == "FAILED":

        out.append(
            "Structure has failed."
        )

    elif status == "EXPIRED":

        out.append(
            "Setup expired before confirmation."
        )

    return " | ".join(out)


# =========================================================
# EVENT RULES
# =========================================================
def ema20_event_rules(
    event,
    close,
    ema20
):

    status = event.get("status")
    pattern = event.get("type")

    # =====================================================
    # PENDING
    # =====================================================
    if status == "PENDING":

        # -------------------------------------------------
        # EMA20 CROSS
        # -------------------------------------------------
        if pattern == "EMA20_CROSS":

            if event["direction"] == "Bullish":

                if close > ema20:
                    return "CONFIRM"

                if close < ema20:
                    return "FAIL"

            elif event["direction"] == "Bearish":

                if close < ema20:
                    return "CONFIRM"

                if close > ema20:
                    return "FAIL"

        # -------------------------------------------------
        # EMA20 RECLAIM
        # -------------------------------------------------
        elif pattern == "EMA20_RECLAIM":

            if event["direction"] == "Bullish":

                if close > ema20:
                    return "CONFIRM"

                if close < ema20:
                    return "FAIL"

            elif event["direction"] == "Bearish":

                if close < ema20:
                    return "CONFIRM"

                if close > ema20:
                    return "FAIL"

        # -------------------------------------------------
        # EMA20 FAILURE
        # -------------------------------------------------
        elif pattern == "EMA20_FAILURE":

            if event["direction"] == "Bullish":

                if close > ema20:
                    return "CONFIRM"

                if close < ema20:
                    return "FAIL"

            elif event["direction"] == "Bearish":

                if close < ema20:
                    return "CONFIRM"

                if close > ema20:
                    return "FAIL"

    # =====================================================
    # CONFIRMED
    # =====================================================
    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":

            if close < ema20:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if close > ema20:
                return "FAIL"

    # =====================================================
    # OPTIONAL EXPIRATION
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
def build_ema20_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(
        high - low,
        1e-9
    )

    direction = event["direction"]

    interpretation = event.get(
        "interpretation",
        ""
    )

    levels = event.get(
        "levels",
        {}
    )

    trade_type = event.get(
        "type",
        "EMA20"
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
                "Close below EMA20.",

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
                "Close above EMA20.",

            "interpretation":
                interpretation

        }

    return {}


# =========================================================
# MAIN ANALYZER
# EVENT / STATE ARCHITECTURE
# =========================================================
def analyze_ema20(df, event_store):

    logger.info("[EMA20] analyze_ema20() called")

    latest_pattern = None

    # =====================================================
    # STEP 1
    # Locate the most recent TRUE transition event.
    #
    # Because detect_ema20() now emits ONLY:
    #
    #   EMA20_CROSS
    #   EMA20_RECLAIM
    #   EMA20_FAILURE
    #
    # the newest detected event is no longer every candle.
    # This allows the lifecycle engine to validate the event
    # using subsequent candles.
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_ema20(
            candle,
            df,
            i
        )

        if not detected.get("detected"):
            continue

        latest_pattern = {

            "id": 1,

            "event_type": "EMA20",

            "detected": True,

            "type": detected["type"],

            "direction": detected["direction"],

            "high": detected["high"],

            "low": detected["low"],

            "close": detected["close"],

            "ema20": detected["ema20"],

            "index": i,

            "date": extract_event_date(df, i),

            "days_active": 0,

            "status": "PENDING",

            "status_reason":
                "Awaiting EMA20 confirmation.",

            "levels": get_primary_levels(
                df,
                i
            ),

            # populated later
            "state": {},

            "interpretation": ""

        }

        logger.info(

            "[EMA20] Event found "
            f"{latest_pattern['type']} "
            f"date={latest_pattern['date']} "
            f"index={i}"

        )

        break

    # =====================================================
    # No event
    # =====================================================
    if latest_pattern is None:

        return {

            "event": {},

            "trade": {},

            "regime": "NONE"

        }

    # =====================================================
    # STEP 2
    # EVENT LIFECYCLE
    #
    # Walk forward through every candle AFTER the event.
    # =====================================================
    for i in range(

        latest_pattern["index"] + 1,

        len(df)

    ):

        candle = df.iloc[i]

        close = f(
            candle["Close"]
        )

        ema20 = f(
            get_ema20(
                df,
                i
            )
        )

        latest_pattern["days_active"] = (

            i -

            latest_pattern["index"]

        )

        action = ema20_event_rules(

            latest_pattern,

            close,

            ema20

        )

        # ---------------------------------------------
        # Keep state continuously updated
        # ---------------------------------------------
        latest_pattern["state"] = (

            detect_ema20_state(

                df,

                i

            )

        )

        # ---------------------------------------------
        # CONFIRMED
        # ---------------------------------------------
        if (

            action == "CONFIRM"

            and

            latest_pattern["status"] == "PENDING"

        ):

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = (

                extract_event_date(

                    df,

                    i

                )

            )

            latest_pattern["status_reason"] = (

                "EMA20 structure confirmed."

            )

        # ---------------------------------------------
        # FAILED
        # ---------------------------------------------
        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"

            latest_pattern["resolved_date"] = (

                extract_event_date(

                    df,

                    i

                )

            )

            latest_pattern["status_reason"] = (

                build_ema20_trade_state(

                    latest_pattern

                )["failure"]

            )

            break

        # ---------------------------------------------
        # EXPIRED
        # ---------------------------------------------
        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"

            latest_pattern["resolved_date"] = (

                extract_event_date(

                    df,

                    i

                )

            )

            latest_pattern["status_reason"] = (

                "EMA20 setup expired."

            )

            break

    # =====================================================
    # STEP 3
    # If no validation candles existed
    # (event occurred on newest bar),
    # populate the state from the latest candle.
    # =====================================================
    if not latest_pattern["state"]:

        latest_pattern["state"] = (

            detect_ema20_state(

                df,

                latest_pattern["index"]

            )

        )

    # =====================================================
    # STEP 4
    # Interpretation
    # =====================================================
    latest_pattern["interpretation"] = (

        interpret_ema20(

            latest_pattern

        )

    )

    # =====================================================
    # STEP 5
    # Trade
    # =====================================================
    trade = build_ema20_trade_state(

        latest_pattern

    )

    # =====================================================
    # STEP 6
    # Regime comes directly from the
    # EMA20 State Engine.
    # =====================================================
    regime = (

        latest_pattern["state"].get(

            "regime",

            "TRANSITION"

        )

    )

    logger.info(

        "[EMA20] Completed "
        f"status={latest_pattern['status']} "
        f"regime={regime}"

    )

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime

    }