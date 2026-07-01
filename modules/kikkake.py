# =========================================================
# KIKKAKE FAMILY MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# PROGRESSIVE EVENT VERSION (SEED REQUIRED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("kikkake")


def detect_kikkake(c1, c2, c3, f):

    logger.debug("[KIKKAKE] detect_kikkake() called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except Exception as e:
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [o1, h1, l1, c1c, o2, h2, l2, c2c, o3, h3, l3, c3c]):
        return {"detected": False}

    # =====================================================
    # STRUCTURE DEFINITIONS
    # =====================================================

    body1 = abs(c1c - o1)
    body3 = abs(c3c - o3)

    # Mother candle (c1)
    # Inside candle (c2)
    inside_bar = (
        h2 < h1 and
        l2 > l1
    )

    if not inside_bar:
        return {"detected": False}

    # =====================================================
    # BULLISH KIKKAKE
    # =====================================================
    # 1. Bearish mother candle
    # 2. Inside bar forms
    # 3. False breakdown below inside bar low
    # 4. Reclaim back inside range
    # 5. Close shows rejection / stabilization
    # =====================================================

    bullish = (
        c1c < o1 and
        l3 < l2 and              # false downside break
        c3c > l2 and             # reclaim above inside low
        c3c < h2                 # still within inside bar range (controlled reclaim)
    )

    # =====================================================
    # BEARISH KIKKAKE
    # =====================================================
    # 1. Bullish mother candle
    # 2. Inside bar forms
    # 3. False breakout above inside bar high
    # 4. Rejection back inside range
    # =====================================================

    bearish = (
        c1c > o1 and
        h3 > h2 and             # false upside break
        c3c < h2 and            # rejection below inside high
        c3c > l2                # stays inside range
    )

    if bullish:
        return {
            "detected": True,
            "type": "Bullish Kikkake",
            "direction": "Bullish",
            "high": h1,
            "low": l1,
            "close": c3c
        }

    if bearish:
        return {
            "detected": True,
            "type": "Bearish Kikkake",
            "direction": "Bearish",
            "high": h1,
            "low": l1,
            "close": c3c
        }

    return {"detected": False}


def detect_kikkake_seed(c1, c2, c3, f):

    logger.debug("[KIKKAKE] seed detection called")

    try:
        o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
        o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
        o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])
    except Exception:
        return {"detected": False}

    if any(v is None for v in [o1, h1, l1, c1c, o2, h2, l2, c2c, o3, h3, l3, c3c]):
        return {"detected": False}

    # =====================================================
    # STRUCTURE BASELINE
    # =====================================================

    inside_bar = (
        h2 < h1 and
        l2 > l1
    )

    if not inside_bar:
        return {"detected": False}

    body1 = abs(c1c - o1)
    body2 = abs(c2c - o2)

    # =====================================================
    # SEED LOGIC PRINCIPLE
    # We only detect EARLY trap formation:
    # - Inside bar exists (compression)
    # - First directional probe begins
    # - No breakout confirmation yet
    # =====================================================

    # =====================================================
    # BULLISH SEED (EARLY DOWNWARD LIQUIDITY GRAB)
    # =====================================================
    bullish_seed = (
        c1c < o1 and          # bearish mother candle
        l3 < l2 and           # probe below inside bar
        c3c > l2              # recovery back into range
    )

    # =====================================================
    # BEARISH SEED (EARLY UPWARD LIQUIDITY GRAB)
    # =====================================================
    bearish_seed = (
        c1c > o1 and          # bullish mother candle
        h3 > h2 and           # probe above inside bar
        c3c < h2              # rejection back into range
    )

    if bullish_seed:
        return {
            "detected": True,
            "type": "Bullish Kikkake (Seed)",
            "direction": "Bullish",
            "high": h1,
            "low": l1,
            "stage": "SEED"
        }

    if bearish_seed:
        return {
            "detected": True,
            "type": "Bearish Kikkake (Seed)",
            "direction": "Bearish",
            "high": h1,
            "low": l1,
            "stage": "SEED"
        }

    return {"detected": False}

# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_kikkake(event):

    direction = event.get("direction")
    ptype = event.get("type", "")
    status = event.get("status")

    interpretations = []

    # =====================================================
    # CORE STRUCTURE LOGIC (FALSE BREAKOUT MECHANISM)
    # =====================================================

    if "Seed" in ptype:

        interpretations.append(
            "Early Kikkake seed detected: inside-bar compression with developing false breakout conditions."
        )

    else:

        interpretations.append(
            "Kikkake structure detected: inside-bar compression followed by directional liquidity sweep and re-entry."
        )

    # =====================================================
    # REVERSAL MECHANISM CORE (KIKKAKE IDENTITY)
    # =====================================================

    interpretations.append(
        "Market attempted a breakout from compression but failed to sustain acceptance beyond the mother candle range."
    )

    interpretations.append(
        "This reflects a liquidity trap where stop orders were triggered before reversal back into the prior range."
    )

    # =====================================================
    # DIRECTIONAL PSYCHOLOGY
    # =====================================================

    if direction == "Bullish":

        interpretations.append(
            "Bullish reversal pressure: downside liquidity sweep absorbed, followed by strong recovery into range."
        )

        interpretations.append(
            "Institutional accumulation behavior implied after failed breakdown."
        )

    elif direction == "Bearish":

        interpretations.append(
            "Bearish reversal pressure: upside liquidity sweep rejected, followed by rejection back into range."
        )

        interpretations.append(
            "Institutional distribution behavior implied after failed breakout."
        )

    # =====================================================
    # STATE CONTEXT
    # =====================================================

    if status == "SEED":

        interpretations.append(
            "Early formation phase: breakout attempt not yet fully confirmed; structure still developing."
        )

    elif status == "PENDING":

        interpretations.append(
            "Structure is active but unresolved; confirmation or failure still possible."
        )

    elif status == "CONFIRMED":

        interpretations.append(
            "Kikkake reversal confirmed through sustained rejection of breakout direction."
        )

    elif status == "FAILED":

        interpretations.append(
            "Kikkake structure invalidated due to sustained acceptance beyond breakout boundary."
        )

    # =====================================================
    # FINAL OUTPUT
    # =====================================================

    return " | ".join(interpretations)

def build_kikkake_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")

    # =====================================================
    # BULLISH KIKKAKE
    # (False downside break → reversal long)
    # =====================================================
    if direction == "Bullish":

        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",

            # breakout/reclaim entry
            "entry": high,

            # liquidity sweep stop (below structure low)
            "stop": low - rng * 0.10,

            "wick_stop": low,

            # structural invalidation
            "invalidation": low,

            # expansion targets
            "target1": high + rng,
            "target2": high + (rng * 2),

            "failure": f"Close below {low}",

            "interpretation":
                "Bullish Kikkake represents a failed downside liquidity sweep "
                "followed by structural reclaim and directional reversal."
        }

    # =====================================================
    # BEARISH KIKKAKE
    # (False upside break → reversal short)
    # =====================================================
    if direction == "Bearish":

        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",

            # breakdown entry
            "entry": low,

            # liquidity sweep stop (above structure high)
            "stop": high + rng * 0.10,

            "wick_stop": high,

            # structural invalidation
            "invalidation": high,

            # expansion targets
            "target1": low - rng,
            "target2": low - (rng * 2),

            "failure": f"Close above {high}",

            "interpretation":
                "Bearish Kikkake represents a failed upside liquidity sweep "
                "followed by rejection and directional breakdown."
        }

    return {}


def kikkake_event_rules(event, candle, close, high, low):

    status = event.get("status")
    direction = event.get("direction")

    # =====================================================
    # SEED STATE (INITIAL BREAK / TRAP RESOLUTION)
    # =====================================================
    if status == "SEED":

        # -------------------------------------------------
        # Bullish Kikkake
        # false downside break → reclaim above structure
        # -------------------------------------------------
        if direction == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        # -------------------------------------------------
        # Bearish Kikkake
        # false upside break → reject below structure
        # -------------------------------------------------
        elif direction == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    # =====================================================
    # PENDING STATE (STRUCTURE STILL FORMING / VALIDATING)
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
    # CONFIRMED STATE (POST-TRAP EXPANSION ONLY)
    # =====================================================
    elif status == "CONFIRMED":

        if direction == "Bullish":

            # invalidation only if structure fully breaks down
            if close < event["low"]:
                return "FAIL"

        elif direction == "Bearish":

            # invalidation only if structure fully breaks up
            if close > event["high"]:
                return "FAIL"

    return None


def analyze_kikkake(df, event_store, f=float):

    logger.info("[KIKKAKE] analyze_kikkake() called")

    latest_pattern = None

    # =====================================================
    # PASS 1: FULL PATTERN CONFIRMATION (PRIORITY LAYER)
    # =====================================================
    for i in range(len(df) - 1, 1, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        detected = detect_kikkake(c1, c2, c3, f)

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "high": detected["high"],
                "low": detected["low"],
                "index": i - 2,
                "date": extract_event_date(df, i),
                "status": "PENDING",
                "status_reason": "Full Kikkake detected"
            }
            break

    # =====================================================
    # PASS 2: SEED DETECTION (ONLY IF NO FULL PATTERN)
    # =====================================================
    if latest_pattern is None:

        for i in range(len(df) - 1, 1, -1):

            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            seed = detect_kikkake_seed(c1, c2, c3, f)

            if seed.get("detected"):

                latest_pattern = {
                    "id": 1,
                    "detected": True,
                    "type": seed["type"],
                    "direction": seed["direction"],
                    "high": seed["high"],
                    "low": seed["low"],
                    "index": i - 2,
                    "date": extract_event_date(df, i),
                    "status": "SEED",
                    "status_reason": "Early Kikkake structure forming"
                }
                break

    # =====================================================
    # NO PATTERN FOUND
    # =====================================================
    if latest_pattern is None:
        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # =====================================================
    # VALIDATION LOOP (STATE ENGINE)
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = kikkake_event_rules(
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
            latest_pattern["status_reason"] = "Kikkake confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Kikkake invalidated"
            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Expired"
            break

    # =====================================================
    # TRADE CONSTRUCTION
    # =====================================================
    trade = build_kikkake_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }