import logging

from modules.signalEngine import (
    evaluate_trend,
    detect_liquidity_sweep,
    evaluate_structure,
    evaluate_fibonacci
)

from modules.volumeAnalysis import (
    rvol,
    detect_volume_spike,
    institutional_accumulation_state
)

logger = logging.getLogger("institutional_context")


# =========================================================
# FORMATTERS
# =========================================================
def fmt_trend(x):
    return f"{x['trend']} (Strength: {x['score']})"

def fmt_sweep(x):
    return x["type"] if x["sweep"] else "None"

def fmt_structure(x):
    return x["label"]

def fmt_fib(x):
    return x["label"]

def fmt_volume(x):
    return x.get("label", "UNKNOWN VOLUME STATE")


# =========================================================
# VOLUME WRAPPER (IMPORTANT FIX)
# =========================================================
def volume_confirmation(df):

    volume = df["Volume"]
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    rv = rvol(volume)
    spike = detect_volume_spike(volume)
    inst = institutional_accumulation_state(close, high, low, volume)

    def last(x):
        return x.iloc[-1] if hasattr(x, "iloc") else x[-1]

    rv_last = float(last(rv) or 0)
    spike_last = bool(last(spike))
    inst_last = last(inst)

    # ============================
    # NEW: HUMAN STATE LAYER
    # ============================

    if rv_last >= 3.0 and spike_last:
        state = "EXTREME INSTITUTIONAL VOLUME"
    elif rv_last >= 2.0:
        state = "HIGH EXPANSION VOLUME"
    elif rv_last >= 1.5 and spike_last:
        state = "ABOVE AVERAGE SPIKE"
    elif rv_last < 0.7:
        state = "EXTREMELY LOW PARTICIPATION"
    elif rv_last < 1.0:
        state = "LOW / DRYING VOLUME"
    else:
        state = "NORMAL PARTICIPATION"

    return {
        "confirmed": rv_last > 1.5 and spike_last,
        "rvol": rv_last,
        "institutional_state": str(inst_last),

        # 🔥 THIS is what UI should use
        "label": state,

        # keep for calculations only
        "score": rv_last
    }
    
def derive_regime(trend, sweep, structure, volume):
    
    # -------------------------
    # LIQUIDITY FIRST (Wyckoff priority)
    # -------------------------
    if sweep["sweep"]:
        return "LIQUIDITY_EVENT"

    # -------------------------
    # EXPANSION PHASE
    # -------------------------
    if trend["trend"] == "Bullish":
        if volume["label"] in ["EXTREME INSTITUTIONAL VOLUME", "HIGH EXPANSION VOLUME"]:
            return "BULLISH_EXPANSION"

    if trend["trend"] == "Bearish":
        if volume["label"] in ["EXTREME INSTITUTIONAL VOLUME", "HIGH EXPANSION VOLUME"]:
            return "BEARISH_EXPANSION"

    # -------------------------
    # ACCUMULATION / DISTRIBUTION
    # -------------------------
    if structure["label"] == "Near Support":
        return "ACCUMULATION_ZONE"

    if structure["label"] == "Near Resistance":
        return "DISTRIBUTION_ZONE"

    # -------------------------
    # COMPRESSION
    # -------------------------
    if volume["label"] in ["LOW / DRYING VOLUME", "EXTREMELY LOW PARTICIPATION"]:
        return "COMPRESSION_PHASE"

    # -------------------------
    # DEFAULT
    # -------------------------
    return "TRANSITION"
    

# =========================================================
# CONTEXT BUILDER (SINGLE SOURCE OF TRUTH)
# =========================================================
def build_institutional_context(df, f=float):

    trend = evaluate_trend(df, f)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    fib = evaluate_fibonacci(df)
    volume = volume_confirmation(df)
    regime = derive_regime(
        trend,
        sweep,
        structure,
        volume
    )    

    packed = {

        # RAW
        "_trend_raw": trend,
        "_sweep_raw": sweep,
        "_structure_raw": structure,
        "_fib_raw": fib,
        "_volume_raw": volume,

        # DISPLAY
        "trend": fmt_trend(trend),
        "liquidity_sweep": fmt_sweep(sweep),
        "structure": fmt_structure(structure),
        "fibonacci": fmt_fib(fib),
        "volume": fmt_volume(volume),

        "institutional_state": volume["institutional_state"],
        "regime": regime
    }

    return packed