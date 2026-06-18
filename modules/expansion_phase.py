import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# EXPANSION PHASE ENGINE (INSTITUTIONAL FIXED)
# =========================================================

def detect_expansion_phase(df):

    df = normalize_timestamp(df)

    # -----------------------------------------------------
    # SAFETY CHECKS
    # -----------------------------------------------------

    if df is None or len(df) < 60:
        return {
            "phase": "NONE",
            "confidence": 0.0,
            "interpretation": "Insufficient structure for expansion analysis."
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
    # 1. VOLATILITY EXPANSION (KEY FIX)
    # -----------------------------------------------------

    recent_range = np.mean(high[recent] - low[recent])
    prior_range = np.mean(high[prior] - low[prior])

    volatility_expanding = recent_range > prior_range * 1.30

    # -----------------------------------------------------
    # 2. STRUCTURAL BREAKOUT CONFIRMATION
    # -----------------------------------------------------

    prior_high = np.max(high[prior])
    recent_high = np.max(high[recent])

    breakout = recent_high > prior_high

    # -----------------------------------------------------
    # 3. VOLUME CONFIRMATION (RELATIVE, NOT SPIKE)
    # -----------------------------------------------------

    recent_vol = np.mean(volume[recent])
    prior_vol = np.mean(volume[prior])

    volume_expanding = recent_vol > prior_vol * 1.25

    # -----------------------------------------------------
    # 4. MOMENTUM QUALITY (NOT JUST SLOPE)
    # -----------------------------------------------------

    slope = np.polyfit(range(20), close[-20:], 1)[0]
    volatility = np.std(close[-20:])

    momentum = abs(slope) > volatility * 0.12

    # -----------------------------------------------------
    # 5. TREND CONTEXT FILTER (IMPORTANT FIX)
    # -----------------------------------------------------

    trend_continuation = slope > 0 and close[-1] > np.mean(close[-20:])

    # -----------------------------------------------------
    # EXPANSION SCORE
    # -----------------------------------------------------

    score = 0.0

    if breakout:
        score += 0.40

    if volatility_expanding:
        score += 0.25

    if volume_expanding:
        score += 0.20

    if momentum:
        score += 0.10

    if trend_continuation:
        score += 0.05

    confidence = round(min(score, 1.0), 3)

    # =====================================================
    # CLASSIFICATION (FIXED LOGIC)
    # =====================================================

    # 🔴 TRUE EXPANSION (RARE)
    if (
        confidence >= 0.75
        and breakout
        and volatility_expanding
    ):
        return {
            "phase": "EXPANSION",
            "confidence": confidence,
            "interpretation": (
                "True expansion regime detected. "
                "Market is in structural breakout with volatility expansion, "
                "volume participation, and directional continuation."
            )
        }

    # 🟡 TRANSITION / CONTINUATION STATE
    if confidence >= 0.45:
        return {
            "phase": "TRANSITION",
            "confidence": confidence,
            "interpretation": (
                "Market showing continuation pressure but lacks full expansion confirmation. "
                "Structure is still developing."
            )
        }

    # 🟢 NOT EXPANSION
    return {
        "phase": "NONE",
        "confidence": max(0.2, 1.0 - confidence),
        "interpretation": (
            "No expansion regime detected. "
            "Market remains within existing value structure."
        )
    }


# =========================================================
# JOURNAL WRAPPER
# =========================================================

def run_expansion_phase_engine(df):

    try:
        r = detect_expansion_phase(df)

        return {
            "dominant_phase": r["phase"],
            "confidence": r["confidence"],

            "expansion_block": f"""
📊 EXPANSION PHASE ANALYSIS
--------------------------
Phase: {r['phase']}
Confidence: {r['confidence']:.2f}

Institutional Interpretation:
{r['interpretation']}
""",

            "phase_context_block": f"""
===========================
📊 EXPANSION CONTEXT
===========================

Phase: {r['phase']}
Confidence: {r['confidence']:.2f}

{r['interpretation']}
"""
        }

    except Exception as e:
        raise RuntimeError(f"EXPANSION FAILURE: {str(e)}")