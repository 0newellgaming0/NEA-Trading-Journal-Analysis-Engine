import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("wyckoff_transition")


# =========================================================
# PHASE DETECTOR (TEST → LPS)
# =========================================================
def detect_test_lps_structure(c1, c2, f):

    try:
        h1, l1, c1c = f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        h2, l2, c2c = f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [h1, l1, c1c, h2, l2, c2c]):
        return {"detected": False}

    support = l1
    resistance = h1
    midpoint = (support + resistance) / 2

    # =====================================================
    # TEST STRUCTURE
    # =====================================================
    test = (
        l2 >= support and
        c2c > support and
        c2c < midpoint
    )

    # =====================================================
    # LPS STRUCTURE
    # =====================================================
    lps = (
        l2 > support and
        c2c > midpoint and
        c2c < resistance * 1.02
    )

    # =====================================================
    # FIX: TYPE MUST BE STRUCTURAL ONLY (NOT STATE)
    # =====================================================

    if lps:
        return {
            "detected": True,

            # FIX: type is STRUCTURE, not state
            "type": "Wyckoff Transition Structure",

            "structure_type": "LPS_CANDIDATE",
            "stage": "STRUCTURE",

            "support": support,
            "resistance": resistance,
            "high": h2,
            "low": l2,
            "close": c2c
        }

    if test:
        return {
            "detected": True,
            "type": "Wyckoff Transition Structure",
            "structure_type": "TEST_CANDIDATE",
            "stage": "STRUCTURE",

            "support": support,
            "resistance": resistance,
            "high": h2,
            "low": l2,
            "close": c2c
        }

    return {"detected": False}


# =========================================================
# SOS DETECTOR (BREAKOUT CONFIRMATION)
# =========================================================
def detect_sos(event, candle, f):

    close = f(candle["Close"])
    high = f(candle["High"])

    # MUST REQUIRE LPS EXISTENCE BEFORE SOS VALIDATION
    if event.get("status") not in ["LPS", "CONFIRMED"]:
        return {"detected": False}

    if close > event["resistance"]:
        return {
            "detected": True,
            "stage": "SOS",
            "close": close,
            "high": high
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (MARKUP EXPANSION)
# =========================================================
def build_wyckoff_markup_trade(event):

    # ONLY VALID AFTER LPS OR CONFIRMED
    if event.get("status") not in ["LPS", "CONFIRMED"]:
        return {
            "trade_type": None,
            "direction": None,
            "entry": None,
            "stop": None,
            "invalidation": None,
            "target1": None,
            "target2": None,
            "failure": "Insufficient structure (requires LPS/SOS)",
            "interpretation": "Structure incomplete for markup trade."
        }

    high = event["resistance"]
    low = event["support"]
    rng = max(high - low, 1e-9)

    return {
        "trade_type": "MARKUP",
        "direction": "LONG",

        "entry": high,
        "stop": low,
        "invalidation": low,

        "target1": high + rng,
        "target2": high + 2 * rng,

        "failure": f"Close below {low}",

        "interpretation": (
            "Wyckoff Test → LPS → SOS sequence completed. "
            "Markup phase initiated with breakout confirmation."
        )
    }


# =========================================================
# EVENT RULES (STATE MACHINE)
# =========================================================
def wyckoff_transition_rules(event, candle, f):

    status = event.get("status")

    close = f(candle["Close"])
    low = f(candle["Low"])

    support = event["support"]
    resistance = event["resistance"]

    # =====================================================
    # GLOBAL INVALIDATION
    # =====================================================
    if close < support:
        return "FAIL"

    # =====================================================
    # TEST STATE
    # =====================================================
    if status == "TEST":

        # MUST SHOW HOLDING BEHAVIOR BEFORE LPS
        if close > support and close > (support + resistance) / 2:
            return "LPS"

    # =====================================================
    # LPS STATE
    # =====================================================
    if status == "LPS":

        # REQUIRE TRUE BREAKOUT CONFIRMATION
        if close > resistance:
            return "SOS"

    # =====================================================
    # SOS STATE
    # =====================================================
    if status == "SOS":

        return "CONFIRMED"

    return None


# =========================================================
# MAIN ANALYZER (TASUKI-STYLE STRUCTURE)
# =========================================================
def analyze_wyckoff_t(df, event_store, f=float):

    logger.info("[WYCKOFF TRANSITION] analyze_wyckoff_transition() called")

    latest_pattern = None

    # =====================================================
    # PASS 1
    # =====================================================
    for i in range(len(df) - 1, 0, -1):

        c1 = df.iloc[i - 1]
        c2 = df.iloc[i]

        detected = detect_test_lps_structure(c1, c2, f)

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "stage": detected["stage"],

                "support": detected["support"],
                "resistance": detected["resistance"],

                "high": detected["high"],
                "low": detected["low"],
                "close": detected["close"],

                "index": i - 1,
                "date": extract_event_date(df, i),

                "status": "SEED",
                "days_active": 0,
                "status_reason": f"{detected['stage']} detected"
            }
            break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =====================================================
    # PASS 2 STATE MACHINE
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        action = wyckoff_transition_rules(latest_pattern, candle, f)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "LPS":
            latest_pattern["status"] = "LPS"

        elif action == "SOS":
            latest_pattern["status"] = "SOS"

        elif action == "CONFIRMED":
            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Structure invalidated"
            break

    trade = build_wyckoff_markup_trade(latest_pattern)

    if latest_pattern["status"] == "CONFIRMED":
        regime = "MARKUP"
    elif latest_pattern["status"] == "FAILED":
        regime = "DISTRIBUTION_RISK"
    else:
        regime = "TRANSITION"

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": regime
    }