import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# EXHAUSTION PHASE ENGINE (INSTITUTIONAL FIXED)
# =========================================================

def detect_exhaustion_phase(df):

    df = normalize_timestamp(df)

    # -----------------------------------------------------
    # SAFETY CHECKS
    # -----------------------------------------------------

    if df is None or len(df) < 60:
        return {
            "phase": "NONE",
            "confidence": 0.0,
            "interpretation": "Insufficient structure for exhaustion analysis."
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

    recent = slice(-10, None)
    mid = slice(-20, -10)
    long = slice(-60, None)

    # -----------------------------------------------------
    # 1. MOMENTUM DECAY CURVE (FIXED CORE LOGIC)
    # -----------------------------------------------------

    slope_recent = np.polyfit(range(10), close[recent], 1)[0]
    slope_mid = np.polyfit(range(10), close[mid], 1)[0]

    momentum_decay = slope_recent < slope_mid

    # -----------------------------------------------------
    # 2. TREND MATURITY FILTER (CRITICAL ADDITION)
    # -----------------------------------------------------

    slope_long = np.polyfit(range(30), close[-30:], 1)[0]
    long_volatility = np.std(close[-30:])

    trend_mature = abs(slope_long) > long_volatility * 0.15

    # -----------------------------------------------------
    # 3. VOLUME EXHAUSTION (NOT JUST SPIKE)
    # -----------------------------------------------------

    recent_vol = np.mean(volume[recent])
    prior_vol = np.mean(volume[mid])

    volume_expansion = recent_vol > prior_vol * 1.6

    volume_climax = volume[-1] > np.mean(volume[-20:]) * 1.8

    # -----------------------------------------------------
    # 4. WICK REJECTION PRESSURE
    # -----------------------------------------------------

    wick_size = np.mean(high[recent] - close[recent])
    wick_expansion = wick_size > np.std(close[-20:]) * 0.6

    # -----------------------------------------------------
    # 5. VOLATILITY SHIFT (IMPORTANT FIX)
    # -----------------------------------------------------

    recent_range = np.mean(high[recent] - low[recent])
    prior_range = np.mean(high[mid] - low[mid])

    volatility_expansion_after_contraction = recent_range > prior_range * 1.3

    # -----------------------------------------------------
    # EXHAUSTION SCORE
    # -----------------------------------------------------

    score = 0.0

    if momentum_decay:
        score += 0.30

    if volume_expansion:
        score += 0.25

    if volume_climax:
        score += 0.15

    if wick_expansion:
        score += 0.15

    if volatility_expansion_after_contraction:
        score += 0.10

    if trend_mature:
        score += 0.05

    confidence = round(min(score, 1.0), 3)

    # =====================================================
    # CLASSIFICATION LOGIC (FIXED)
    # =====================================================

    # 🔴 TRUE EXHAUSTION (STRONG REVERSAL RISK)
    if confidence >= 0.75 and momentum_decay and volume_climax:
        return {
            "phase": "EXHAUSTION",
            "confidence": confidence,
            "interpretation": (
                "True exhaustion regime detected. "
                "Momentum deterioration with volume climax and "
                "structural weakening suggests late-cycle behavior "
                "and elevated reversal risk."
            )
        }

    # 🟡 TRANSITION / FATIGUE STATE
    if confidence >= 0.45:
        return {
            "phase": "TRANSITION",
            "confidence": confidence,
            "interpretation": (
                "Late-stage trend fatigue detected. "
                "Momentum is weakening but full exhaustion "
                "confirmation is not yet present."
            )
        }

    # 🟢 NONE
    return {
        "phase": "NONE",
        "confidence": max(0.2, 1.0 - confidence),
        "interpretation": (
            "No exhaustion structure detected. "
            "Trend remains structurally intact."
        )
    }


# =========================================================
# JOURNAL WRAPPER
# =========================================================

def run_exhaustion_phase_engine(df):

    try:
        r = detect_exhaustion_phase(df)

        return {
            "dominant_phase": r["phase"],
            "confidence": r["confidence"],

            "exhaustion_block": f"""
📊 EXHAUSTION PHASE ANALYSIS
--------------------------
Phase: {r['phase']}
Confidence: {r['confidence']:.2f}

Institutional Interpretation:
{r['interpretation']}
""",

            "phase_context_block": f"""
===========================
📊 EXHAUSTION CONTEXT
===========================

Phase: {r['phase']}
Confidence: {r['confidence']:.2f}

{r['interpretation']}
"""
        }

    except Exception as e:
        raise RuntimeError(f"EXHAUSTION FAILURE: {str(e)}")