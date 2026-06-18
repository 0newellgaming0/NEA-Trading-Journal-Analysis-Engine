# =========================================================
# INSTITUTIONAL LIQUIDITY PHASE ENGINE (V3 - AUCTION MODEL)
# FIXED FOR JOURNAL INTEGRATION STABILITY
# =========================================================

import numpy as np

from modules.price_discovery_status import calculate_price_discovery_status
from modules.discovery_phase import detect_discovery_phase
from modules.expansion_phase import detect_expansion_phase
from modules.acceptance_phase import detect_acceptance_phase
from modules.exhaustion_phase import detect_exhaustion_phase
from modules.distribution_phase import detect_distribution_phase


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0


# =========================================================
# TIMEFRAME CONTEXT (FIXED: ALWAYS DICT OUTPUT)
# =========================================================

def infer_timeframe_context(df_meta=None):

    tf = "1D"

    if isinstance(df_meta, dict) and "timeframe" in df_meta:
        tf = df_meta["timeframe"]

    tf = str(tf)

    tf_map = {
        "15m": ("EXECUTION / MICRO STRUCTURE", "15m"),
        "60m": ("TACTICAL STRUCTURE", "60m"),
        "1D": ("SWING STRUCTURE (ANCHOR)", "1D"),
        "1W": ("MACRO REGIME FILTER", "1W")
    }

    role, normalized = tf_map.get(tf, ("UNKNOWN STRUCTURE LAYER", tf))

    return {
        "timeframe": normalized,
        "role": role
    }


# =========================================================
# PHASE SCORING CORE
# =========================================================

def wrap_phase(name, result):

    if not isinstance(result, dict):
        return {
            "phase": name,
            "score": 0.0,
            "status": "FAIL",
            "interpretation": "Invalid module output"
        }

    score = safe_float(result.get("confidence", 0))
    interpretation = result.get("interpretation", "")

    return {
        "phase": name,
        "score": score,
        "status": "PASS" if score >= 0.70 else "FAIL",
        "interpretation": interpretation
    }


# =========================================================
# AUCTION REGIME CLASSIFIER
# =========================================================

def classify_regime(scores):

    values = {p["phase"]: p["score"] for p in scores}

    acceptance = values.get("ACCEPTANCE", 0)
    discovery = values.get("DISCOVERY", 0)
    expansion = values.get("EXPANSION", 0)
    exhaustion = values.get("EXHAUSTION", 0)
    distribution = values.get("DISTRIBUTION", 0)

    if acceptance >= 0.70:
        return "BALANCED_AUCTION"

    if discovery >= expansion:
        return "TRANSITION_DISCOVERY"

    if expansion >= 0.70:
        return "TREND_EXPANSION"

    if exhaustion >= 0.70:
        return "LATE_CYCLE_EXHAUSTION"

    if distribution >= 0.70:
        return "DISTRIBUTION_RISK"

    return "TRANSITION_REGIME"


# =========================================================
# ACTIVE PHASE
# =========================================================

def select_active_phase(scores):

    valid = [p for p in scores if p["score"] > 0]

    if not valid:
        return "NO_STRUCTURE", 0.0

    best = max(valid, key=lambda x: x["score"])

    return best["phase"], best["score"]


# =========================================================
# MAIN ENGINE
# =========================================================

def run_price_phase_analysis(df, df_meta=None):

    tf_context = infer_timeframe_context(df_meta)

    context_score = safe_float(
        calculate_price_discovery_status(df).get("confidence", 0)
    )

    phases = [
        wrap_phase("DISCOVERY", detect_discovery_phase(df)),
        wrap_phase("EXPANSION", detect_expansion_phase(df)),
        wrap_phase("ACCEPTANCE", detect_acceptance_phase(df)),
        wrap_phase("EXHAUSTION", detect_exhaustion_phase(df)),
        wrap_phase("DISTRIBUTION", detect_distribution_phase(df)),
    ]

    regime = classify_regime(phases)
    active_phase, active_conf = select_active_phase(phases)

    structural_strength = (
        active_conf * 0.7 +
        context_score * 0.3
    )

    return {
        "timeframe": tf_context,   # ALWAYS dict now
        "regime": regime,
        "active_phase": active_phase,
        "confidence": active_conf,
        "context_score": context_score,
        "structural_strength": structural_strength,
        "phases": phases
    }


# =========================================================
# CONTEXT BLOCK (SAFE + JOURNAL STABLE)
# =========================================================

def build_phase_context_block(result):

    tf = result.get("timeframe", {})

    tf_name = tf.get("timeframe", "UNKNOWN")
    tf_role = tf.get("role", "UNKNOWN STRUCTURE LAYER")

    return f"""
===========================
📊 MARKET LIQUIDITY REGIME
===========================

Timeframe:
{tf_name} — {tf_role}

Regime:
{result.get('regime','N/A')}

Active Phase:
{result.get('active_phase','N/A')}

Confidence:
{result.get('confidence',0.0):.2f}

Context Score:
{result.get('context_score',0.0):.2f}

Structural Strength:
{result.get('structural_strength',0.0):.2f}

Interpretation:
Market is an auction system operating across liquidity states.
All phases represent competing structural hypotheses, not absolute states.
"""


# =========================================================
# PIPELINE OUTPUT
# =========================================================

def build_liquidity_block(result):

    tf = result.get("timeframe", {})

    lines = []
    lines.append("📊 LIQUIDITY PHASE ANALYSIS")
    lines.append("--------------------------")
    lines.append("")
    lines.append(f"TIMEFRAME: {tf.get('timeframe','N/A')}")
    lines.append(f"REGIME: {result.get('regime','N/A')}")
    lines.append(f"ACTIVE PHASE: {result.get('active_phase','N/A')}")
    lines.append(f"CONTEXT SCORE: {result.get('context_score',0.0):.2f}")
    lines.append(f"STRUCTURAL STRENGTH: {result.get('structural_strength',0.0):.2f}")
    lines.append("")
    lines.append("PHASE SCORES:")
    lines.append("")

    for p in result.get("phases", []):

        symbol = "✓" if p.get("status") == "PASS" else "·"

        lines.append(f"{symbol} {p.get('phase')} → {p.get('score',0.0):.2f}")

        if p.get("interpretation"):
            lines.append(f"  {p['interpretation']}")

        lines.append("")

    return "\n".join(lines)


# =========================================================
# ENTRY POINT
# =========================================================

def run_liquidity_phase_engine(df, df_meta=None):

    result = run_price_phase_analysis(df, df_meta)

    return {
        "liquidity_block": build_liquidity_block(result),
        "phase_context_block": build_phase_context_block(result),

        "timeframe": result["timeframe"],
        "regime": result["regime"],
        "active_phase": result["active_phase"],
        "confidence": result["confidence"],
        "context_score": result["context_score"],
        "structural_strength": result["structural_strength"],
        "raw": result
    }