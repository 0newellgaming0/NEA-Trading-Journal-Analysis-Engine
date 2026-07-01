# =========================================================
# WYCKOFF EXPANSION MODULE (FIXED STATE AUTHORITY)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("wyckoff_expansion")


# =========================================================
# DETECTOR (LPS SEED BASE - PURE STRUCTURE ONLY)
# =========================================================
def detect_lps_seed(c1, c2, f):

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

    lps = (
        l2 > support and
        c2c > midpoint and
        c2c < resistance * 1.01
    )

    if not lps:
        return {"detected": False}

    return {
        "detected": True,
        "type": "Wyckoff LPS (Seed)",
        "direction": "Bullish",

        "support": support,
        "resistance": resistance,

        "high": h2,
        "low": l2,
        "close": c2c,

        "stage": "LPS"
    }


# =========================================================
# DETECTOR (SOS - SIGNAL ONLY, NO STATE AUTHORITY)
# =========================================================
def detect_sos(event, candle, f):

    close = f(candle["Close"])
    resistance = event.get("resistance")

    if resistance is None:
        return {"valid": False}

    if close > resistance:
        return {"valid": True, "signal": "SOS"}

    return {"valid": False}


# =========================================================
# DETECTOR (MARKUP - SIGNAL ONLY)
# =========================================================
def detect_markup(event, candle, f):

    close = f(candle["Close"])
    resistance = event.get("resistance")

    if resistance is None:
        return {"valid": False}

    if close > resistance * 1.01:
        return {"valid": True, "signal": "MARKUP"}

    return {"valid": False}


# =========================================================
# DETECTOR (BUYING CLIMAX - SIGNAL ONLY)
# =========================================================
def detect_buying_climax(event, candle, f):

    high = f(candle["High"])
    low = f(candle["Low"])
    close = f(candle["Close"])
    open_ = f(candle["Open"])

    resistance = event.get("resistance")

    if resistance is None:
        return {"valid": False}

    body = abs(close - open_)
    rng = max(high - low, 1e-9)

    bc = (
        high > resistance * 1.03 and
        close < high and
        body / rng < 0.4
    )

    return {"valid": bc, "signal": "BUYING_CLIMAX" if bc else None}


# =========================================================
# TRADE BUILDER
# =========================================================
def build_wyckoff_expansion_trade(event):

    if event.get("status") not in ["MARKUP", "SOS"]:
        return {
            "trade_type": None,
            "direction": None,
            "entry": None,
            "stop": None,
            "invalidation": None,
            "target1": None,
            "target2": None,
            "failure": "Structure incomplete (needs SOS/Markup)",
            "interpretation": "Expansion not confirmed."
        }

    high = event["resistance"]
    low = event["support"]
    rng = max(high - low, 1e-9)

    return {
        "trade_type": "MARKUP_EXPANSION",
        "direction": "LONG",

        "entry": high,
        "stop": low,
        "invalidation": low,

        "target1": high + rng,
        "target2": high + 2 * rng,

        "failure": f"Close below {low}",

        "interpretation": (
            "Wyckoff LPS → SOS → Markup sequence detected. "
            "Expansion phase active until Buying Climax exhaustion."
        )
    }


# =========================================================
# STATE MACHINE (SINGLE SOURCE OF TRUTH)
# =========================================================
def wyckoff_expansion_rules(event, candle, f):

    status = event.get("status")

    close = f(candle["Close"])
    support = event["support"]
    resistance = event["resistance"]

    # GLOBAL INVALIDATION
    if close < support:
        return "FAIL"

    # LPS → SOS
    if status == "LPS":
        if close > resistance:
            return "SOS"

    # SOS → MARKUP
    if status == "SOS":
        if close > resistance * 1.01:
            return "MARKUP"

    # MARKUP → BUYING CLIMAX
    if status == "MARKUP":
        if detect_buying_climax(event, candle, f)["valid"]:
            return "BC"

    # BUYING CLIMAX → FAIL (exhaustion)
    if status == "BUYING_CLIMAX":
        if close < resistance:
            return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (FIXED STATE AUTHORITY)
# =========================================================
def analyze_wyckoff_expansion(df, event_store, f=float):

    logger.info("[WYCKOFF EXPANSION] analyze_wyckoff_expansion() called")

    latest_pattern = None

    # PASS 1: DETECT SEED
    for i in range(len(df) - 1, 0, -1):

        c1 = df.iloc[i - 1]
        c2 = df.iloc[i]

        seed = detect_lps_seed(c1, c2, f)

        if seed.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": seed["type"],
                "direction": seed["direction"],

                "support": seed["support"],
                "resistance": seed["resistance"],

                "high": seed["high"],
                "low": seed["low"],
                "close": seed["close"],

                "index": i - 1,
                "date": extract_event_date(df, i),

                "status": "LPS",
                "days_active": 0,
                "status_reason": "LPS seed detected"
            }
            break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # PASS 2: STATE MACHINE (NO DETECTOR OVERRIDES)
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        action = wyckoff_expansion_rules(latest_pattern, candle, f)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "SOS":
            if latest_pattern["status"] == "LPS":
                latest_pattern["status"] = "SOS"
                latest_pattern["sos_date"] = extract_event_date(df, i)

        elif action == "MARKUP":
            if latest_pattern["status"] == "SOS":
                latest_pattern["status"] = "MARKUP"

        elif action == "BC":
            latest_pattern["status"] = "BUYING_CLIMAX"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

        elif action == "FAIL":
            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Expansion invalidated"
            break

    trade = build_wyckoff_expansion_trade(latest_pattern)

    if latest_pattern["status"] == "MARKUP":
        regime = "MARKUP"
    elif latest_pattern["status"] == "BUYING_CLIMAX":
        regime = "DISTRIBUTION_RISK"
    elif latest_pattern["status"] == "FAILED":
        regime = "DISTRIBUTION_RISK"
    else:
        regime = "TRANSITION"

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": regime
    }