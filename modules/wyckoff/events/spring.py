from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from modules.wyckoff.schemas import TimeframeContext, ManipulationEvent

from modules.wyckoff.common import (
    SPRING,
    LIQUIDITY_SWEEP_LOW,
    STOP_HUNT,
    safe_float,
    clamp_confidence
)

# Volume confirmation engine (external dependency)
try:
    from modules.wyckoff.volume_profile import confirm_volume_profile
except:
    confirm_volume_profile = None


# =========================================================
# CONFIG
# =========================================================

DEFAULT_LOOKBACK = 20
SWEEP_THRESHOLD = 0.0025   # 0.25% below support minimum sweep requirement
MAX_SWEEP_EXTREME = 0.02   # 2% cap for scoring normalization


# =========================================================
# SUPPORT DETECTION (STRUCTURAL)
# =========================================================

def detect_support_level(df: pd.DataFrame, i: int, lookback: int) -> float:
    """
    Rolling structural support = lowest low in lookback window prior to event.
    """
    start = max(0, i - lookback)
    window = df["Low"].iloc[start:i]

    if len(window) == 0:
        return float(df["Low"].iloc[i])

    return float(np.min(window))


# =========================================================
# SPRING LOGIC CORE
# =========================================================

def is_spring_event(
    df: pd.DataFrame,
    i: int,
    support: float
) -> Dict[str, Any]:
    """
    Wyckoff Spring definition:
    - Price sweeps below support (liquidity grab)
    - Closes back above support (reclaim)
    """

    low = safe_float(df["Low"].iloc[i])
    close = safe_float(df["Close"].iloc[i])
    high = safe_float(df["High"].iloc[i])

    swept = low < support * (1 - SWEEP_THRESHOLD)
    reclaimed = close > support

    sweep_depth = max(0.0, support - low)
    sweep_depth_pct = sweep_depth / max(support, 1e-6)

    return {
        "is_spring": swept and reclaimed,
        "sweep_depth": sweep_depth,
        "sweep_depth_pct": sweep_depth_pct,
        "liquidity_event": swept
    }


# =========================================================
# CONFIDENCE SCORING
# =========================================================

def score_spring(
    sweep_depth_pct: float,
    volume_strength: float = 0.0
) -> float:
    """
    Combines:
    - liquidity sweep depth
    - volume confirmation strength
    """

    depth_score = min(sweep_depth_pct / MAX_SWEEP_EXTREME, 1.0)
    volume_score = clamp_confidence(volume_strength)

    score = (depth_score * 0.6) + (volume_score * 0.4)
    return clamp_confidence(score)


# =========================================================
# MAIN DETECTOR
# =========================================================

def detect_springs(
    context: TimeframeContext,
    lookback: int = DEFAULT_LOOKBACK
) -> List[ManipulationEvent]:

    df = context.data.copy().reset_index(drop=True)

    springs: List[ManipulationEvent] = []

    if len(df) < lookback + 5:
        return springs

    for i in range(lookback, len(df)):

        # ----------------------------
        # STEP 1: STRUCTURAL SUPPORT
        # ----------------------------
        support = detect_support_level(df, i, lookback)

        result = is_spring_event(df, i, support)

        if not result["is_spring"]:
            continue

        # ----------------------------
        # STEP 2: VOLUME CONFIRMATION
        # ----------------------------
        volume_strength = 0.0
        volume_meta = {}

        if confirm_volume_profile:
            try:
                vol_result = confirm_volume_profile(
                    df.iloc[:i + 1],
                    lookback=lookback,
                    event_type="SPRING"
                )

                volume_strength = float(vol_result.get("strength", 0.0))
                volume_meta = vol_result

            except:
                volume_strength = 0.0

        # ----------------------------
        # STEP 3: CONFIDENCE SCORING
        # ----------------------------
        confidence = score_spring(
            result["sweep_depth_pct"],
            volume_strength
        )

        # ----------------------------
        # STEP 4: BUILD EVENT
        # ----------------------------
        event = ManipulationEvent(
            event_type=SPRING,
            index=i,
            timestamp=df["timestamp"].iloc[i] if "timestamp" in df.columns else i,
            price=float(df["Close"].iloc[i]),
            timeframe=context.timeframe,
            confidence=confidence,
            volume_confirmed=volume_strength > 0.6,
            metadata={
                "support_level": support,
                "low": float(df["Low"].iloc[i]),
                "high": float(df["High"].iloc[i]),
                "close": float(df["Close"].iloc[i]),
                "sweep_depth": result["sweep_depth"],
                "sweep_depth_pct": result["sweep_depth_pct"],
                "liquidity_event": True,
                "volume_strength": volume_strength,
                "volume_profile": volume_meta,
                "event_tags": [
                    SPRING,
                    LIQUIDITY_SWEEP_LOW,
                    STOP_HUNT
                ]
            }
        )

        springs.append(event)

    return springs


# =========================================================
# OPTIONAL: ATTACH TO CONTEXT
# =========================================================

def attach_springs_to_context(context: TimeframeContext) -> TimeframeContext:
    """
    Convenience pipeline hook.
    """

    context.springs = detect_springs(context)
    return context