import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("elliott_wave")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# FRACTAL PIVOT DETECTOR (STRUCTURAL ONLY)
# =========================================================
def detect_fractal_pivot(df, i, window=2):

    if i < window or i >= len(df) - window:
        return None

    highs = [f(df["High"].iloc[j]) for j in range(i - window, i + window + 1)]
    lows = [f(df["Low"].iloc[j]) for j in range(i - window, i + window + 1)]

    high = f(df["High"].iloc[i])
    low = f(df["Low"].iloc[i])

    if low == min(lows):
        return {
            "type": "PIVOT_LOW",
            "direction": "BullishPivot",
            "price": low,
            "index": i
        }

    if high == max(highs):
        return {
            "type": "PIVOT_HIGH",
            "direction": "BearishPivot",
            "price": high,
            "index": i
        }

    return None


# =========================================================
# WAVE TYPE RESOLVER (SAFE + CAPPED)
# =========================================================
def resolve_wave_type(stage, direction, seed=False):

    stage = max(0, min(stage, 5))  # HARD CAP (fixes Wave 51 bug)
    suffix = "_SEED" if seed else ""

    if direction == "Bullish":
        if stage == 0:
            return f"ELLIOTT_SEED_BUY{suffix}"
        return f"WAVE_{stage}_BUY{suffix}"

    if direction == "Bearish":
        if stage == 0:
            return f"ELLIOTT_SEED_SELL{suffix}"
        return f"WAVE_{stage}_SELL{suffix}"

    return None


# =========================================================
# BUILD WAVE STRUCTURE (PIVOT-BASED)
# =========================================================
def build_wave_structure(pivots, start_index):

    if start_index + 5 >= len(pivots):
        return None

    return {
        "W1": (pivots[start_index], pivots[start_index + 1]),
        "W2": (pivots[start_index + 1], pivots[start_index + 2]),
        "W3": (pivots[start_index + 2], pivots[start_index + 3]),
        "W4": (pivots[start_index + 3], pivots[start_index + 4]),
        "W5": (pivots[start_index + 4], pivots[start_index + 5]),
    }


# =========================================================
# WAVE VALIDATION ENGINE (STRICT RULE SET)
# =========================================================
def validate_wave_1_3(w1, w2, w3, direction):

    p1 = w1["price"]
    p2 = w2["price"]
    p3 = w3["price"]

    # RULE 1: structural direction
    if direction == "Bullish":
        if not (p1 < p2 < p3):
            return False
    else:
        if not (p1 > p2 > p3):
            return False

    # RULE 2: Wave 3 cannot be shortest
    w1_size = abs(w2["price"] - w1["price"])
    w3_size = abs(w3["price"] - w2["price"])

    if w3_size < w1_size:
        return False

    return True


# =========================================================
# SEED DETECTOR
# =========================================================
def detect_elliott_seed(pivot):

    return {
        "detected": True,
        "wave_stage": 0,
        "type": "ELLIOTT_SEED",
        "direction": pivot["direction"].replace("Pivot", ""),
        "price": pivot["price"],
        "index": pivot["index"]
    }


# =========================================================
# TRADE BUILDER (STRUCTURAL MODEL)
# =========================================================
def build_elliott_trade_state(event):

    price = event["high"]
    low = event["low"]
    stage = event.get("wave_stage", 0)
    direction = event["direction"]

    if direction == "Bullish":

        return {
            "trade_type": "IMPULSE",
            "direction": "LONG",
            "entry": price,
            "stop": low * 0.98,
            "invalidation": low,
            "target1": price * (1.02 + stage * 0.01),
            "target2": price * (1.05 + stage * 0.02),
            "failure": "Wave structure invalidated below pivot",
            "interpretation": f"Elliott Wave {stage} bullish impulse structure"
        }

    if direction == "Bearish":

        return {
            "trade_type": "IMPULSE",
            "direction": "SHORT",
            "entry": price,
            "stop": price * 1.02,
            "invalidation": price,
            "target1": low * (0.98 - stage * 0.01),
            "target2": low * (0.95 - stage * 0.02),
            "failure": "Wave structure invalidated above pivot",
            "interpretation": f"Elliott Wave {stage} bearish impulse structure"
        }

    return {}


# =========================================================
# EVENT RULE ENGINE (NO BREAKOUT LOGIC)
# =========================================================
def elliott_event_rules(event, close):

    direction = event["direction"]
    price = event["high"]

    if direction == "Bullish":

        if close > price:
            return "CONFIRM"

        if close < event["low"] * 0.97:
            return "FAIL"

    if direction == "Bearish":

        if close < event["low"]:
            return "CONFIRM"

        if close > event["high"] * 1.03:
            return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (FULL STATE MACHINE FIXED)
# =========================================================
def analyze_elliott_waves(df, event_store, f=float):

    logger.info("[ELLIOTT] analyze_elliott_wave() called")

    pivots = []
    latest_pattern = None

    # =====================================================
    # PASS 1: BUILD PIVOTS
    # =====================================================
    for i in range(len(df)):
        pivot = detect_fractal_pivot(df, i)
        if pivot:
            pivots.append(pivot)

    # =====================================================
    # PASS 2: FIND VALID WAVE 1 STRUCTURE
    # =====================================================
    for i in range(len(pivots) - 3):

        w1, w2, w3 = pivots[i], pivots[i + 1], pivots[i + 2]

        direction = "Bullish" if w3["price"] > w1["price"] else "Bearish"

        if validate_wave_1_3(w1, w2, w3, direction):

            latest_pattern = {
                "id": 1,
                "detected": True,
                "type": resolve_wave_type(1, direction),
                "direction": direction,
                "wave_stage": 1,
                "high": max(w1["price"], w2["price"], w3["price"]),
                "low": min(w1["price"], w2["price"], w3["price"]),
                "index": w3["index"],
                "status": "WAVE_1",
                "status_reason": "Validated impulse structure"
            }
            break

    # =====================================================
    # PASS 3: SEED FALLBACK
    # =====================================================
    if latest_pattern is None and pivots:

        seed = detect_elliott_seed(pivots[-1])

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": resolve_wave_type(0, seed["direction"], seed=True),
            "direction": seed["direction"],
            "wave_stage": 0,
            "high": seed["price"],
            "low": seed["price"],
            "index": seed["index"],
            "status": "SEED",
            "status_reason": "Structure forming"
        }

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # =====================================================
    # PASS 4: PROGRESSION ENGINE (SAFE STATE MACHINE)
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        close = f(df["Close"].iloc[i])

        action = elliott_event_rules(latest_pattern, close)

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM":

            latest_pattern["wave_stage"] += 1

            # HARD CAP (fixes Wave_51 bug permanently)
            if latest_pattern["wave_stage"] > 5:
                latest_pattern["status"] = "INVALID_STRUCTURE"
                break

            stage = latest_pattern["wave_stage"]

            latest_pattern["type"] = resolve_wave_type(stage, latest_pattern["direction"])
            latest_pattern["status"] = f"WAVE_{stage}"
            latest_pattern["status_reason"] = f"Wave {stage} confirmed"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["status_reason"] = "Structure invalidated"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            break

    trade = build_elliott_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "ELLIOTT_IMPULSE"
    }