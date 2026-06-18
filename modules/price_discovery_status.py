import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# PRICE DISCOVERY STATUS ENGINE (INSTITUTIONAL FIXED)
# =========================================================
# PURPOSE:
#   This is NOT a phase engine.
#   This is a REGIME CLASSIFIER only.
#
# OUTPUT:
#   - ACCEPTANCE (default market state)
#   - TRANSITION (mixed conditions)
#   - DISCOVERY (rare, structural breakout regime)
# =========================================================


def calculate_price_discovery_status(df):

    df = normalize_timestamp(df)

    # -----------------------------------------------------
    # SAFETY CHECKS
    # -----------------------------------------------------

    if df is None or len(df) < 60:
        return {
            "status": "ACCEPTANCE",
            "confidence": 0.20,
            "interpretation": "Insufficient structure → defaulting to equilibrium (acceptance)."
        }

    close = df["Close"].values
    high = df["High"].values
    low = df["Low"].values
    volume = df["Volume"].values

    # -----------------------------------------------------
    # STRUCTURE WINDOWS
    # -----------------------------------------------------

    recent = slice(-20, None)
    prior = slice(-60, -20)

    # guard
    if len(close) < 60:
        recent = slice(-20, None)
        prior = slice(0, 20)

    # -----------------------------------------------------
    # PRICE BREAKOUT QUALITY
    # -----------------------------------------------------

    recent_high = np.max(high[recent])
    prior_high = np.max(high[prior])

    recent_low = np.min(low[recent])
    prior_low = np.min(low[prior])

    breakout_up = recent_high > prior_high
    breakout_down = recent_low < prior_low

    structure_break = breakout_up or breakout_down

    # -----------------------------------------------------
    # VOLATILITY REGIME
    # -----------------------------------------------------

    recent_range = np.mean(high[recent] - low[recent])
    prior_range = np.mean(high[prior] - low[prior])

    volatility_expanding = recent_range > prior_range * 1.25

    # -----------------------------------------------------
    # VOLUME REGIME (FILTERED, NOT SPIKE ONLY)
    # -----------------------------------------------------

    recent_vol = np.mean(volume[recent])
    prior_vol = np.mean(volume[prior])

    volume_expanding = recent_vol > prior_vol * 1.20

    # -----------------------------------------------------
    # TREND CONTEXT (IMPORTANT FIX)
    # -----------------------------------------------------

    slope = np.polyfit(range(20), close[-20:], 1)[0]

    trending = abs(slope) > np.std(close[-20:]) * 0.002

    # -----------------------------------------------------
    # STRUCTURAL SCORE (HARDER THRESHOLDS)
    # -----------------------------------------------------

    score = 0.0

    if structure_break:
        score += 0.45

    if volatility_expanding:
        score += 0.25

    if volume_expanding:
        score += 0.20

    if trending:
        score += 0.10

    confidence = round(min(score, 1.0), 3)

    # =====================================================
    # REGIME CLASSIFICATION (FIXED LOGIC)
    # =====================================================

    # 🔴 STRICT DISCOVERY (RARE)
    if confidence >= 0.75:
        return {
            "status": "DISCOVERY",
            "confidence": confidence,
            "interpretation": (
                "Structural breakout regime detected. "
                "Price is leaving accepted value with volatility expansion "
                "and participation increase."
            )
        }

    # 🟡 TRANSITION REGIME (MOST COMMON ACTIVE STATE)
    if confidence >= 0.45:
        return {
            "status": "TRANSITION",
            "confidence": confidence,
            "interpretation": (
                "Mixed structural conditions. "
                "Market is transitioning between acceptance and expansion "
                "without confirmed breakout regime."
            )
        }

    # 🟢 DEFAULT STATE (IMPORTANT FIX)
    return {
        "status": "ACCEPTANCE",
        "confidence": max(0.20, 1.0 - confidence),
        "interpretation": (
            "Market in equilibrium. "
            "No confirmed structural breakout or expansion conditions."
        )
    }


# =========================================================
# JOURNAL WRAPPER (UNCHANGED OUTPUT FORMAT)
# =========================================================

def run_price_discovery_status_engine(df):

    try:

        result = calculate_price_discovery_status(df)

        return {
            "status": result["status"],
            "confidence": result["confidence"],

            "price_discovery_block": f"""
📊 PRICE DISCOVERY STATUS
-------------------------
Status: {result['status']}
Confidence: {result['confidence']:.2f}

Institutional Interpretation:
{result['interpretation']}
""",

            "phase_context_block": f"""
===========================
📊 PRICE DISCOVERY CONTEXT
===========================

Status: {result['status']}
Confidence: {result['confidence']:.2f}

{result['interpretation']}
"""
        }

    except Exception as e:
        raise RuntimeError(f"PRICE DISCOVERY STATUS FAILURE: {str(e)}")