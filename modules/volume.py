# =========================================================
# EXTREME VOLUME MODULE (SWING INSTITUTIONAL FLOW ENGINE)
# RVOL SEED → CONTEXT FILTER → CONFIRM → TRACK → INVALIDATE
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("extreme_volume")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# ADAPTIVE RVOL (SWING WEIGHTED)
# =========================================================
def compute_rvol(df, i):

    if i < 30:
        return 0.0

    current = f(df["Volume"].iloc[i])

    short_avg = f(df["Volume"].iloc[i-10:i].mean())
    swing_avg = f(df["Volume"].iloc[i-30:i].mean())

    baseline = (short_avg * 0.35) + (swing_avg * 0.65)

    if baseline <= 0:
        return 0.0

    return current / baseline


# =========================================================
# TREND CONTEXT FILTER (CRITICAL ADDITION)
# prevents false RVOL spikes in chop
# =========================================================
def get_trend_context(df, i):

    close = f(df["Close"].iloc[i])

    ema20 = df["Close"].ewm(span=20, adjust=False).mean().iloc[i]
    ema50 = df["Close"].ewm(span=50, adjust=False).mean().iloc[i]
    ema200 = df["Close"].ewm(span=200, adjust=False).mean().iloc[i]

    bullish = ema20 > ema50 > ema200 and close > ema200
    bearish = ema20 < ema50 < ema200 and close < ema200

    return {
        "bullish": bullish,
        "bearish": bearish,
        "ema20": f(ema20),
        "ema50": f(ema50),
        "ema200": f(ema200)
    }


# =========================================================
# SEED DETECTOR (EXPANDED QUALITY FILTER)
# =========================================================
def detect_extreme_volume_seed(df, i, threshold=2.5):

    rvol = compute_rvol(df, i)

    if rvol < threshold:
        return {"detected": False}

    open_ = f(df["Open"].iloc[i])
    close = f(df["Close"].iloc[i])

    high = f(df["High"].iloc[i])
    low = f(df["Low"].iloc[i])

    body = abs(close - open_)
    range_ = max(high - low, 1e-9)

    body_strength = body / range_

    # =====================================================
    # QUALITY FILTERS
    # =====================================================
    if body_strength < 0.2:
        return {"detected": False}  # weak participation candle

    return {
        "detected": True,
        "type": "EXTREME_VOLUME_SEED",
        "direction": "Bullish" if close >= open_ else "Bearish",
        "rvol": rvol,
        "high": high,
        "low": low,
        "index": i
    }


# =========================================================
# EVENT RULE ENGINE (STATE MACHINE)
# =========================================================
def volume_event_rules(event, candle, prev_candle):

    close = f(candle["Close"])
    prev_low = f(prev_candle["Low"])
    prev_high = f(prev_candle["High"])

    direction = event["direction"]
    status = event["status"]

    # =========================
    # PENDING → CONFIRM / FAIL
    # =========================
    if status == "PENDING":

        if direction == "Bullish":

            if close > prev_high:
                return "CONFIRM"

            if close < prev_low:
                return "FAIL"

        else:

            if close < prev_low:
                return "CONFIRM"

            if close > prev_high:
                return "FAIL"

    # =========================
    # CONFIRMED → TRACK
    # =========================
    if status == "CONFIRMED":

        # dynamic structure invalidation
        if direction == "Bullish" and close < prev_low:
            return "FAIL"

        if direction == "Bearish" and close > prev_high:
            return "FAIL"

        return "HOLD"

    return None


# =========================================================
# TRADE BUILDER (STRUCTURE ONLY)
# =========================================================
def build_volume_trade(event):

    direction = event["direction"]

    if event["status"] != "CONFIRMED":

        return {
            "trade_type": "VOLUME_SEED",
            "direction": direction,
            "entry": None,
            "stop": None,
            "invalidation": None,
            "target1": None,
            "target2": None,
            "failure": "Awaiting confirmation",
            "interpretation": "RVOL spike detected but not confirmed"
        }

    return {
        "trade_type": "VOLUME_EXPANSION",
        "direction": "LONG" if direction == "Bullish" else "SHORT",

        "entry": "BREAKOUT" if direction == "Bullish" else "BREAKDOWN",

        "stop": "STRUCTURE_BASED",
        "invalidation": "PREVIOUS_CANDLE_BREAK",

        "target1": "RANGE_EXPANSION",
        "target2": "TREND_EXTENSION",

        "failure": (
            "Close below previous low"
            if direction == "Bullish"
            else "Close above previous high"
        ),

        "interpretation": "Institutional RVOL expansion confirmed with structural continuation"
    }


# =========================================================
# MAIN ANALYZER (EXPANDED FLOW ENGINE)
# =========================================================
def analyze_extreme_volume(df, event_store, threshold=2.5):

    logger.info("[EXTREME VOLUME] analyzer started")

    latest_event = None

    # =====================================================
    # 1. SEED DETECTION (QUALITY FILTERED)
    # =====================================================
    for i in range(len(df) - 1, 30, -1):

        seed = detect_extreme_volume_seed(df, i, threshold)

        if not seed.get("detected"):
            continue

        context = get_trend_context(df, i)

        # =================================================
        # CONTEXT FILTER (IMPORTANT UPGRADE)
        # only take aligned volume spikes
        # =================================================
        if seed["direction"] == "Bullish" and not context["bullish"]:
            continue

        if seed["direction"] == "Bearish" and not context["bearish"]:
            continue

        latest_event = {
            "id": 1,
            "detected": True,
            "type": seed["type"],
            "direction": seed["direction"],
            "rvol": seed["rvol"],
            "high": seed["high"],
            "low": seed["low"],
            "index": i,
            "date": extract_event_date(df, i),
            "status": "PENDING",
            "context": context
        }

        break

    if not latest_event:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =====================================================
    # 2. EVENT LIFECYCLE TRACKING
    # =====================================================
    for i in range(latest_event["index"] + 1, len(df)):

        candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]

        action = volume_event_rules(latest_event, candle, prev_candle)

        latest_event["bars_active"] = i - latest_event["index"]

        if action == "CONFIRM":
            latest_event["status"] = "CONFIRMED"

        elif action == "FAIL":
            latest_event["status"] = "FAILED"
            latest_event["resolved_date"] = extract_event_date(df, i)
            break

    # =====================================================
    # 3. TRADE BUILD
    # =====================================================
    trade = build_volume_trade(latest_event)

    return {
        "event": latest_event,
        "trade": trade,
        "regime": latest_event["status"]
    }