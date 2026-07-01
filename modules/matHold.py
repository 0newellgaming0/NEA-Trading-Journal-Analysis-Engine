# =========================================================
# MAT HOLD FAMILY MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# PROGRESSIVE EVENT VERSION (SEED REQUIRED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("mat_hold")


# =========================================================
# FULL PATTERN DETECTOR (CONFIRMATION)
# =========================================================
def detect_mat_hold(c1, c2, c3, c4, c5, f):

    logger.debug("[MAT HOLD] detect_mat_hold() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
        o4, h4, l4, c4c = f(c4["Open"]), f(c4["High"]), f(c4["Low"]), f(c4["Close"])
        o5, h5, l5, c5c = f(c5["Open"]), f(c5["High"]), f(c5["Low"]), f(c5["Close"])
    except:
        return {"detected": False}

    body1 = abs(c1c - o1)
    body2 = abs(c2c - o2)
    body3 = abs(c3c - o3)
    body4 = abs(c4c - o4)
    body5 = abs(c5c - o5)

    range1 = max(h1 - l1, 1e-9)
    range5 = max(h5 - l5, 1e-9)

    long1 = body1 >= range1 * 0.60
    long5 = body5 >= range5 * 0.60

    structure_high = max(h1, h2, h3, h4)
    structure_low = min(l1, l2, l3, l4)

    # =====================================================
    # LOOSENED STRUCTURE SYMMETRY (NEW LAYER)
    # =====================================================
    pullback_depth = max(h1 - min(l2, l3, l4), 1e-9)
    pullback_ratio = pullback_depth / range1

    tight = pullback_ratio < 0.35
    balanced = 0.35 <= pullback_ratio < 0.65
    deep = pullback_ratio >= 0.65

    loose_valid = tight or balanced  # allow more structures through

    # =====================================================
    # RISING MAT HOLD
    # =====================================================
    bullish = (
        c1c > o1 and long1 and

        o2 > c1c and
        l2 > c1c and

        c2c < o2 and

        h2 < h1 and h3 < h1 and h4 < h1 and
        l2 > l1 and l3 > l1 and l4 > l1 and

        body2 < body1 and body3 < body1 and body4 < body1 and

        c5c > o5 and long5 and
        c5c > h1
    )

    # =====================================================
    # FALLING MAT HOLD
    # =====================================================
    bearish = (
        c1c < o1 and long1 and

        o2 < c1c and
        h2 < c1c and

        c2c > o2 and

        l2 > l1 and l3 > l1 and l4 > l1 and
        h2 < h1 and h3 < h1 and h4 < h1 and

        body2 < body1 and body3 < body1 and body4 < body1 and

        c5c < o5 and long5 and
        c5c < l1
    )

    # =====================================================
    # LOOSENED FALLBACK CONFIRMATION (NEW LOGIC INSIDE SAME FUNCTION)
    # =====================================================

    loose_bullish = (
        c1c > o1 and loose_valid and
        c5c > c1c and
        h2 <= h1 and h3 <= h1 and h4 <= h1
    )

    loose_bearish = (
        c1c < o1 and loose_valid and
        c5c < c1c and
        l2 >= l1 and l3 >= l1 and l4 >= l1
    )

    if bullish or loose_bullish:
        return {
            "detected": True,
            "type": "Rising Mat Hold" if bullish else "Loose Rising Mat Hold",
            "direction": "Bullish",
            "high": structure_high,
            "low": structure_low,
            "close": c5c
        }

    if bearish or loose_bearish:
        return {
            "detected": True,
            "type": "Falling Mat Hold" if bearish else "Loose Falling Mat Hold",
            "direction": "Bearish",
            "high": structure_high,
            "low": structure_low,
            "close": c5c
        }

    return {"detected": False}


# =========================================================
# REQUIRED SEED DETECTOR
# =========================================================
def detect_mat_hold_seed(c1, c2, c3, c4, c5, f):

    logger.debug("[MAT HOLD] seed detection called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
        o4, h4, l4, c4c = f(c4["Open"]), f(c4["High"]), f(c4["Low"]), f(c4["Close"])
    except:
        return {"detected": False}

    body1 = abs(c1c - o1)
    range1 = max(h1 - l1, 1e-9)
    long1 = body1 >= range1 * 0.60

    structure_high = max(h1, h2, h3, h4)
    structure_low = min(l1, l2, l3, l4)

    # =====================================================
    # LOOSENED SEED STRUCTURE VALIDATION (NEW LAYER)
    # =====================================================
    pullback_depth = max(h1 - min(l2, l3, l4), 1e-9)
    pullback_ratio = pullback_depth / range1

    soft_valid = pullback_ratio < 0.70   # widened tolerance for SEED

    bullish_seed = (
        c1c > o1 and long1 and
        o2 > c1c and l2 > c1c and
        c2c < o2 and
        h2 <= h1 and h3 <= h1 and h4 <= h1 and
        l2 > l1 and l3 > l1 and l4 > l1 and
        soft_valid
    )

    bearish_seed = (
        c1c < o1 and long1 and
        o2 < c1c and h2 < c1c and
        c2c > o2 and
        l2 >= l1 and l3 >= l1 and l4 >= l1 and
        h2 < h1 and h3 < h1 and h4 < h1 and
        soft_valid
    )

    if bullish_seed:
        return {
            "detected": True,
            "type": "Rising Mat Hold (Seed)",
            "direction": "Bullish",
            "high": structure_high,
            "low": structure_low,
            "stage": "SEED"
        }

    if bearish_seed:
        return {
            "detected": True,
            "type": "Falling Mat Hold (Seed)",
            "direction": "Bearish",
            "high": structure_high,
            "low": structure_low,
            "stage": "SEED"
        }

    return {"detected": False}

# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_mat_hold(event):

    direction = event.get("direction")
    ptype = event.get("type", "")
    status = event.get("status")

    interpretations = []

    interpretations.append(
        "Mat Hold detected: an impulsive expansion candle is followed by a controlled multi-bar consolidation before continuation."
    )

    interpretations.append(
        "The pullback structure reflects controlled retracement rather than distribution or reversal."
    )

    interpretations.append(
        "Price remains structurally anchored within the initial expansion range, preserving directional imbalance."
    )

    # =====================================================
    # LOOSENED SYMMETRY EXTENSION (NEW LOGIC LAYER)
    # =====================================================

    interpretations.append(
        "Pullback symmetry is evaluated loosely: internal candles may vary in size but must remain within impulse structure boundaries."
    )

    interpretations.append(
        "Compression quality is defined by containment within the initial expansion range rather than strict candle-to-candle symmetry."
    )

    # =====================================================
    # DIRECTIONAL CONTEXT
    # =====================================================

    if direction == "Bullish":

        interpretations.append(
            "Bullish structure indicates buyers maintained control through shallow retracement and absorption of selling pressure."
        )

        interpretations.append(
            "Failure to retrace the impulse candle suggests institutional accumulation during consolidation."
        )

        interpretations.append(
            "Breakout behavior is expected to re-accelerate trend continuation beyond structure highs."
        )

    elif direction == "Bearish":

        interpretations.append(
            "Bearish structure indicates sellers maintained control through shallow pullback and absorption of buying pressure."
        )

        interpretations.append(
            "Failure to retrace the impulse candle suggests institutional distribution during consolidation."
        )

        interpretations.append(
            "Breakdown behavior is expected to extend trend continuation below structure lows."
        )

    # =====================================================
    # STATUS CONTEXT
    # =====================================================

    if status == "SEED":

        interpretations.append(
            "Early Mat Hold structure detected but continuation remains unconfirmed."
        )

    elif status == "PENDING":

        interpretations.append(
            "Full Mat Hold structure present; awaiting directional acceptance."
        )

    elif status == "CONFIRMED":

        interpretations.append(
            "Mat Hold continuation confirmed with directional acceptance beyond structure boundary."
        )

    elif status == "FAILED":

        interpretations.append(
            "Mat Hold invalidated due to failure of directional continuation."
        )

    elif status == "EXPIRED":

        interpretations.append(
            "Mat Hold structure expired without continuation."
        )

    return " | ".join(interpretations)


# =========================================================
# TRADE BUILDER
# =========================================================
def build_mat_hold_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    interpretation = interpret_mat_hold(event)

    direction = event.get("direction")

    if direction == "Bullish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - (rng * 0.10),
            "invalidation": low,
            "target1": high + rng,
            "target2": high + (rng * 2),
            "failure": f"Close below {low}",
            "interpretation": interpretation
        }

    if direction == "Bearish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + (rng * 0.10),
            "invalidation": high,
            "target1": low - rng,
            "target2": low - (rng * 2),
            "failure": f"Close above {high}",
            "interpretation": interpretation
        }

    return {}


# =========================================================
# EVENT RULES
# =========================================================
def mat_hold_event_rules(event, candle, close, high, low):

    status = event.get("status", "SEED")

    # -----------------------------------------------------
    # EXPIRATION CONTROL
    # -----------------------------------------------------
    if event.get("days_active", 0) > 15:
        return "EXPIRE"

    direction = event.get("direction")

    # =====================================================
    # SEED STATE
    # =====================================================
    if status == "SEED":

        if direction == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        elif direction == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # =====================================================
    # PENDING STATE
    # =====================================================
    elif status == "PENDING":

        if direction == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        elif direction == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # =====================================================
    # CONFIRMED STATE
    # =====================================================
    elif status == "CONFIRMED":

        if direction == "Bullish" and close < event["low"]:
            return "FAIL"

        if direction == "Bearish" and close > event["high"]:
            return "FAIL"

    return None

# =========================================================
# MAIN ANALYZER (SEED REQUIRED PATH)
# =========================================================
def analyze_mat_hold(df, event_store, f=float):

    logger.info("[MAT HOLD] analyze_mat_hold() called")

    latest_pattern = None

    # =====================================================
    # PASS 1: FULL PATTERN DETECTION
    # =====================================================
    for i in range(len(df) - 1, 3, -1):

        c1 = df.iloc[i - 4]
        c2 = df.iloc[i - 3]
        c3 = df.iloc[i - 2]
        c4 = df.iloc[i - 1]
        c5 = df.iloc[i]

        detected = detect_mat_hold(c1, c2, c3, c4, c5, f)

        if detected.get("detected"):

            event_date = extract_event_date(df, i - 4)

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "index": i - 4,

                # ✅ FIX: correct detected date (was missing/unknown)
                "date": event_date,
                "detected_date": event_date,

                "status": "PENDING",
                "status_reason": "Full Mat Hold detected"
            }
            break

    # =====================================================
    # PASS 2: SEED DETECTION
    # =====================================================
    if latest_pattern is None:

        for i in range(len(df) - 1, 3, -1):

            c1 = df.iloc[i - 4]
            c2 = df.iloc[i - 3]
            c3 = df.iloc[i - 2]
            c4 = df.iloc[i - 1]
            c5 = df.iloc[i]

            seed = detect_mat_hold_seed(c1, c2, c3, c4, c5, f)

            if seed.get("detected"):

                event_date = extract_event_date(df, i - 4)

                latest_pattern = {
                    "id": 1,
                    "detected": True,
                    "type": seed["type"],
                    "direction": seed["direction"],
                    "high": seed["high"],
                    "low": seed["low"],
                    "index": i - 4,

                    # ✅ FIX: correct detected date
                    "date": event_date,
                    "detected_date": event_date,

                    "status": "SEED",
                    "status_reason": "Early Mat Hold structure forming"
                }
                break

    if latest_pattern is None:
        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # =====================================================
    # VALIDATION LOOP
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        high = f(candle["High"])
        low = f(candle["Low"])

        action = mat_hold_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Mat Hold structure confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Mat Hold invalidated"
            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Expired"
            break

    trade = build_mat_hold_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }