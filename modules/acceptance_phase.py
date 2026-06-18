import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# ACCEPTANCE PHASE ENGINE (INSTITUTIONAL FIXED)
# =========================================================

def detect_acceptance_phase(df):

    df = normalize_timestamp(df)

    # -----------------------------------------------------
    # SAFETY CHECKS
    # -----------------------------------------------------

    if df is None or len(df) < 60:
        return {
            "phase": "NONE",
            "confidence": 0.0,
            "interpretation": "Insufficient structure for acceptance analysis."
        }

    required_cols = ["High", "Low", "Close", "Volume"]

    for c in required_cols:
        if c not in df.columns:
            return {
                "phase": "NONE",
                "confidence": 0.0,
                "interpretation": f"Missing required column '{c}' after normalization."
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

    # -----------------------------------------------------
    # 1. RANGE EFFICIENCY (CORE ACCEPTANCE CONDITION)
    # -----------------------------------------------------

    recent_range = np.mean(high[recent] - low[recent])
    prior_range = np.mean(high[prior] - low[prior])

    range_compression = recent_range < prior_range * 1.10

    # -----------------------------------------------------
    # 2. VALUE AREA STABILITY
    # -----------------------------------------------------

    value_high = np.max(high[recent])
    value_low = np.min(low[recent])

    value_mid = np.mean(close[recent])

    deviation_up = np.mean(high[recent] - value_mid)
    deviation_down = np.mean(value_mid - low[recent])

    balance_ratio = min(deviation_up, deviation_down) / (max(deviation_up, deviation_down) + 1e-9)

    balanced_auction = balance_ratio > 0.65

    # -----------------------------------------------------
    # 3. VOLUME STABILITY (NO EXPANSION)
    # -----------------------------------------------------

    recent_vol = np.mean(volume[recent])
    prior_vol = np.mean(volume[prior])

    volume_stable = abs(recent_vol - prior_vol) / (prior_vol + 1e-9) < 0.20

    # -----------------------------------------------------
    # 4. TREND FLATNESS (NOT JUST LOW SLOPE)
    # -----------------------------------------------------

    slope = np.polyfit(range(20), close[-20:], 1)[0]
    volatility = np.std(close[-20:])

    flat_structure = abs(slope) < volatility * 0.10

    # -----------------------------------------------------
    # 5. NO BREAKOUT CONDITION (CRITICAL FIX)
    # -----------------------------------------------------

    prior_high = np.max(high[prior])
    prior_low = np.min(low[prior])

    no_breakout = (
        value_high <= prior_high
        and value_low >= prior_low
    )

    # -----------------------------------------------------
    # ACCEPTANCE SCORE
    # -----------------------------------------------------

    score = 0.0

    if range_compression:
        score += 0.25

    if balanced_auction:
        score += 0.30

    if volume_stable:
        score += 0.20

    if flat_structure:
        score += 0.15

    if no_breakout:
        score += 0.10

    confidence = round(min(score, 1.0), 3)

    # =====================================================
    # CLASSIFICATION LOGIC (FIXED)
    # =====================================================

    # 🔴 TRUE ACCEPTANCE (REAL EQUILIBRIUM)
    if confidence >= 0.75:
        return {
            "phase": "ACCEPTANCE",
            "confidence": confidence,
            "interpretation": (
                "True equilibrium regime detected. "
                "Market is operating inside a stable value area with "
                "balanced two-sided auction, compressed volatility, "
                "and no structural breakout pressure."
            )
        }

    # 🟡 TRANSITION (IMPORTANT FIX)
    if confidence >= 0.45:
        return {
            "phase": "TRANSITION",
            "confidence": confidence,
            "interpretation": (
                "Market is balancing but not fully accepted. "
                "Structure shows partial equilibrium conditions with "
                "potential directional build-up."
            )
        }

    # 🟢 NONE
    return {
        "phase": "NONE",
        "confidence": max(0.2, 1.0 - confidence),
        "interpretation": (
            "No true acceptance structure detected. "
            "Market is not in equilibrium conditions."
        )
    }


# =========================================================
# JOURNAL WRAPPER
# =========================================================

def run_acceptance_phase_engine(df):

    try:
        r = detect_acceptance_phase(df)

        return {
            "dominant_phase": r["phase"],
            "confidence": r["confidence"],

            "acceptance_block": f"""
📊 ACCEPTANCE PHASE ANALYSIS
---------------------------
Phase: {r['phase']}
Confidence: {r['confidence']:.2f}

Institutional Interpretation:
{r['interpretation']}
""",

            "phase_context_block": f"""
===========================
📊 ACCEPTANCE CONTEXT
===========================

Phase: {r['phase']}
Confidence: {r['confidence']:.2f}

{r['interpretation']}
"""
        }

    except Exception as e:
        raise RuntimeError(f"ACCEPTANCE FAILURE: {str(e)}")