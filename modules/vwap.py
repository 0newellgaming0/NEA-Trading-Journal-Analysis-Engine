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
# VWAP CALCULATION
# =========================================================
def get_vwap(df, i):

    try:

        if i <= 0:
            return f(df["Close"].iloc[i])

        tp = (
            df["High"].iloc[:i + 1] +
            df["Low"].iloc[:i + 1] +
            df["Close"].iloc[:i + 1]
        ) / 3.0

        vol = df["Volume"].iloc[:i + 1]

        cum_vol = vol.sum()

        if cum_vol <= 0:
            return f(df["Close"].iloc[i])

        cum_val = (tp * vol).sum()

        return cum_val / cum_vol

    except Exception as e:

        logger.warning(f"[VWAP] calculation error: {e}")

        return f(df["Close"].iloc[i])

def detect_vwap_state(df, i):

    vwap = get_vwap(df, i)

    prev = get_vwap(df, i - 1)

    close = f(df["Close"].iloc[i])

    if close > vwap:

        direction = "Bullish"

    elif close < vwap:

        direction = "Bearish"

    else:

        direction = "Neutral"

    return {

        "vwap": vwap,

        "direction": direction,

        "rising": vwap > prev,

        "falling": vwap < prev

    }

# =========================================================
# VWAP DETECTOR (PURE)
# =========================================================
def detect_vwap(candle, df, i):

    logger.debug("[VWAP] detect_vwap() called")

    try:

        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

    except Exception as e:

        return {"detected": False, "error": str(e)}

    if high <= low:
        return {"detected": False}

    vwap = get_vwap(df, i)

    prev_close = f(df["Close"].iloc[i - 1]) if i > 0 else close
    prev_vwap = get_vwap(df, i - 1) if i > 0 else vwap

    state = detect_vwap_state(df, i)

    # =====================================================
    # TRUE EVENTS ONLY (NO BACKGROUND STATES)
    # =====================================================

    bullish_cross = prev_close <= prev_vwap and close > vwap
    bearish_cross = prev_close >= prev_vwap and close < vwap

    bullish_accept = close > vwap and state["rising"]
    bearish_accept = close < vwap and state["falling"]

    # =====================================================
    # VWAP RECLAIM (IMPORTANT EVENT)
    # =====================================================
    if bullish_cross:

        return {

            "detected": True,
            "type": "VWAP_RECLAIM",
            "trade_type": "REVERSAL",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "close": close,
            "vwap": vwap,
            "state": state
        }

    # =====================================================
    # VWAP BREAKDOWN
    # =====================================================
    if bearish_cross:

        return {

            "detected": True,
            "type": "VWAP_BREAKDOWN",
            "trade_type": "REVERSAL",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "close": close,
            "vwap": vwap,
            "state": state
        }

    # =====================================================
    # VWAP CONTINUATION (ONLY WHEN STRONG TREND ACCEPTANCE)
    # =====================================================
    if bullish_accept and close > open_:

        return {

            "detected": True,
            "type": "VWAP_CONTINUATION",
            "trade_type": "CONTINUATION",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "close": close,
            "vwap": vwap,
            "state": state
        }

    if bearish_accept and close < open_:

        return {

            "detected": True,
            "type": "VWAP_REJECTION",
            "trade_type": "CONTINUATION",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "close": close,
            "vwap": vwap,
            "state": state
        }

    return {"detected": False}

# =========================================================
# INTERPRETATION ENGINE (PURE)
# =========================================================
def interpret_vwap(event):

    pattern = event.get("type")
    direction = event.get("direction")

    state = event.get("state", {})

    vwap_level = state.get("vwap", event.get("vwap", 0.0))
    trend_dir = state.get("direction", "Neutral")
    rising = state.get("rising", False)
    falling = state.get("falling", False)

    text = []

    # =====================================================
    # EVENT INTERPRETATION
    # =====================================================
    if pattern == "VWAP_RECLAIM":

        text.append(
            "Price reclaimed VWAP, indicating a shift back into institutional acceptance above fair value."
        )

        text.append(
            "This often marks the transition from rejection to controlled bullish continuation."
        )

    elif pattern == "VWAP_BREAKDOWN":

        text.append(
            "Price lost VWAP support, signaling institutional rejection of higher prices."
        )

        text.append(
            "This often indicates distribution or early bearish trend expansion."
        )

    elif pattern == "VWAP_CONTINUATION":

        text.append(
            "Price remains supported above VWAP with rising VWAP structure."
        )

        text.append(
            "Institutional flow continues to support directional bullish momentum."
        )

    elif pattern == "VWAP_REJECTION":

        text.append(
            "Price rejected VWAP and failed to regain acceptance."
        )

        text.append(
            "This supports continuation of bearish pressure and downside expansion."
        )

    # =====================================================
    # CONTEXT LAYER (MACD STYLE)
    # =====================================================
    if trend_dir == "Bullish":

        text.append(
            "Market is currently accepting prices above VWAP."
        )

    elif trend_dir == "Bearish":

        text.append(
            "Market is currently rejecting prices below VWAP."
        )

    # =====================================================
    # VWAP DIRECTIONAL STRUCTURE
    # =====================================================
    if rising:

        text.append("VWAP is trending upward, supporting bullish bias.")

    elif falling:

        text.append("VWAP is trending downward, reinforcing bearish bias.")

    return " | ".join(text)
    

# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_vwap_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(high - low, 1e-9)

    direction = event["direction"]
    trade_type = event.get("trade_type", "CONTINUATION")

    interpretation = event.get("interpretation", "")

    # =====================================================
    # LONG SETUP (VWAP RECLAIM / ACCEPTANCE ABOVE)
    # =====================================================
    if direction == "Bullish":

        return {

            "trade_type": trade_type,

            "direction": "LONG",

            "entry": high,

            # VWAP logic: invalidation = loss of acceptance zone
            "stop": low - (0.10 * rng),

            "invalidation": low,

            "support": event.get("vwap", low),

            "resistance": high + rng,

            "target1": high + rng,

            "target2": high + (2 * rng),

            "failure": "Price loses VWAP acceptance and closes below it.",

            "interpretation": interpretation

        }

    # =====================================================
    # SHORT SETUP (VWAP BREAKDOWN / REJECTION BELOW)
    # =====================================================
    elif direction == "Bearish":

        return {

            "trade_type": trade_type,

            "direction": "SHORT",

            "entry": low,

            "stop": high + (0.10 * rng),

            "invalidation": high,

            "support": low - rng,

            "resistance": event.get("vwap", high),

            "target1": low - rng,

            "target2": low - (2 * rng),

            "failure": "Price reclaims VWAP and closes above it.",

            "interpretation": interpretation

        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def vwap_event_rules(event, close, high, low, vwap):

    status = event.get("status")
    pattern = event.get("type")

    # =====================================================
    # PENDING STATE (FAST CONFIRM / FAIL)
    # =====================================================
    if status == "PENDING":

        # ---------------------------------------------
        # VWAP RECLAIM
        # ---------------------------------------------
        if pattern == "VWAP_RECLAIM":

            if close > vwap:
                return "CONFIRM"

            if close < vwap:
                return "FAIL"

        # ---------------------------------------------
        # VWAP BREAKDOWN
        # ---------------------------------------------
        elif pattern == "VWAP_BREAKDOWN":

            if close < vwap:
                return "CONFIRM"

            if close > vwap:
                return "FAIL"

        # ---------------------------------------------
        # VWAP CONTINUATION
        # ---------------------------------------------
        elif pattern == "VWAP_CONTINUATION":

            if close > vwap:
                return "CONFIRM"

            if close < vwap:
                return "FAIL"

        # ---------------------------------------------
        # VWAP REJECTION
        # ---------------------------------------------
        elif pattern == "VWAP_REJECTION":

            if close < vwap:
                return "CONFIRM"

            if close > vwap:
                return "FAIL"

    # =====================================================
    # CONFIRMED STATE (LOSS OF VWAP = FAILURE)
    # =====================================================
    elif status == "CONFIRMED":

        if event["direction"] == "Bullish" and close < vwap:
            return "FAIL"

        if event["direction"] == "Bearish" and close > vwap:
            return "FAIL"

    # =====================================================
    # EXPIRATION LOGIC (PREVENT STALE SIGNAL DRIFT)
    # =====================================================
    if status == "PENDING" and event.get("days_active", 0) > 8:

        return "EXPIRE"

    return None


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_vwap(df, event_store):

    logger.info("[VWAP] analyze_vwap() called")

    latest_pattern = None

    # =====================================================
    # STEP 1 - FIND MOST RECENT TRUE EVENT
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_vwap(
            candle,
            df,
            i
        )

        if not detected.get("detected"):
            continue

        state = detect_vwap_state(df, i)

        latest_pattern = {

            "id": 1,

            "detected": True,

            "event_type": "VWAP",

            "type": detected["type"],

            "trade_type": detected["trade_type"],

            "direction": detected["direction"],

            "high": detected["high"],

            "low": detected["low"],

            "close": detected["close"],

            "vwap": detected["vwap"],

            "state": state,

            "index": i,

            "date": extract_event_date(df, i),

            "days_active": 0,

            "status": "PENDING",

            "status_reason": "Awaiting VWAP confirmation.",

            "interpretation": ""

        }

        logger.info(
            f"[VWAP] Event found {latest_pattern['type']} at {latest_pattern['date']}"
        )

        break

    # =====================================================
    # NO EVENT FOUND
    # =====================================================
    if latest_pattern is None:

        return {

            "event": {},

            "trade": {},

            "regime": "NONE"

        }

    # =====================================================
    # STEP 2 - IMMEDIATE EVENT CANDLE VALIDATION
    # (MACD-STYLE EARLY FAILURE / CONFIRM CHECK)
    # =====================================================
    action = vwap_event_rules(

        latest_pattern,

        latest_pattern["close"],

        latest_pattern["high"],

        latest_pattern["low"],

        latest_pattern["vwap"]

    )

    if action == "CONFIRM":

        latest_pattern["status"] = "CONFIRMED"

        latest_pattern["resolved_date"] = latest_pattern["date"]

        latest_pattern["status_reason"] = "VWAP acceptance confirmed immediately."

    elif action == "FAIL":

        latest_pattern["status"] = "FAILED"

        latest_pattern["resolved_date"] = latest_pattern["date"]

        latest_pattern["status_reason"] = "VWAP structure invalidated on event candle."

    # =====================================================
    # STEP 3 - FORWARD VALIDATION LOOP (REAL MARKET EVOLUTION)
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        high = f(candle["High"])
        low = f(candle["Low"])

        vwap = get_vwap(df, i)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        latest_pattern["state"] = detect_vwap_state(df, i)

        action = vwap_event_rules(

            latest_pattern,

            close,

            high,

            low,

            vwap

        )

        # ---------------------------------------------
        # CONFIRMATION
        # ---------------------------------------------
        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = "VWAP acceptance confirmed during follow-through."

        # ---------------------------------------------
        # FAILURE (IMMEDIATE EXIT)
        # ---------------------------------------------
        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"

            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = build_vwap_trade_state(latest_pattern)["failure"]

            break

        # ---------------------------------------------
        # EXPIRATION CONTROL
        # ---------------------------------------------
        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"

            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = "VWAP signal expired without confirmation."

            break

    # =====================================================
    # STEP 4 - FINAL STATE UPDATE (LATEST MARKET CONTEXT)
    # =====================================================
    latest_pattern["state"] = detect_vwap_state(df, len(df) - 1)

    # =====================================================
    # STEP 5 - INTERPRETATION ENGINE
    # =====================================================
    latest_pattern["interpretation"] = interpret_vwap(latest_pattern)

    # =====================================================
    # STEP 6 - TRADE BUILD
    # =====================================================
    trade = build_vwap_trade_state(latest_pattern)

    # =====================================================
    # STEP 7 - REGIME CLASSIFICATION (VWAP CONTEXT)
    # =====================================================
    state = latest_pattern["state"]

    if state["direction"] == "Bullish":

        regime = "VWAP_BULL_ACCEPTANCE"

    elif state["direction"] == "Bearish":

        regime = "VWAP_BEAR_REJECTION"

    else:

        regime = "VWAP_TRANSITION"

    # =====================================================
    # RETURN STRUCTURE
    # =====================================================
    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime

    }