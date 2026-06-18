import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# DISCOVERY PHASE ENGINE (INSTITUTIONAL GRADE FIXED)
# =========================================================

def detect_discovery_phase(df):

    df = normalize_timestamp(df)

    # -----------------------------------------------------
    # BASIC SAFETY CHECKS
    # -----------------------------------------------------

    if df is None or len(df) < 60:
        return {
            "phase": "NONE",
            "confidence": 0.0,
            "interpretation": "Insufficient structure for discovery evaluation."
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
    # 1. RANGE COMPRESSION (CRITICAL FIX)
    # -----------------------------------------------------
    recent_range = np.mean(high[recent] - low[recent])
    prior_range = np.mean(high[prior] - low[prior])

    compression_break = recent_range > prior_range * 1.35

    # -----------------------------------------------------
    # 2. STRUCTURAL BREAKOUT
    # -----------------------------------------------------

    prior_high = np.max(high[prior])
    recent_high = np.max(high[recent])

    prior_low = np.min(low[prior])
    recent_low = np.min(low[recent])

    breakout_up = recent_high > prior_high
    breakout_down = recent_low < prior_low

    structural_break = breakout_up or breakout_down

    # -----------------------------------------------------
    # 3. VOLUME EXPANSION (RELATIVE, NOT SPIKE ONLY)
    # -----------------------------------------------------

    recent_vol = np.mean(volume[recent])
    prior_vol = np.mean(volume[prior])

    volume_expansion = recent_vol > prior_vol * 1.25

    # -----------------------------------------------------
    # 4. MOMENTUM SHIFT (NOT JUST SLOPE)
    # -----------------------------------------------------

    slope = np.polyfit(range(20), close[-20:], 1)[0]
    volatility = np.std(close[-20:])

    momentum_shift = abs(slope) > volatility * 0.15

    # -----------------------------------------------------
    # 5. BREAKOUT QUALITY SCORE
    # -----------------------------------------------------

    score = 0.0

    if structural_break:
        score += 0.40

    if compression_break:
        score += 0.25

    if volume_expansion:
        score += 0.20

    if momentum_shift:
        score += 0.15

    confidence = round(min(score, 1.0), 3)

    # =====================================================
    # CLASSIFICATION (FIXED LOGIC)
    # =====================================================

    # 🔴 TRUE DISCOVERY (RARE EVENT)
    if (
        confidence >= 0.75
        and structural_break
        and compression_break
    ):
        return {
            "phase": "DISCOVERY",
            "confidence": confidence,
            "interpretation": (
                "True structural breakout detected. "
                "Market is leaving established value with volatility expansion, "
                "compression release, and institutional participation."
            )
        }

    # 🟡 TRANSITION STATE (IMPORTANT FIX)
    if confidence >= 0.45:
        return {
            "phase": "TRANSITION",
            "confidence": confidence,
            "interpretation": (
                "Building structural pressure. "
                "Market is transitioning between acceptance and breakout conditions "
                "without confirmed discovery regime."
            )
        }

    # 🟢 DEFAULT STATE
    return {
        "phase": "NONE",
        "confidence": max(0.2, 1.0 - confidence),
        "interpretation": (
            "No structural breakout or expansion detected. "
            "Market remains within accepted value conditions."
        )
    }


# =========================================================
# JOURNAL WRAPPER
# =========================================================

def run_discovery_phase_engine(df):

    try:
        result = detect_discovery_phase(df)

        discovery_block = f"""
📊 DISCOVERY PHASE ANALYSIS
--------------------------
Phase: {result['phase']}
Confidence: {result['confidence']:.2f}

Institutional Interpretation:
{result['interpretation']}
"""

        return {
            "dominant_phase": result["phase"],
            "confidence": result["confidence"],
            "discovery_block": discovery_block,
            "phase_context_block": f"""
===========================
📊 DISCOVERY CONTEXT
===========================

Phase: {result['phase']}
Confidence: {result['confidence']:.2f}

{result['interpretation']}
"""
        }

    except Exception as e:
        raise RuntimeError(f"DISCOVERY PHASE FAILURE: {str(e)}")