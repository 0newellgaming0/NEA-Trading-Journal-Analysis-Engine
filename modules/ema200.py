import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("ema200")


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
def get_ema200(df, i):
    return df["Close"].ewm(span=200, adjust=False).mean().iloc[i]


def get_ema50(df, i):
    return df["Close"].ewm(span=50, adjust=False).mean().iloc[i]


def get_ema20(df, i):
    return df["Close"].ewm(span=20, adjust=False).mean().iloc[i]


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
            "sma200": f(get_sma(df, i, 200))
        }

    except:
        return {
            "support": 0.0,
            "resistance": 0.0,
            "sma200": 0.0
        }


# =========================================================
# EMA STACK CLASSIFICATION (MIRROR EMA50 STYLE)
# =========================================================
def classify_ema_stack(ema20, ema50, ema200, close):

    bullish_stack = (ema20 > ema50 > ema200)
    bearish_stack = (ema20 < ema50 < ema200)

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
# EMA200 COMPRESSION STATE
# =========================================================
def detect_ema200_compression(ema200, ema50, ema20, close, atr=0.0):

    spread = abs(ema20 - ema50) + abs(ema50 - ema200)

    tight = (
        spread < atr * 0.6
        if atr > 0
        else spread < close * 0.003
    )

    price_near = abs(close - ema200) < (
        atr * 0.4 if atr > 0 else close * 0.005
    )

    if tight and price_near:
        return {"state": "EMA200_CRUNCH"}

    return {"state": "NORMAL"}


# =========================================================
# EMA200 EXPANSION STATE
# =========================================================
def detect_ema200_expansion(ema200, close, atr=0.0):

    distance = abs(close - ema200)

    threshold = atr if atr > 0 else close * 0.02

    if distance < threshold:
        return {
            "state": "NEUTRAL",
            "direction": "Neutral"
        }

    return {
        "state": "BULLISH_EXPANSION" if close > ema200 else "BEARISH_EXPANSION",
        "direction": "Bullish" if close > ema200 else "Bearish"
    }


# =========================================================
# EMA200 RECLAIM EVENT
# =========================================================
def detect_ema200_reclaim(prev_close, close, open_, ema200, prev_ema200, high, low):

    bullish = (
        prev_close < prev_ema200
        and close > ema200
        and low <= ema200
    )

    bearish = (
        prev_close > prev_ema200
        and close < ema200
        and high >= ema200
    )

    if bullish:
        return {"reclaim": True, "direction": "Bullish"}

    if bearish:
        return {"reclaim": True, "direction": "Bearish"}

    return {"reclaim": False}


# =========================================================
# EMA200 FAILURE EVENT
# =========================================================
def detect_ema200_failure(prev_close, close, open_, ema200, prev_ema200):

    bullish_break = (
        prev_close > prev_ema200
        and close < ema200
        and close < open_
    )

    bearish_break = (
        prev_close < prev_ema200
        and close > ema200
        and close > open_
    )

    if bullish_break:
        return {"failure": True, "direction": "Bearish"}

    if bearish_break:
        return {"failure": True, "direction": "Bullish"}

    return {"failure": False}


# =========================================================
# EMA200 STATE ENGINE
# =========================================================
def detect_ema200_state(df, i):

    close = f(df["Close"].iloc[i])

    ema20 = f(get_ema20(df, i))
    ema50 = f(get_ema50(df, i))
    ema200 = f(get_ema200(df, i))

    return {
        "stack": classify_ema_stack(ema20, ema50, ema200, close),
        "compression": detect_ema200_compression(ema200, ema50, ema20, close),
        "expansion": detect_ema200_expansion(ema200, close),
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200
    }


# =========================================================
# EMA200 DETECTOR (EVENTS ONLY - MIRROR EMA50)
# =========================================================
def detect_ema200(candle, df, i):

    logger.debug("[EMA200] detect_ema200() called")

    try:
        high = f(candle["High"])
        low = f(candle["Low"])
        open_ = f(candle["Open"])
        close = f(candle["Close"])

        ema20 = f(get_ema20(df, i))
        ema50 = f(get_ema50(df, i))
        ema200 = f(get_ema200(df, i))

    except Exception as e:
        return {"detected": False, "error": str(e)}

    if high <= low:
        return {"detected": False}

    prev_close = f(df["Close"].iloc[max(0, i - 1)])
    prev_ema200 = f(get_ema200(df, max(0, i - 1)))

    stack = classify_ema_stack(ema20, ema50, ema200, close)

    cross_up = (prev_close <= prev_ema200 and close > ema200)
    cross_down = (prev_close >= prev_ema200 and close < ema200)

    reclaim = detect_ema200_reclaim(prev_close, close, open_, ema200, prev_ema200, high, low)
    failure = detect_ema200_failure(prev_close, close, open_, ema200, prev_ema200)
    compression = detect_ema200_compression(ema200, ema50, ema20, close)

    if cross_up:
        return {
            "detected": True,
            "event_type": "EMA200",
            "type": "EMA200_CROSS",
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
            "event_type": "EMA200",
            "type": "EMA200_CROSS",
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

    if reclaim["reclaim"]:
        return {
            "detected": True,
            "event_type": "EMA200",
            "type": "EMA200_RECLAIM",
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

    if failure["failure"]:
        return {
            "detected": True,
            "event_type": "EMA200",
            "type": "EMA200_FAILURE",
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

    if compression["state"] == "EMA200_CRUNCH":
        return {
            "detected": True,
            "event_type": "EMA200",
            "type": "EMA200_CRUNCH",
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

    return {"detected": False}


def interpret_ema200(event):

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

    status = event.get("status", "UNKNOWN")

    out = []

    # =====================================================
    # EVENT INTERPRETATION
    # =====================================================
    if pattern == "EMA200_CROSS":

        out.append(
            "Price crossed the EMA200, signaling a major structural regime shift."
        )

    elif pattern == "EMA200_RECLAIM":

        out.append(
            "Price reclaimed the EMA200 after liquidity sweep, indicating institutional re-acceptance."
        )

    elif pattern == "EMA200_FAILURE":

        out.append(
            "Price failed the EMA200, confirming macro-level structural rejection."
        )

    elif pattern == "EMA200_CRUNCH":

        out.append(
            "EMA200 compression detected. Long-term volatility contraction in progress."
        )

    # =====================================================
    # STACK INTERPRETATION
    # =====================================================
    if stack == "BULL_STACK":

        out.append(
            "EMA20 > EMA50 > EMA200 confirms full institutional bullish alignment."
        )

    elif stack == "BEAR_STACK":

        out.append(
            "EMA20 < EMA50 < EMA200 confirms full institutional bearish distribution structure."
        )

    elif stack == "ABOVE_200_BUILDING":

        out.append(
            "Price is holding above EMA200 while building bullish macro structure."
        )

    elif stack == "BELOW_200_BUILDING":

        out.append(
            "Price is holding below EMA200 while building bearish macro structure."
        )

    else:

        out.append(
            "EMA200 structure remains in transition / rotational state."
        )

    # =====================================================
    # CONTINUOUS STATE
    # =====================================================
    if compression == "EMA200_CRUNCH":

        out.append(
            "Long-term compression remains active around EMA200."
        )

    if expansion == "BULLISH_EXPANSION":

        out.append(
            "Bullish expansion away from EMA200 continues."
        )

    elif expansion == "BEARISH_EXPANSION":

        out.append(
            "Bearish expansion away from EMA200 continues."
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

        out.append("Awaiting macro confirmation.")

    elif status == "CONFIRMED":

        out.append("Macro structure confirmed.")

    elif status == "FAILED":

        out.append("Macro structure invalidated.")

    elif status == "EXPIRED":

        out.append("Setup expired.")

    return " | ".join(out)
    
def ema200_event_rules(event, close, ema200):

    status = event.get("status")
    pattern = event.get("type")

    # =====================================================
    # PENDING STATE RULES
    # =====================================================
    if status == "PENDING":

        # ---------------------------------------------
        # CROSS
        # ---------------------------------------------
        if pattern == "EMA200_CROSS":

            if event["direction"] == "Bullish" and close > ema200:
                return "CONFIRM"

            if event["direction"] == "Bearish" and close < ema200:
                return "CONFIRM"

            if event["direction"] == "Bullish" and close < ema200:
                return "FAIL"

            if event["direction"] == "Bearish" and close > ema200:
                return "FAIL"

        # ---------------------------------------------
        # RECLAIM
        # ---------------------------------------------
        elif pattern == "EMA200_RECLAIM":

            if event["direction"] == "Bullish" and close > ema200:
                return "CONFIRM"

            if event["direction"] == "Bearish" and close < ema200:
                return "CONFIRM"

            if event["direction"] == "Bullish" and close < ema200:
                return "FAIL"

            if event["direction"] == "Bearish" and close > ema200:
                return "FAIL"

        # ---------------------------------------------
        # FAILURE
        # ---------------------------------------------
        elif pattern == "EMA200_FAILURE":

            return "CONFIRM"

        # ---------------------------------------------
        # CRUNCH
        # ---------------------------------------------
        elif pattern == "EMA200_CRUNCH":

            if abs(close - ema200) > (close * 0.02):
                return "CONFIRM"

    # =====================================================
    # CONFIRMED STATE RULES
    # =====================================================
    elif status == "CONFIRMED":

        if event["direction"] == "Bullish" and close < ema200:
            return "FAIL"

        if event["direction"] == "Bearish" and close > ema200:
            return "FAIL"

    # =====================================================
    # EXPIRATION RULE
    # =====================================================
    if status == "PENDING" and event.get("days_active", 0) > 12:
        return "EXPIRE"

    return None    


def build_ema200_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(high - low, 1e-9)

    direction = event["direction"]

    trade_type = event.get("trade_type", "CONTINUATION")

    interpretation = event.get("interpretation", "")

    levels = event.get("levels", {})

    # =====================================================
    # BULLISH
    # =====================================================
    if direction == "Bullish":

        return {
            "trade_type": trade_type,
            "direction": "LONG",
            "entry": high,
            "stop": low - (0.10 * rng),
            "invalidation": low,
            "support": levels.get("support", low),
            "resistance": levels.get("resistance", high),
            "target1": high + rng,
            "target2": high + (2 * rng),
            "failure": "Close back below EMA200.",
            "interpretation": interpretation
        }

    # =====================================================
    # BEARISH
    # =====================================================
    elif direction == "Bearish":

        return {
            "trade_type": trade_type,
            "direction": "SHORT",
            "entry": low,
            "stop": high + (0.10 * rng),
            "invalidation": high,
            "support": levels.get("support", low),
            "resistance": levels.get("resistance", high),
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": "Close back above EMA200.",
            "interpretation": interpretation
        }

    return {}


def analyze_ema200(df, event_store):

    logger.info("[EMA200] analyze_ema200() called")

    latest_pattern = None

    # =====================================================
    # FIND MOST RECENT EVENT (BACKWARD SCAN)
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_ema200(candle, df, i)

        if not detected.get("detected"):
            continue

        latest_pattern = {

            "id": 1,
            "detected": True,
            "event_type": "EMA200",
            "type": detected["type"],
            "trade_type": detected.get("trade_type", "CONTINUATION"),
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
            "status_reason": "Awaiting EMA200 confirmation.",

            "levels": get_primary_levels(df, i),

            "state": detect_ema200_state(df, i),

            "interpretation": ""
        }

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =====================================================
    # VALIDATION LOOP
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        ema200 = f(get_ema200(df, i))

        latest_pattern["days_active"] = i - latest_pattern["index"]

        latest_pattern["state"] = detect_ema200_state(df, i)

        action = ema200_event_rules(latest_pattern, close, ema200)

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "EMA200 structure confirmed."

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = build_ema200_trade_state(latest_pattern)["failure"]
            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "EMA200 setup expired."
            break

    # =====================================================
    # FINAL STATE
    # =====================================================
    latest_pattern["state"] = detect_ema200_state(df, len(df) - 1)

    # =====================================================
    # INTERPRETATION
    # =====================================================
    latest_pattern["interpretation"] = interpret_ema200(latest_pattern)

    # =====================================================
    # TRADE BUILD
    # =====================================================
    trade = build_ema200_trade_state(latest_pattern)

    # =====================================================
    # REGIME CLASSIFICATION
    # =====================================================
    stack = latest_pattern["state"]["stack"]["stack"]

    if stack in ("BULL_STACK", "ABOVE_200_BUILDING"):
        regime = "BULL_TREND"

    elif stack in ("BEAR_STACK", "BELOW_200_BUILDING"):
        regime = "BEAR_TREND"

    else:
        regime = "TRANSITION"

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": regime
    }