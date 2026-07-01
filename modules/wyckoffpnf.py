# =========================================================
# WYCKOFF POINT & FIGURE TRADE SETUP MODULE
# INSTITUTIONAL GRADE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# PROGRESSIVE EVENT VERSION (SEED REQUIRED)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("wyckoff_pnf")


# =========================================================
# SAFE HELPER (CRITICAL FIX: FLOAT SAFETY)
# =========================================================
def f(x):
    try:
        return float(x)
    except Exception:
        return None


def clean_series(series):
    return [f(x) for x in series if f(x) is not None]


# =========================================================
# SAFE BOX CONVERSION (REQUIRED FIX)
# =========================================================
def box(price, box_size):
    return int(float(price) / float(box_size))


def detect_wyckoff_pnf(price_series, box_size, reversal=3):
    """
    REAL WYCKOFF POINT & FIGURE STRUCTURE ENGINE

    RULES:
    - Uses ONLY price series (no candles)
    - Builds X/O columns
    - Applies fixed box size
    - Applies reversal rule (default 3-box)
    - Time is ignored
    """

    logger.debug("[WYCKOFF_PNF] real PnF detection called")

    if price_series is None or len(price_series) < 5:
        return {"detected": False}

    # =====================================================
    # 1. PNF STRUCTURE BUILD (X/O COLUMNS)
    # =====================================================

    columns = []
    current_column = None

    def box_round(price):
        return int(price / box_size)

    for price in price_series:

        box = box_round(price)

        if current_column is None:
            current_column = {
                "type": "X",
                "boxes": [box]
            }
            continue

        last_box = current_column["boxes"][-1]

        # =================================================
        # EXTEND CURRENT COLUMN
        # =================================================
        if current_column["type"] == "X":

            if box >= last_box:
                current_column["boxes"].append(box)

            elif (last_box - box) >= reversal:
                columns.append(current_column)
                current_column = {
                    "type": "O",
                    "boxes": [box]
                }

        elif current_column["type"] == "O":

            if box <= last_box:
                current_column["boxes"].append(box)

            elif (box - last_box) >= reversal:
                columns.append(current_column)
                current_column = {
                    "type": "X",
                    "boxes": [box]
                }

    if current_column:
        columns.append(current_column)

    # =====================================================
    # 2. STRUCTURE VALIDATION
    # =====================================================

    if len(columns) < 3:
        return {"detected": False}

    last = columns[-1]
    prev = columns[-2]
    prev2 = columns[-3]

    # =====================================================
    # RANGE (CAUSE ZONE)
    # NOTE: box space is integer-discretized; conversion is intentional
    # =====================================================

    all_boxes = [b for col in columns for b in col["boxes"]]
    box_high = max(all_boxes) * box_size
    box_low = min(all_boxes) * box_size

    # =====================================================
    # SPRING (TRUE WYCKOFF PnF STRUCTURE - ALIGNED WITH SEED)
    # =====================================================
    prev_low = min(prev["boxes"])
    last_low = min(last["boxes"])
    prev_high = max(prev["boxes"])
    last_high = max(last["boxes"])

    spring_penetration = prev_low - last_low

    spring = (
        prev["type"] == "O" and
        last["type"] == "X" and

        # MUST break prior support
        last_low < prev_low and

        # MUST have real sweep depth
        spring_penetration >= 1 and

        # rejection into structure
        last_high > prev_low and

        # failure to build O continuation (consistency with seed)
        len(last["boxes"]) <= len(prev["boxes"])
    )

    # =====================================================
    # UPTHRUST (TRUE WYCKOFF PnF STRUCTURE - ALIGNED WITH SEED)
    # =====================================================
    upthrust_penetration = last_high - prev_high

    upthrust = (
        prev["type"] == "X" and
        last["type"] == "O" and

        # break resistance
        last_high > prev_high and

        # real sweep
        upthrust_penetration >= 1 and

        # rejection back into structure
        last_low < prev_high and

        # failure to build X continuation
        len(last["boxes"]) <= len(prev["boxes"])
    )

    # =====================================================
    # SOS (STRUCTURAL ACCEPTANCE BREAKOUT)
    # =====================================================
    sos = (
        last["type"] == "X" and
        max(last["boxes"]) > max(prev["boxes"]) and
        len(last["boxes"]) >= len(prev["boxes"]) and

        # IMPORTANT: must not be rejection structure
        min(last["boxes"]) >= min(prev["boxes"])
    )

    # =====================================================
    # SOW (STRUCTURAL ACCEPTANCE BREAKDOWN)
    # =====================================================
    sow = (
        last["type"] == "O" and
        min(last["boxes"]) < min(prev["boxes"]) and
        len(last["boxes"]) >= len(prev["boxes"]) and

        # must show acceptance of lower prices
        max(last["boxes"]) <= max(prev["boxes"])
    )

    # =====================================================
    # FINAL CLASSIFICATION
    # =====================================================

    if spring:
        return {
            "detected": True,
            "type": "Wyckoff Spring (PnF True Structure)",
            "direction": "Bullish",
            "columns": columns,
            "box_high": box_high,
            "box_low": box_low,
            "cause_boxes": len(columns)
        }

    if upthrust:
        return {
            "detected": True,
            "type": "Wyckoff Upthrust (PnF True Structure)",
            "direction": "Bearish",
            "columns": columns,
            "box_high": box_high,
            "box_low": box_low,
            "cause_boxes": len(columns)
        }

    if sos:
        return {
            "detected": True,
            "type": "SOS (Sign of Strength - PnF)",
            "direction": "Bullish",
            "columns": columns,
            "box_high": box_high,
            "box_low": box_low,
            "cause_boxes": len(columns)
        }

    if sow:
        return {
            "detected": True,
            "type": "SOW (Sign of Weakness - PnF)",
            "direction": "Bearish",
            "columns": columns,
            "box_high": box_high,
            "box_low": box_low,
            "cause_boxes": len(columns)
        }

    return {"detected": False}


# =========================================================
# SEED DETECTION (EARLY LIQUIDITY GRAB BEFORE CONFIRMATION)
# =========================================================
def detect_wyckoff_pnf_seed(price_series, box_size, reversal=3):

    logger.debug("[WYCKOFF_PNF] seed detection called")

    if price_series is None or len(price_series) < 5:
        return {"detected": False}

    def box(price):
        return int(price / box_size)

    columns = []
    current = None

    for price in price_series:

        b = box(price)

        if current is None:
            current = {"type": "X", "boxes": [b]}
            continue

        last = current["boxes"][-1]

        if current["type"] == "X":

            if b >= last:
                current["boxes"].append(b)

            elif (last - b) >= reversal:
                columns.append(current)
                current = {"type": "O", "boxes": [b]}

        elif current["type"] == "O":

            if b <= last:
                current["boxes"].append(b)

            elif (b - last) >= reversal:
                columns.append(current)
                current = {"type": "X", "boxes": [b]}

    if current:
        columns.append(current)

    if len(columns) < 3:
        return {"detected": False}

    prev1 = columns[-2]
    last = columns[-1]

    all_boxes = [b for c in columns for b in c["boxes"]]

    range_high = max(all_boxes)
    range_low = min(all_boxes)

    prev_high = max(prev1["boxes"])
    prev_low = min(prev1["boxes"])
    last_high = max(last["boxes"])
    last_low = min(last["boxes"])

    prev_range = prev_high - prev_low
    last_range = last_high - last_low

    bullish_seed = (
        prev1["type"] == "O" and
        last["type"] == "X" and

        last_low < prev_low and
        (prev_low - last_low) >= 1 and

        last_high > prev_low and

        # FINAL ALIGNMENT FIX
        len(last["boxes"]) <= max(len(prev1["boxes"]), 1)
    )

    bearish_seed = (
        prev1["type"] == "X" and
        last["type"] == "O" and

        last_high > prev_high and
        (last_high - prev_high) >= 1 and

        last_low < prev_high and

        # FINAL ALIGNMENT FIX
        len(last["boxes"]) <= max(len(prev1["boxes"]), 1)
    )

    if bullish_seed:
        return {
            "detected": True,
            "type": "Wyckoff Spring (PnF Seed)",
            "direction": "Bullish",
            "stage": "SEED",
            "columns": columns,
            "box_high": range_high,
            "box_low": range_low,
            "high": range_high,
            "low": range_low,
            "detected_date": None,
            "resolved_date": None,
            "bars_active": len(price_series)
        }

    if bearish_seed:
        return {
            "detected": True,
            "type": "Wyckoff Upthrust (PnF Seed)",
            "direction": "Bearish",
            "stage": "SEED",
            "columns": columns,
            "box_high": range_high,
            "box_low": range_low,
            "high": range_high,
            "low": range_low,
            "detected_date": None,
            "resolved_date": None,
            "bars_active": len(price_series)
        }

    return {"detected": False}

def interpret_wyckoff_pnf(event):

    direction = event.get("direction")
    ptype = event.get("type", "")
    status = event.get("status")
    stage = event.get("stage")

    interpretations = []

    # =====================================================
    # CORE STRUCTURE IDENTITY (PnF CONTEXT)
    # =====================================================

    if "Seed" in ptype:
        interpretations.append(
            "Early Wyckoff Point & Figure seed detected: initial column transition within developing X/O structure indicating early liquidity reaction inside a range."
        )
    else:
        interpretations.append(
            "Wyckoff Point & Figure structure detected: column-based range behavior showing interaction between supply and demand within a defined PnF box structure."
        )

    interpretations.append(
        "Price is being expressed through X/O column transitions rather than time-based candles, consistent with Wyckoff PnF methodology for mapping cause."
    )

    # =====================================================
    # LIQUIDITY BEHAVIOR INTERPRETATION
    # =====================================================

    interpretations.append(
        "Observed behavior reflects a liquidity test of the PnF range boundary, where price probes structural extremes before reverting back into the established column framework."
    )

    interpretations.append(
        "This aligns with Wyckoff principles where cause is built through alternating absorption of supply and demand within horizontal structure."
    )

    # =====================================================
    # DIRECTIONAL INTERPRETATION (PnF CONTEXT)
    # =====================================================

    if direction == "Bullish":

        interpretations.append(
            "Bullish PnF behavior: downward supply pressure is being absorbed within O-columns, followed by emergence of X-columns indicating demand taking control."
        )

        interpretations.append(
            "Potential accumulation behavior: structure suggests absorption of supply near lower PnF boundary (Spring-type behavior in column context)."
        )

    elif direction == "Bearish":

        interpretations.append(
            "Bearish PnF behavior: upward demand pressure is being rejected within X-columns, followed by expansion of O-columns indicating supply dominance."
        )

        interpretations.append(
            "Potential distribution behavior: structure suggests rejection of higher prices near upper PnF boundary (Upthrust-type behavior in column context)."
        )

    # =====================================================
    # STRUCTURAL STATE INTERPRETATION
    # =====================================================

    if stage == "SEED":

        interpretations.append(
            "Seed phase: early column transition without full commitment. Structure is still forming and lacks confirmed continuation of X or O dominance."
        )

    if status == "PENDING":

        interpretations.append(
            "Pending structure: PnF cause is developing. Market is still alternating between X and O columns without decisive breakout from the range."
        )

    elif status == "CONFIRMED":

        interpretations.append(
            "Confirmed PnF structure: column continuation indicates acceptance beyond prior balance zone, signaling resolved directional intent."
        )

    elif status == "FAILED":

        interpretations.append(
            "Failed PnF structure: column transition did not sustain, indicating rejection of attempted breakout and return to balance behavior."
        )

    # =====================================================
    # FINAL OUTPUT
    # =====================================================

    return " | ".join(interpretations)


# =========================================================
# TRADE STATE BUILDER (WYCKOFF PnF INSTITUTIONAL MODEL)
# =========================================================

def build_wyckoff_pnf_trade_state(event):

    columns = event.get("columns", [])
    direction = event.get("direction")

    if not columns:
        return {}

    # =====================================================
    # STRUCTURAL RANGE (CAUSE ZONE)
    # =====================================================
    all_boxes = [b for col in columns for b in col["boxes"]]

    box_high = max(all_boxes)
    box_low = min(all_boxes)

    rng = max(box_high - box_low, 1e-9)

    # =====================================================
    # BULLISH (SPRING / ACCUMULATION RESPONSE)
    # =====================================================
    if direction == "Bullish":

        return {
            "trade_type": "REVERSAL",
            "direction": "LONG",

            # PnF breakout confirmation entry (SOS trigger zone)
            "entry": box_high,

            # structural invalidation (loss of accumulation range)
            "stop": box_low - 1,

            "wick_stop": box_low,

            "invalidation": box_low,

            # PnF expansion targets (range projection proxy)
            "target1": box_high + rng,
            "target2": box_high + (2 * rng),

            "failure": f"PnF close/column break below {box_low}",

            "interpretation":
                "Wyckoff PnF Spring trade: structural accumulation range with bullish column reversal indicating absorption of supply and emergence of demand."
        }

    # =====================================================
    # BEARISH (UPTHRUST / DISTRIBUTION RESPONSE)
    # =====================================================
    if direction == "Bearish":

        return {
            "trade_type": "REVERSAL",
            "direction": "SHORT",

            # PnF breakdown confirmation entry (SOW trigger zone)
            "entry": box_low,

            # structural invalidation
            "stop": box_high + 1,

            "wick_stop": box_high,

            "invalidation": box_high,

            # expansion targets
            "target1": box_low - rng,
            "target2": box_low - (2 * rng),

            "failure": f"PnF close/column break above {box_high}",

            "interpretation":
                "Wyckoff PnF Upthrust trade: structural distribution range with bearish column reversal indicating rejection of demand and expansion of supply."
        }

    return {}


# =========================================================
# STATE ENGINE RULES (EVENT RESOLUTION LOGIC)
# =========================================================
def wyckoff_pnf_event_rules(event, price):

    status = event.get("status")
    direction = event.get("direction")

    box_high = f(event.get("box_high"))
    box_low = f(event.get("box_low"))
    price = f(price)

    if box_high is None or box_low is None or price is None:
        return None

    if status == "SEED":

        if direction == "Bullish":
            if price > box_high:
                return "CONFIRM"
            if price < box_low:
                return "FAIL"

        elif direction == "Bearish":
            if price < box_low:
                return "CONFIRM"
            if price > box_high:
                return "FAIL"

    elif status == "PENDING":

        if direction == "Bullish":
            if price > box_high:
                return "CONFIRM"
            if price < box_low:
                return "FAIL"

        elif direction == "Bearish":
            if price < box_low:
                return "CONFIRM"
            if price > box_high:
                return "FAIL"

    elif status == "CONFIRMED":

        if direction == "Bullish" and price < box_low:
            return "FAIL"

        if direction == "Bearish" and price > box_high:
            return "FAIL"

    return None
    
def analyze_wyckoff_pnf(price_series, event_store=None, box_size=1.0, reversal=3):

    logger.info("[WYCKOFF_PNF] analyze_wyckoff_pnf() called")

    price_series = clean_series(price_series)

    if price_series is None or len(price_series) < 5:
        return {
            "event": {
                "detected": False,
                "type": None,
                "direction": None,
                "status": "NO_SEED"
            },
            "trade": {},
            "regime": "NONE"
        }

    columns = []
    current = None

    for price in price_series:

        b = box(price, box_size)

        if current is None:
            current = {"type": "X", "boxes": [b]}
            continue

        last = current["boxes"][-1]

        if current["type"] == "X":

            if b >= last:
                current["boxes"].append(b)

            elif (last - b) >= reversal:
                columns.append(current)
                current = {"type": "O", "boxes": [b]}

        elif current["type"] == "O":

            if b <= last:
                current["boxes"].append(b)

            elif (b - last) >= reversal:
                columns.append(current)
                current = {"type": "X", "boxes": [b]}

    if current:
        columns.append(current)

    if len(columns) < 3:
        return {
            "event": {
                "detected": False,
                "type": None,
                "direction": None,
                "status": "NO_SEED"
            },
            "trade": {},
            "regime": "NONE"
        }

    all_boxes = [b for col in columns for b in col["boxes"]]

    box_high = max(all_boxes) * box_size
    box_low = min(all_boxes) * box_size

    prev1 = columns[-2]
    last = columns[-1]

    bullish_seed = (
        prev1["type"] == "O" and
        last["type"] == "X" and
        min(last["boxes"]) <= min(prev1["boxes"]) and
        len(last["boxes"]) <= len(prev1["boxes"])
    )

    bearish_seed = (
        prev1["type"] == "X" and
        last["type"] == "O" and
        max(last["boxes"]) >= max(prev1["boxes"]) and
        len(last["boxes"]) <= len(prev1["boxes"])
    )

    if not (bullish_seed or bearish_seed):
        return {
            "event": {
                "detected": False,
                "type": None,
                "direction": None,
                "status": "NO_SEED"
            },
            "trade": {},
            "regime": "NONE"
        }

    # FIX 3 — EVENT STRUCTURE STABILITY
    event = {
        "id": 1,
        "detected": True,
        "type": "Wyckoff Spring (PnF Seed)" if bullish_seed else "Wyckoff Upthrust (PnF Seed)",
        "direction": "Bullish" if bullish_seed else "Bearish",
        "columns": columns,
        "box_high": box_high,
        "box_low": box_low,
        "status": "SEED",

        "detected_date": None,
        "resolved_date": None,
        "bars_active": len(price_series)
    }

    for price in price_series:

        action = wyckoff_pnf_event_rules(event, price)

        if action == "CONFIRM":
            event["status"] = "CONFIRMED"
            event["status_reason"] = "PnF continuation confirmed"
            break

        elif action == "FAIL":
            event["status"] = "FAILED"
            event["status_reason"] = "PnF structure invalidated"
            break

    trade = build_wyckoff_pnf_trade_state(event)

    # FIX 5 — GUARANTEED STRUCTURED RETURN
    return {
        "event": event,
        "trade": trade,
        "regime": "WYCKOFF_PNF" if event.get("detected") else "NONE"
    }