import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("bw_ao_ac")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# AO CALCULATION
# =========================================================
def calculate_ao(df, i):

    if i < 33:
        return 0.0

    median = (df["High"] + df["Low"]) / 2.0

    fast = median.iloc[i - 4:i + 1].mean()
    slow = median.iloc[i - 33:i + 1].mean()

    return fast - slow


# =========================================================
# AC CALCULATION
# =========================================================
def calculate_ac(df, i):

    if i < 37:
        return 0.0

    ao_vals = [calculate_ao(df, j) for j in range(i - 4, i + 1)]

    return ao_vals[-1] - sum(ao_vals) / len(ao_vals)


# =========================================================
# SIGNAL RESOLUTION (AO/AC ONLY)
# =========================================================
def resolve_aoac_signal(ao, prev_ao, ac, prev_ac):

    # =====================================================
    # AO ZERO CROSS EVENTS
    # =====================================================
    if prev_ao <= 0 and ao > 0:
        return "AO_ZERO_CROSS_BUY"

    if prev_ao >= 0 and ao < 0:
        return "AO_ZERO_CROSS_SELL"

    # =====================================================
    # AC ZERO CROSS EVENTS
    # =====================================================
    if prev_ac <= 0 and ac > 0:
        return "AC_ZERO_CROSS_BUY"

    if prev_ac >= 0 and ac < 0:
        return "AC_ZERO_CROSS_SELL"

    # =====================================================
    # MOMENTUM ZONES
    # =====================================================
    if ao > 0 and ac > 0:
        return "GREEN_ZONE_BUY"

    if ao < 0 and ac < 0:
        return "RED_ZONE_SELL"

    return None


# =========================================================
# EVENT RULES (STRUCTURE ONLY)
# =========================================================
def aoac_event_rules(event, close):

    ptype = event.get("type")
    direction = event.get("direction")

    if direction not in ["Bullish", "Bearish"]:
        return None

    if ptype in ["AO_ZERO_CROSS_BUY", "AC_ZERO_CROSS_BUY", "GREEN_ZONE_BUY"]:
        return "BUY_CONTEXT"

    if ptype in ["AO_ZERO_CROSS_SELL", "AC_ZERO_CROSS_SELL", "RED_ZONE_SELL"]:
        return "SELL_CONTEXT"

    return None


# =========================================================
# TRADE BUILDER (AO/AC ONLY EXECUTION MODEL)
# =========================================================
def build_aoac_trade_state(event):

    if event.get("direction") not in ["Bullish", "Bearish"]:
        return {}

    high = event.get("high", 0)
    low = event.get("low", 0)
    close = event.get("close", 0)

    rng = max(high - low, 1e-9)
    signal_type = event.get("type", "")

    # =====================================================
    # LONG TRADES
    # =====================================================
    if "BUY" in signal_type:

        return {
            "trade_type": "AOAC_EXECUTION_MODEL",
            "direction": "LONG",

            "entry": high,
            "stop": low - (0.10 * rng),
            "invalidation": low,

            "target1": high + rng,
            "target2": high + (2 * rng),

            "failure": "AO/AC momentum shifts bearish",

            "signal_source": signal_type,
            "interpretation": event.get("interpretation", "")
        }

    # =====================================================
    # SHORT TRADES
    # =====================================================
    if "SELL" in signal_type:

        return {
            "trade_type": "AOAC_EXECUTION_MODEL",
            "direction": "SHORT",

            "entry": low,
            "stop": high + (0.10 * rng),
            "invalidation": high,

            "target1": low - rng,
            "target2": low - (2 * rng),

            "failure": "AO/AC momentum shifts bullish",

            "signal_source": signal_type,
            "interpretation": event.get("interpretation", "")
        }

    return {}


# =========================================================
# MAIN ANALYZER (VWAP-STYLE ARCHITECTURE)
# =========================================================
def analyze_alligator(df, event_store=None):

    logger.info("[AO/AC] analyzer started")

    latest = None

    # =====================================================
    # STEP 1 - FIND MOST RECENT SIGNAL
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        ao = calculate_ao(df, i)
        ac = calculate_ac(df, i)

        prev_ao = calculate_ao(df, i - 1)
        prev_ac = calculate_ac(df, i - 1)

        signal = resolve_aoac_signal(ao, prev_ao, ac, prev_ac)

        if not signal:
            continue

        zone = (
            "GREEN_ZONE" if ao > 0 and ac > 0 else
            "RED_ZONE" if ao < 0 and ac < 0 else
            "GRAY_ZONE"
        )

        latest = {
            "id": i,
            "detected": True,

            "type": signal,
            "direction": "Bullish" if "BUY" in signal else "Bearish",

            # =====================================================
            # CRITICAL FIX: PRICE CONTEXT (REQUIRED FOR TRADE ENGINE)
            # =====================================================
            "high": f(df["High"].iloc[i]),
            "low": f(df["Low"].iloc[i]),
            "close": f(df["Close"].iloc[i]),

            "ao": ao,
            "ac": ac,
            "zone": zone,

            "momentum_strength": abs(ao) + abs(ac),

            "index": i,
            "date": extract_event_date(df, i),

            "status": "PENDING",
            "resolved_date": None,
            "days_active": 0,

            "interpretation": "Bill Williams AO/AC Signal"
        }

        break

    # =====================================================
    # NO EVENT FOUND
    # =====================================================
    if latest is None:

        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # =====================================================
    # STEP 2 - FORWARD VALIDATION (FAIL ONLY)
    # =====================================================
    for i in range(latest["index"] + 1, len(df)):

        latest["days_active"] = i - latest["index"]

        ao = calculate_ao(df, i)
        ac = calculate_ac(df, i)

        # ONLY FAILURE LOGIC (NO CONFIRM LOGIC)
        if latest["direction"] == "Bullish" and ao < 0:
            latest["status"] = "FAILED"
            latest["resolved_date"] = extract_event_date(df, i)
            break

        if latest["direction"] == "Bearish" and ao > 0:
            latest["status"] = "FAILED"
            latest["resolved_date"] = extract_event_date(df, i)
            break

    # =====================================================
    # STEP 3 - TRADE BUILD
    # =====================================================
    trade = build_aoac_trade_state(latest)

    # =====================================================
    # STEP 4 - REGIME
    # =====================================================
    regime = (
        "AOAC_BULL" if latest["direction"] == "Bullish"
        else "AOAC_BEAR"
    )

    latest["interpretation"] = f"Bill Williams AO/AC {regime}"

    # =====================================================
    # RETURN STRUCTURE (VWAP COMPATIBLE)
    # =====================================================
    return {
        "event": latest,
        "trade": trade,
        "regime": regime
    }