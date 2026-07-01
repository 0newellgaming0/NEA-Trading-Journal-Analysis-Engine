# =========================================================
# WYCKOFF SPRING FAMILY MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# PROGRESSIVE EVENT VERSION (SEED REQUIRED)
# SPRING → TEST → LPS → SOS
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("wyckoff_spring")


# =========================================================
# DETECTOR (SPRING SEED)
# =========================================================
def detect_spring_seed(c1, c2, f):

    try:
        h1, l1, c1c = f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        h2, l2, c2c = f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [h1, l1, c1c, h2, l2, c2c]):
        return {"detected": False}

    spring = (l2 < l1 and c2c > l1)

    if not spring:
        return {"detected": False}

    # =====================================================
    # FIX: ALWAYS PRESERVE STRUCTURE LEVELS (EVEN IF FAILED LATER)
    # =====================================================
    return {
        "detected": True,
        "type": "Wyckoff Spring (Seed)",
        "direction": "Bullish",

        # STRUCTURE (NEVER LOSE THESE)
        "support": l1,
        "resistance": h1,

        # EVENT METRICS
        "spring_low": l2,
        "spring_close": c2c,

        "stage": "SEED",

        # =================================================
        # FIX: STRUCTURE LOCK (CRITICAL FOR DOWNSTREAM NODES)
        # =================================================
        "structure_locked": True
    }


# =========================================================
# DETECTOR (TEST)
# =========================================================
def detect_spring_test(event, candle, f):

    try:
        close = f(candle["Close"])
        low = f(candle["Low"])
    except Exception:
        return {"stage": "TEST", "valid": False}

    if close is None or low is None:
        return {"stage": "TEST", "valid": False}

    # TEST = revisit support without breakdown
    if low >= event.get("support") and close > event.get("support"):
        return {"stage": "TEST", "valid": True}

    return {"stage": "TEST", "valid": False}


# =========================================================
# DETECTOR (LPS)
# =========================================================
def detect_lps(event, candle, f):

    try:
        close = f(candle["Close"])
        low = f(candle["Low"])
    except Exception:
        return {"stage": "LPS", "valid": False}

    support = event.get("support")
    resistance = event.get("resistance")

    if support is None or resistance is None:
        return {"stage": "LPS", "valid": False}

    higher_low = low > support
    strong_close = close > (support + resistance) / 2

    if higher_low and strong_close:
        return {"stage": "LPS", "valid": True}

    return {"stage": "LPS", "valid": False}


# =========================================================
# DETECTOR (SOS)
# =========================================================
def detect_sos(event, candle, f):

    try:
        close = f(candle["Close"])
    except Exception:
        return {"stage": "SOS", "valid": False}

    resistance = event.get("resistance")

    if resistance is None:
        return {"stage": "SOS", "valid": False}

    # SOS = breakout above resistance after LPS
    if close > resistance:
        return {"stage": "SOS", "valid": True}

    return {"stage": "SOS", "valid": False}


# =========================================================
# TRADE BUILDER
# =========================================================
def build_wyckoff_trade_state(event):

    # ONLY BUILD IF STRUCTURE IS AT LEAST LPS OR CONFIRMED
    status = event.get("status")

    if status not in ["LPS", "CONFIRMED"]:
        return {
            "trade_type": None,
            "direction": None,
            "entry": None,
            "stop": None,
            "invalidation": None,
            "target1": None,
            "target2": None,
            "failure": "Insufficient structure (needs LPS/SOS)",
            "interpretation": "Wyckoff structure incomplete for trade activation."
        }

    high = event.get("resistance")
    low = event.get("support")

    if high is None or low is None:
        return {
            "trade_type": None,
            "direction": None,
            "entry": None,
            "stop": None,
            "invalidation": None,
            "target1": None,
            "target2": None,
            "failure": "Invalid event data",
            "interpretation": "Missing structure levels."
        }

    rng = max(high - low, 1e-9)

    return {
        "trade_type": "ACCUMULATION",
        "direction": "LONG",
        "entry": high,
        "stop": low,
        "invalidation": low,

        "target1": high + rng,
        "target2": high + 2 * rng,

        "failure": f"Close below {low}",

        "interpretation": (
            "Wyckoff Spring → Test → LPS → SOS structure. "
            "Accumulation confirmed via liquidity sweep and expansion."
        )
    }


# =========================================================
# EVENT RULES (STATE MACHINE LIKE TASUKI)
# =========================================================
def wyckoff_event_rules(event, candle, f):

    status = event.get("status")

    close = f(candle["Close"])
    high = f(candle["High"])
    low = f(candle["Low"])

    support = event.get("support")
    resistance = event.get("resistance")

    if support is None or resistance is None:
        return None

    # =====================================================
    # HARD INVALIDATION
    # =====================================================
    if close < support:
        return "FAIL"

    # =====================================================
    # SEED STATE
    # =====================================================
    if status == "SEED":
        return "TEST"

    # =====================================================
    # TEST STATE
    # =====================================================
    if status == "TEST":

        if low > support and close > (support + resistance) / 2:
            return "LPS"

        return None

    # =====================================================
    # LPS STATE
    # =====================================================
    if status == "LPS":

        if close > resistance:
            return "SOS"

        return None

    # =====================================================
    # SOS STATE
    # =====================================================
    if status == "SOS":

        return None

    return None


# =========================================================
# MAIN ANALYZER (TASUKI STRUCTURE MATCHED)
# =========================================================
def analyze_wyckoff_c(df, event_store, f=float):

    logger.info("[WYCKOFF] analyze_wyckoff() called")

    latest_pattern = None

    # =====================================================
    # PASS 1: SPRING SEED DETECTION
    # =====================================================
    for i in range(len(df) - 1, 0, -1):

        c1 = df.iloc[i - 1]
        c2 = df.iloc[i]

        seed = detect_spring_seed(c1, c2, f)

        if seed.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": seed["type"],
                "direction": seed["direction"],

                # =================================================
                # STRUCTURE (MUST ALWAYS BE PRESERVED)
                # =================================================
                "support": seed["support"],
                "resistance": seed["resistance"],

                "spring_low": seed["spring_low"],
                "spring_close": seed["spring_close"],

                "index": i - 1,
                "date": extract_event_date(df, i),

                "status": "SEED",
                "days_active": 0,
                "status_reason": "Wyckoff Spring Seed detected"
            }
            break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =====================================================
    # VALIDATION LOOP (STATE MACHINE)
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        # =================================================
        # STOP PROCESSING IF TERMINAL STATE REACHED
        # =================================================
        if latest_pattern["status"] in ["CONFIRMED", "FAILED"]:
            break

        action = wyckoff_event_rules(latest_pattern, candle, f)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        # =================================================
        # STATE TRANSITIONS (STRICT ORDER ENFORCED)
        # =================================================

        if action == "TEST" and latest_pattern["status"] == "SEED":
            latest_pattern["status"] = "TEST"

        elif action == "LPS" and latest_pattern["status"] in ["TEST", "SEED"]:
            latest_pattern["status"] = "LPS"

        elif action == "SOS" and latest_pattern["status"] == "LPS":
            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Spring invalidated (support broken)"
            break

    # =====================================================
    # TRADE BUILD (SAFE GUARD)
    # =====================================================
    trade = build_wyckoff_trade_state(latest_pattern)

    # =====================================================
    # REGIME LOGIC (CLEAN STATE RESOLUTION)
    # =====================================================
    status = latest_pattern["status"]

    if status == "CONFIRMED":
        regime = "ACCUMULATION"

    elif status == "FAILED":
        regime = "DISTRIBUTION_RISK"

    elif status in ["SEED", "TEST", "LPS"]:
        regime = "ACCUMULATION_IN_PROGRESS"

    else:
        regime = "TRANSITION"

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": regime
    }