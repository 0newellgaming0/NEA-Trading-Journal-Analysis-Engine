# =========================================================
# TLINE MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# ENHANCED - PINBAR STRUCTURE PARITY PRESERVED
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("doji Sandwiches")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0



# =========================================================
# REQUIRED SEED DETECTOR
# =========================================================
def detect_doji_sandwich_seed(c1, c2, c3, f):

    logger.debug("[DOJI] seed detection called")

    # c3 intentionally unused
    # maintained for detector parity

    try:
        o1 = f(c1["Open"])
        h1 = f(c1["High"])
        l1 = f(c1["Low"])
        c1c = f(c1["Close"])

        o2 = f(c2["Open"])
        h2 = f(c2["High"])
        l2 = f(c2["Low"])
        c2c = f(c2["Close"])

    except Exception:
        return {"detected": False}

    rng2 = max(h2 - l2, 1e-9)
    body2 = abs(c2c - o2)

    is_doji = body2 <= (rng2 * 0.10)

    if not is_doji:
        return {"detected": False}

    upper_shadow = h2 - max(o2, c2c)
    lower_shadow = min(o2, c2c) - l2

    if (
        upper_shadow > rng2 * 0.25 and
        lower_shadow > rng2 * 0.25
    ):
        doji_type = "Long-Legged Doji"

    elif lower_shadow > upper_shadow * 2:
        doji_type = "Dragonfly Doji"

    elif upper_shadow > lower_shadow * 2:
        doji_type = "Gravestone Doji"

    else:
        doji_type = "Standard Doji"

    if c1c > o1:

        return {
            "detected": True,
            "type": f"Bullish {doji_type} Sandwich (Seed)",
            "direction": "Bullish",
            "doji_type": doji_type,
            "high": max(h1, h2),
            "low": min(l1, l2),
            "stage": "SEED"
        }

    if c1c < o1:

        return {
            "detected": True,
            "type": f"Bearish {doji_type} Sandwich (Seed)",
            "direction": "Bearish",
            "doji_type": doji_type,
            "high": max(h1, h2),
            "low": min(l1, l2),
            "stage": "SEED"
        }

    return {"detected": False}
    
# =========================================================
# FULL PATTERN DETECTOR (CONFIRMATION)
# =========================================================
def detect_doji_sandwich(c1, c2, c3, f):

    logger.debug("[DOJI] detect_doji_sandwich() called")

    try:

        o1 = f(c1["Open"])
        h1 = f(c1["High"])
        l1 = f(c1["Low"])
        c1c = f(c1["Close"])

        o2 = f(c2["Open"])
        h2 = f(c2["High"])
        l2 = f(c2["Low"])
        c2c = f(c2["Close"])

        o3 = f(c3["Open"])
        h3 = f(c3["High"])
        l3 = f(c3["Low"])
        c3c = f(c3["Close"])

    except Exception as e:

        return {
            "detected": False,
            "error": str(e)
        }

    if any(
        v is None
        for v in [
            o1, h1, l1, c1c,
            o2, h2, l2, c2c,
            o3, h3, l3, c3c
        ]
    ):
        return {"detected": False}

    # =====================================================
    # DOJI CLASSIFICATION
    # =====================================================

    rng2 = max(h2 - l2, 1e-9)

    body2 = abs(c2c - o2)

    is_doji = body2 <= (rng2 * 0.10)

    if not is_doji:
        return {"detected": False}

    upper_shadow = h2 - max(o2, c2c)
    lower_shadow = min(o2, c2c) - l2

    doji_type = "Standard Doji"

    if lower_shadow > upper_shadow * 2:
        doji_type = "Dragonfly Doji"

    elif upper_shadow > lower_shadow * 2:
        doji_type = "Gravestone Doji"

    elif (
        upper_shadow > rng2 * 0.25 and
        lower_shadow > rng2 * 0.25
    ):
        doji_type = "Long-Legged Doji"

    # =====================================================
    # BIGALOW BULLISH SANDWICH
    # =====================================================

    bullish = (
        c1c > o1 and
        c3c > o3
    )

    # =====================================================
    # BIGALOW BEARISH SANDWICH
    # =====================================================

    bearish = (
        c1c < o1 and
        c3c < o3
    )

    high = max(h1, h2, h3)
    low = min(l1, l2, l3)

    # =====================================================
    # RESULT
    # =====================================================

    if bullish:

        return {
            "detected": True,
            "type": f"Bullish {doji_type} Sandwich",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "close": c3c,
            "doji_type": doji_type
        }

    if bearish:

        return {
            "detected": True,
            "type": f"Bearish {doji_type} Sandwich",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "close": c3c,
            "doji_type": doji_type
        }

    return {"detected": False}    

# =========================================================
# INTERPRETATION ENGINE
# =========================================================
def interpret_doji_sandwich(event):

    direction = event.get("direction")
    ptype = event.get("type", "")

    interpretations = []

    # =====================================================
    # BIGALOW STRUCTURE INTERPRETATION
    # =====================================================

    if "Dragonfly" in ptype:

        interpretations.append(
            "Dragonfly Doji rejection detected: sellers forced price lower but failed to maintain control."
        )

    elif "Gravestone" in ptype:

        interpretations.append(
            "Gravestone Doji rejection detected: buyers forced price higher but failed to maintain control."
        )

    elif "Long-Legged" in ptype:

        interpretations.append(
            "Long-Legged Doji detected: significant two-sided battle occurred before directional resolution."
        )

    else:

        interpretations.append(
            "Standard Doji equilibrium detected between directional candles."
        )

    # =====================================================
    # SANDWICH LOGIC
    # =====================================================

    interpretations.append(
        "Middle-candle indecision trapped opposing participants before directional resolution."
    )

    # =====================================================
    # DIRECTIONAL PSYCHOLOGY
    # =====================================================

    if direction == "Bullish":

        interpretations.append(
            "Bullish control maintained before and after equilibrium candle."
        )

        interpretations.append(
            "Institutional accumulation behavior suggested by failed bearish follow-through."
        )

    elif direction == "Bearish":

        interpretations.append(
            "Bearish control maintained before and after equilibrium candle."
        )

        interpretations.append(
            "Institutional distribution behavior suggested by failed bullish follow-through."
        )

    # =====================================================
    # EVENT STATUS CONTEXT
    # =====================================================

    status = event.get("status")

    if status == "SEED":

        interpretations.append(
            "Early continuation structure detected but directional confirmation remains pending."
        )

    elif status == "CONFIRMED":

        interpretations.append(
            "Pattern successfully confirmed through post-formation price acceptance."
        )

    elif status == "FAILED":

        interpretations.append(
            "Pattern failed due to loss of directional acceptance after formation."
        )

    return " | ".join(interpretations)
    
# =========================================================
# EVENT RULES
# =========================================================
def doji_sandwich_event_rules(event, candle, close, high, low):

    status = event.get("status")

    if event.get("days_active", 0) > 15:
        return "EXPIRE"

    if status == "SEED":

        if event["direction"] == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    elif status == "PENDING":

        if event["direction"] == "Bullish":

            if close > event["high"]:
                return "CONFIRM"

            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":

            if close < event["low"]:
                return "CONFIRM"

            if close > event["high"]:
                return "FAIL"

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish" and close < event["low"]:
            return "FAIL"

        if event["direction"] == "Bearish" and close > event["high"]:
            return "FAIL"

    return None


# =========================================================
# TRADE BUILDER
# =========================================================
def build_doji_sandwich_trade_state(event):

    high = event["high"]
    low = event["low"]

    rng = max(high - low, 1e-9)

    if event["direction"] == "Bullish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - rng * 0.1,
            "invalidation": low,
            "target1": high + rng,
            "target2": high + rng * 2,
            "failure": f"Close below {low}",
            "interpretation": interpret_doji_sandwich(event)
        }

    if event["direction"] == "Bearish":

        return {
            "trade_type": "CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + rng * 0.1,
            "invalidation": high,
            "target1": low - rng,
            "target2": low - rng * 2,
            "failure": f"Close above {high}",
            "interpretation": interpret_doji_sandwich(event)
        }

    return {}
    
# =========================================================
# MAIN ANALYZER (SEED REQUIRED PATH)
# =========================================================
def analyze_doji_sandwich(df, event_store, f=float):

    logger.info("[DOJI] analyze_doji_sandwich() called")

    latest_pattern = None

    # =====================================================
    # PASS 1 - FULL PATTERN DETECTION
    # =====================================================
    for i in range(len(df) - 1, 1, -1):

        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]

        detected = detect_doji_sandwich(
            c1,
            c2,
            c3,
            f
        )

        if detected.get("detected"):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": detected["type"],
                "direction": detected["direction"],
                "doji_type": detected.get("doji_type"),
                "high": detected["high"],
                "low": detected["low"],
                "close": detected["close"],
                "index": i - 2,
                "date": extract_event_date(df, i),
                "status": "PENDING",
                "status_reason": "Full Doji Sandwich detected"
            }

            break

    # =====================================================
    # PASS 2 - SEED DETECTION
    # =====================================================
    if latest_pattern is None:

        for i in range(len(df) - 1, 1, -1):

            c1 = df.iloc[i - 2]
            c2 = df.iloc[i - 1]
            c3 = df.iloc[i]

            seed = detect_doji_sandwich_seed(
                c1,
                c2,
                c3,
                f
            )

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
                    "status_reason": "Early Doji Sandwich structure forming"
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

        action = doji_sandwich_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        latest_pattern["days_active"] = (
            i - latest_pattern["index"]
        )

        if action == "CONFIRM":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(
                df,
                i
            )
            latest_pattern["status_reason"] = (
                "Doji Sandwich confirmed"
            )

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(
                df,
                i
            )
            latest_pattern["status_reason"] = (
                "Doji Sandwich invalidated"
            )

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(
                df,
                i
            )
            latest_pattern["status_reason"] = "Expired"

            break

    # =====================================================
    # INTERPRETATION
    # =====================================================
    latest_pattern["interpretation"] = (
        interpret_doji_sandwich(
            latest_pattern
        )
    )

    # =====================================================
    # TRADE BUILD
    # =====================================================
    trade = build_doji_sandwich_trade_state(
        latest_pattern
    )

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }