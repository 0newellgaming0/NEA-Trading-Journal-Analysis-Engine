# =========================================================
# MULTI-TIMEFRAME LIQUIDITY PHASE ENGINE (INSTITUTIONAL CORE)
# =========================================================

import numpy as np

from modules.liquidity_phase_engine import run_price_phase_analysis


# =========================================================
# SAFE UTIL
# =========================================================

def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0


# =========================================================
# RUN SINGLE TIMEFRAME WRAPPER
# =========================================================

def analyze_timeframe(df, df_meta=None):
    """
    Runs single-timeframe liquidity phase engine safely.
    """

    if df is None:
        return None

    try:
        return run_price_phase_analysis(df, df_meta)
    except Exception as e:
        return {
            "error": str(e),
            "regime": "ERROR",
            "active_phase": "ERROR",
            "confidence": 0.0,
            "context_score": 0.0,
            "phases": []
        }


# =========================================================
# INFLUENCE LAYER ENGINE
# =========================================================

def compute_influence_layer(results):
    """
    Converts multi-timeframe outputs into weighted influence model.
    """

    weights = {
        "15m": 0.15,
        "60m": 0.25,
        "1D": 0.40,
        "weekly": 0.20
    }

    influence = {
        "15m": 0.0,
        "60m": 0.0,
        "1D": 0.0,
        "weekly": 0.0
    }

    for tf, data in results.items():

        if not data:
            continue

        confidence = safe_float(data.get("confidence", 0.0))
        context = safe_float(data.get("context_score", 0.0))

        # blended structural strength
        strength = (confidence * 0.7) + (context * 0.3)

        influence[tf] = round(strength * weights.get(tf, 0.0), 4)

    return influence


# =========================================================
# MACRO REGIME CLASSIFIER
# =========================================================

def classify_macro(influence, results):
    """
    Determines overall regime bias from multi-timeframe structure.
    """

    total_influence = sum(influence.values())

    if total_influence == 0:
        return "NO_STRUCTURAL_DATA"

    # Directional bias estimation
    bullish_score = 0
    bearish_score = 0

    for tf, data in results.items():

        if not data:
            continue

        regime = data.get("regime", "")

        if "EXPANSION" in regime or "TREND" in regime:
            bullish_score += influence.get(tf, 0)

        if "DISTRIBUTION" in regime or "EXHAUSTION" in regime:
            bearish_score += influence.get(tf, 0)

    # Macro decision logic
    if bullish_score > bearish_score * 1.25:
        return "BULLISH_EXPANSION_BIAS"

    if bearish_score > bullish_score * 1.25:
        return "BEARISH_DISTRIBUTION_BIAS"

    if abs(bullish_score - bearish_score) < 0.05:
        return "BALANCED_AUCTION"

    return "TRANSITIONAL_STRUCTURE"


# =========================================================
# MAIN ENGINE
# =========================================================

def run_liquidity_multi_timeframe_engine(timeframes):
    """
    Master orchestrator:
    - runs all timeframes
    - computes influence layer
    - computes macro regime
    - returns structured institutional output
    """

    results = {}

    # =====================================================
    # RUN EACH TIMEFRAME
    # =====================================================

    for tf, df in timeframes.items():

        results[tf] = analyze_timeframe(
            df,
            df_meta={"timeframe": tf}
        )

    # =====================================================
    # INFLUENCE LAYER
    # =====================================================

    influence = compute_influence_layer(results)

    # =====================================================
    # MACRO REGIME
    # =====================================================

    macro = classify_macro(influence, results)

    # =====================================================
    # TIMEFRAME DISPLAY BLOCKS (ENGINE OWNED)
    # =====================================================

    liquidity_block = build_liquidity_block(results)

    phase_context_block = build_phase_context_block(results, macro)

    # =====================================================
    # FINAL OUTPUT
    # =====================================================

    return {
        "timeframes": results,
        "influence": influence,
        "macro_interpretation": macro,
        "liquidity_block": liquidity_block,
        "phase_context_block": phase_context_block
    }


# =========================================================
# DISPLAY BUILDER (ENGINE RESPONSIBILITY)
# =========================================================

def build_liquidity_block(results):

    lines = []
    lines.append("📊 MULTI-TIMEFRAME LIQUIDITY STRUCTURE")
    lines.append("--------------------------------------")

    for tf, data in results.items():

        if not data:
            lines.append(f"\n{tf}: NO DATA")
            continue

        lines.append(f"\n{tf}")
        lines.append(f"- Regime: {data.get('regime','N/A')}")
        lines.append(f"- Active Phase: {data.get('active_phase','N/A')}")
        lines.append(f"- Confidence: {data.get('confidence',0):.2f}")
        lines.append(f"- Context Score: {data.get('context_score',0):.2f}")

    return "\n".join(lines)


# =========================================================
# CONTEXT BUILDER (ENGINE RESPONSIBILITY)
# =========================================================

def build_phase_context_block(results, macro):

    return f"""
===========================
📊 LIQUIDITY REGIME CONTEXT
===========================

Macro Regime:
{macro}

===========================
TIMEFRAME STRUCTURE SUMMARY
===========================

15m: {results.get("15m", {}).get("regime", "N/A")}
60m: {results.get("60m", {}).get("regime", "N/A")}
Daily: {results.get("1D", {}).get("regime", "N/A")}
Weekly: {results.get("weekly", {}).get("regime", "N/A")}

Interpretation:
Market is a multi-layer auction system where
lower timeframes define execution timing and
higher timeframes define structural bias.
"""