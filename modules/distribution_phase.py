import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# DISTRIBUTION PHASE DETECTION ENGINE (INSTITUTIONAL FIXED)
# =========================================================

def detect_distribution_phase(df):

    df = normalize_timestamp(df)

    # -----------------------------------------------------
    # SAFETY CHECKS
    # -----------------------------------------------------

    if df is None or len(df) < 60:
        return {
            "phase": "NONE",
            "confidence": 0.0,
            "interpretation": "Insufficient structure for distribution analysis."
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
    # 1. TREND MATURITY (CRITICAL FIX)
    # -----------------------------------------------------

    slope_long = np.polyfit(range(30), close[-30:], 1)[0]
    trend_strength = abs(slope_long)

    trend_mature = trend_strength > np.std(close[-30:]) * 0.10

    # -----------------------------------------------------
    # 2. PRICE WEAKNESS (STRUCTURAL SLOPE DECAY)
    # -----------------------------------------------------

    slope_recent = np.polyfit(range(10), close[recent], 1)[0]
    slope_mid = np.polyfit(range(10), close[mid], 1)[0]

    momentum_fading = slope_recent < slope_mid

    # -----------------------------------------------------
    # 3. RANGE EXPANSION AFTER TIGHT STRUCTURE
    # -----------------------------------------------------

    recent_range = np.mean(high[recent] - low[recent])
    prior_range = np.mean(high[mid] - low[mid])

    range_expansion = recent_range > prior_range * 1.25

    # -----------------------------------------------------
    # 4. VOLUME DISTRIBUTION PRESSURE
    # -----------------------------------------------------

    avg_vol = np.mean(volume[-20:])
    vol_expansion = volume[-1] > avg_vol * 1.6
    vol_climax = volume[-1] > np.mean(volume[-20:]) * 1.8

    # -----------------------------------------------------
    # 5. SELLING PRESSURE (WICKS / REJECTION)
    # -----------------------------------------------------

    upper_wick = np.mean(high[recent] - close[recent])
    rejection = upper_wick > np.std(close[-20:]) * 0.55

    # -----------------------------------------------------
    # 6. STRUCTURAL FAILURE (LOWER HIGHS)
    # -----------------------------------------------------

    lower_highs = close[-1] < np.max(close[-10:-1])

    # -----------------------------------------------------
    # SCORE MODEL (FIXED LOGIC)
    # -----------------------------------------------------

    score = 0.0

    if momentum_fading:
        score += 0.25

    if vol_expansion:
        score += 0.20

    if rejection:
        score += 0.15

    if lower_highs:
        score += 0.15

    if range_expansion:
        score += 0.15

    if trend_mature:
        score += 0.10

    confidence = round(min(score, 1.0), 3)

    # =====================================================
    # CLASSIFICATION LOGIC (FIXED)
    # =====================================================

    # 🔴 TRUE DISTRIBUTION
    if confidence >= 0.75 and lower_highs and vol_climax:

        return {
            "phase": "DISTRIBUTION",
            "confidence": confidence,
            "interpretation": (
                "Institutional distribution confirmed. "
                "Trend shows structural failure, lower highs, "
                "volume climax, and expansion of volatility. "
                "Supply dominance is evident."
            )
        }

    # 🟡 TRANSITION DISTRIBUTION (EARLY WARNING)
    if confidence >= 0.45:

        return {
            "phase": "TRANSITION",
            "confidence": confidence,
            "interpretation": (
                "Early distribution characteristics forming. "
                "Momentum is weakening and supply pressure is increasing, "
                "but full structural breakdown is not confirmed."
            )
        }

    # 🟢 NONE
    return {
        "phase": "NONE",
        "confidence": max(0.2, 1.0 - confidence),
        "interpretation": (
            "No distribution structure detected. "
            "Market does not show institutional exit behavior."
        )
    }


# =========================================================
# WRAPPER (JOURNAL OUTPUT)
# =========================================================

def run_distribution_phase_engine(df):

    try:
        result = detect_distribution_phase(df)

        return {
            "dominant_phase": result["phase"],
            "confidence": float(result["confidence"]),

            "distribution_block": f"""
📊 DISTRIBUTION PHASE ANALYSIS
-----------------------------
Phase: {result['phase']}
Confidence: {float(result['confidence']):.2f}

Institutional Interpretation:
{result['interpretation']}
""",

            "phase_context_block": f"""
===========================
📊 MARKET DISTRIBUTION CONTEXT
===========================

Phase: {result['phase']}
Confidence: {float(result['confidence']):.2f}

{result['interpretation']}
"""
        }

    except Exception as e:
        raise RuntimeError(f"DISTRIBUTION MODULE FAILURE: {str(e)}")