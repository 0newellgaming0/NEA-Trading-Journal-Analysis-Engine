import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("bw_fractal")


# =========================================================
# SAFE HELPERS
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# FRACTAL DETECTORS (BILL WILLIAMS 5-BAR FRACTAL)
# =========================================================
def detect_fractal_pivot(df, i):
    """
    Detects classic Bill Williams fractal:
    - Bullish fractal = lowest low in 5-bar window
    - Bearish fractal = highest high in 5-bar window
    """

    if i < 2 or i >= len(df) - 2:
        return None

    high = f(df["High"].iloc[i])
    low = f(df["Low"].iloc[i])

    highs = [f(df["High"].iloc[j]) for j in range(i - 2, i + 3)]
    lows = [f(df["Low"].iloc[j]) for j in range(i - 2, i + 3)]

    # Bullish fractal (liquidity sweep low)
    if low == min(lows):
        return {
            "type": "FRACTAL_PIVOT",
            "direction": "BullishPivot",
            "high": high,
            "low": low,
            "index": i
        }

    # Bearish fractal (liquidity sweep high)
    if high == max(highs):
        return {
            "type": "FRACTAL_PIVOT",
            "direction": "BearishPivot",
            "high": high,
            "low": low,
            "index": i
        }

    return None


# =========================================================
# ACTIVE FRACTAL MANAGER
# =========================================================
def update_active_fractals(state, new_fractal):

    if "bullish" not in state:
        state["bullish"] = None
    if "bearish" not in state:
        state["bearish"] = None

    if new_fractal["direction"] == "BullishPivot":
        state["bullish"] = new_fractal

    if new_fractal["direction"] == "BearishPivot":
        state["bearish"] = new_fractal

    return state


def remove_invalid_fractals(state, current_price):

    if state.get("bullish"):
        if current_price < state["bullish"]["low"]:
            state["bullish"] = None

    if state.get("bearish"):
        if current_price > state["bearish"]["high"]:
            state["bearish"] = None

    return state


# =========================================================
# ALLIGATOR FILTER (MOUTH AVOIDANCE RULE)
# =========================================================
def fractal_inside_alligator(fractal, jaw, teeth, lips):

    price = fractal["high"] if fractal["direction"] == "BearishPivot" else fractal["low"]

    upper = max(jaw, teeth, lips)
    lower = min(jaw, teeth, lips)

    # Ignore fractals inside mouth
    return lower <= price <= upper


# =========================================================
# BREAKOUT ENGINE
# =========================================================
def detect_fractal_breakout(fractal, high, low):

    if fractal["direction"] == "BullishPivot":
        if high > fractal["high"]:
            return "BREAK_UP"
        if low < fractal["low"]:
            return "FAIL"

    if fractal["direction"] == "BearishPivot":
        if low < fractal["low"]:
            return "BREAK_DOWN"
        if high > fractal["high"]:
            return "FAIL"

    return None


# =========================================================
# ENTRY ENGINE
# =========================================================
def evaluate_entry_candidate(active_state):

    bull = active_state.get("bullish")
    bear = active_state.get("bearish")

    if bull and not bear:
        return "BULLISH"

    if bear and not bull:
        return "BEARISH"

    if bull and bear:
        return "CONFLICT"

    return None


# =========================================================
# MAIN ANALYZER (NEA PLUGIN OUTPUT CONTRACT)
# =========================================================
def analyze_bw_fractals(df, alligator_state=None):

    logger.info("[FRACTAL] analyzer started")

    state = {"bullish": None, "bearish": None}
    latest_event = None

    # STEP 1: SCAN FOR FRACTALS
    for i in range(len(df)):

        fractal = detect_fractal_pivot(df, i)

        if not fractal:
            continue

        # STEP 2: ALLIGATOR FILTER
        if alligator_state:
            if fractal_inside_alligator(
                fractal,
                alligator_state.get("jaw", 0),
                alligator_state.get("teeth", 0),
                alligator_state.get("lips", 0)
            ):
                continue

        state = update_active_fractals(state, fractal)

    # STEP 3: CLEAN INVALID FRACTALS
    current_price = f(df["Close"].iloc[-1])
    state = remove_invalid_fractals(state, current_price)

    # STEP 4: ENTRY EVALUATION
    entry_signal = evaluate_entry_candidate(state)

    bullish = state.get("bullish")
    bearish = state.get("bearish")

    confidence = 0

    if entry_signal == "BULLISH":
        confidence = 70 if bullish else 0

    elif entry_signal == "BEARISH":
        confidence = 70 if bearish else 0

    # STEP 5: BUILD EVENT
    latest_event = {
        "id": extract_event_date(df, len(df) - 1),

        "detected": entry_signal is not None,

        "type": "FRACTAL_ENTRY",

        "direction": entry_signal if entry_signal else "NONE",

        "status": "PENDING",

        "status_reason": "Fractal entry engine active",

        "bullish_fractal": bullish if bullish else None,

        "bearish_fractal": bearish if bearish else None,

        "breakout": entry_signal,

        "entry_candidate": entry_signal is not None,

        "confidence": confidence
    }

    return {
        "event": latest_event,
        "trade": {},
        "regime": "ENTRY_ENGINE"
    }