import numpy as np
import pandas as pd

from .rangeFinder import detect_range_structure
from .volumeConfirmation import confirm_volume_profile


# =========================================================
# WYCKOFF CONTEXT OBJECT
# =========================================================

def build_context(df, ticker=None):

    return {
        "df": df,
        "ticker": ticker,
        "signals": {
            "range": None,
            "volume": None,
        },
        "state": {},
        "events": [],
        "score": 0.0
    }


# =========================================================
# ORCHESTRATION PIPELINE
# =========================================================

def run_wyckoff_pipeline(df, ticker=None):

    ctx = build_context(df, ticker)

    # -------------------------
    # 1. RANGE STRUCTURE
    # -------------------------
    ctx["signals"]["range"] = detect_range_structure(df)

    # -------------------------
    # 2. VOLUME CONFIRMATION
    # -------------------------
    ctx["signals"]["volume"] = confirm_volume_profile(df)

    # -------------------------
    # 3. BUILD STATE (LIGHTWEIGHT)
    # -------------------------
    ctx["state"] = build_state(ctx)

    # -------------------------
    # 4. SCORE ENGINE
    # -------------------------
    ctx["score"] = compute_score(ctx)

    # -------------------------
    # 5. EVENT GENERATION
    # -------------------------
    ctx["events"] = generate_events(ctx)

    return ctx


# =========================================================
# STATE BUILDER (minimal core)
# =========================================================

def build_state(ctx):

    range_sig = ctx["signals"]["range"]
    vol_sig = ctx["signals"]["volume"]

    return {
        "range_quality": range_sig.get("quality", 0.0) if range_sig else 0.0,
        "is_in_range": range_sig.get("in_range", False) if range_sig else False,
        "volume_strength": vol_sig.get("strength", 0.0) if vol_sig else 0.0,
        "absorption": vol_sig.get("absorption", 0.0) if vol_sig else 0.0,
    }


# =========================================================
# SCORE ENGINE (Wyckoff alignment score)
# =========================================================

def compute_score(ctx):

    s = ctx["state"]

    return float(
        s["range_quality"] * 0.35 +
        s["volume_strength"] * 0.35 +
        s["absorption"] * 0.20 +
        (1.0 if s["is_in_range"] else 0.0) * 0.10
    )


# =========================================================
# EVENT GENERATION (simple initial version)
# =========================================================

def generate_events(ctx):

    events = []

    s = ctx["state"]

    if s["is_in_range"] and s["volume_strength"] > 0.6:
        events.append({
            "type": "WYCKOFF_ACTIVITY",
            "detail": "Active range with strong volume participation",
            "score": ctx["score"]
        })

    if s["absorption"] > 0.7:
        events.append({
            "type": "ABSORPTION",
            "detail": "Potential accumulation absorption detected",
            "score": ctx["score"]
        })

    return events