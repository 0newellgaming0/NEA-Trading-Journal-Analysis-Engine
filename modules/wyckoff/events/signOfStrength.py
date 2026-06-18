from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from modules.wyckoff.schemas import (
    FractalPoint,
    BreakoutEvent,
    TimeframeContext,
)

from modules.wyckoff.common import (
    FRACTAL_HIGH,
    FRACTAL_LOW,

    BREAKOUT,
    SOS,

    DEMAND_OVERCOMING_SUPPLY,
    CONFIRMED_BREAKOUT_VOLUME,
    WEAK_BREAKOUT_VOLUME,
)

from modules.wyckoff.volume import confirm_volume_profile


# =========================================================
# CONFIG
# =========================================================

LOOKBACK_VOLUME = 20
MIN_SOS_CONFIDENCE = 0.70


# =========================================================
# SAFE UTIL
# =========================================================

def safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


# =========================================================
# STRUCTURAL HELPERS
# =========================================================

def get_last_swing_high(fractals: List[FractalPoint]) -> Optional[FractalPoint]:
    for f in reversed(fractals):
        if f.fractal_type == FRACTAL_HIGH:
            return f
    return None


def get_prior_range_high(fractals: List[FractalPoint], current_index: int, lookback: int = 20) -> float:
    relevant = [f.price for f in fractals if f.index < current_index][-lookback:]
    return max(relevant) if relevant else 0.0


def detect_breakout(close: float, range_high: float) -> bool:
    return close > range_high if range_high > 0 else False


# =========================================================
# SOS CORE DETECTION (STRUCTURE ONLY)
# =========================================================

def detect_sos_structure(
    df: pd.DataFrame,
    fractals: List[FractalPoint],
    i: int
) -> Dict[str, Any]:

    close = safe_float(df["Close"].iloc[i])
    high = safe_float(df["High"].iloc[i])

    range_high = get_prior_range_high(fractals, i)

    breakout = detect_breakout(close, range_high)

    last_high = get_last_swing_high(fractals)

    structure_strength = 0.0

    # 1. Break above prior structure
    if breakout:
        structure_strength += 0.4

    # 2. Higher high confirmation
    if last_high and high > last_high.price:
        structure_strength += 0.2

    # 3. Expansion beyond range
    if range_high > 0 and (high - range_high) / range_high > 0.01:
        structure_strength += 0.2

    return {
        "breakout": breakout,
        "structure_strength": structure_strength,
        "range_high": range_high,
        "last_swing_high": last_high.price if last_high else None
    }


# =========================================================
# VOLUME CONFIRMATION WRAPPER
# =========================================================

def confirm_sos_volume(df: pd.DataFrame, i: int) -> Dict[str, Any]:

    volume_result = confirm_volume_profile(
        df=df.iloc[:i + 1],
        lookback=LOOKBACK_VOLUME,
        breakout_direction="UP",
        event_type="SPRING"
    )

    strength = volume_result.get("strength", 0.0)

    return {
        "volume_strength": strength,
        "confirmed": strength >= 0.65,
        "raw": volume_result
    }


# =========================================================
# FINAL SOS SCORING ENGINE
# =========================================================

def compute_sos_score(structure: Dict, volume: Dict) -> float:

    score = 0.0

    # structure weight
    score += structure["structure_strength"]

    # breakout must exist
    if structure["breakout"]:
        score += 0.3

    # volume confirmation
    if volume["confirmed"]:
        score += 0.3
    else:
        score += volume["volume_strength"] * 0.2

    return float(np.clip(score, 0.0, 1.0))


# =========================================================
# MAIN ENGINE (SOS ONLY)
# =========================================================

def detect_signs_of_strength(context: TimeframeContext) -> Dict[str, Any]:

    df = context.data
    fractals = context.fractals

    sos_events = []

    if len(df) < 30 or len(fractals) < 10:
        return {
            "valid": False,
            "events": [],
            "strength": 0.0,
            "bias": "NEUTRAL"
        }

    for i in range(20, len(df)):

        structure = detect_sos_structure(df, fractals, i)

        if not structure["breakout"]:
            continue

        volume = confirm_sos_volume(df, i)

        score = compute_sos_score(structure, volume)

        if score < MIN_SOS_CONFIDENCE:
            continue

        event = {
            "event_type": SOS,
            "index": i,
            "timestamp": df["timestamp"].iloc[i] if "timestamp" in df else None,
            "price": safe_float(df["Close"].iloc[i]),
            "confidence": score,
            "breakout_level": structure["range_high"],
            "volume_confirmed": volume["confirmed"],
            "metadata": {
                "structure_strength": structure["structure_strength"],
                "volume_strength": volume["volume_strength"],
                "last_swing_high": structure["last_swing_high"],
                "volume_detail": volume["raw"]
            }
        }

        sos_events.append(event)

    # ============================
    # FINAL CONTEXT UPDATE
    # ============================

    context.events.extend(sos_events)

    strongest = max([e["confidence"] for e in sos_events], default=0.0)

    context.score = strongest
    context.bias = "BULLISH" if strongest >= 0.75 else "NEUTRAL"

    return {
        "valid": len(sos_events) > 0,
        "strength": strongest,
        "bias": context.bias,
        "events": sos_events
    }