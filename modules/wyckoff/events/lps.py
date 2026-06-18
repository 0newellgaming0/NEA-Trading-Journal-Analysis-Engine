# =========================================================
# LPS DETECTOR (WYCKOFF ONLY)
# =========================================================

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from modules.wyckoff.schemas import TimeframeContext, MarketEvent
from modules.wyckoff.common import (
    LPS,
    BREAKOUT,
    FRACTAL_HIGH,
    FRACTAL_LOW
)

from modules.wyckoff.volume import confirm_volume_profile


# =========================================================
# SAFE UTIL
# =========================================================

def safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


# =========================================================
# SWING LOW / HIGH HELPERS
# =========================================================

def extract_swing_lows(fractals):
    return [f for f in fractals if f.fractal_type == FRACTAL_LOW]


def extract_swing_highs(fractals):
    return [f for f in fractals if f.fractal_type == FRACTAL_HIGH]


# =========================================================
# CORE LPS LOGIC
# =========================================================

def detect_lps(
    context: TimeframeContext,
    lookahead: int = 10,
    tolerance: float = 0.002,   # 0.2% retest tolerance
    volume_lookback: int = 20
) -> Dict[str, Any]:
    """
    Detect Wyckoff LPS (Last Point of Support) events only.
    """

    df = context.data
    fractals = context.fractals
    breakouts = context.breakouts

    if df is None or len(df) < 20:
        return {"valid": False, "events": []}

    swing_lows = extract_swing_lows(fractals)

    lps_events: List[MarketEvent] = []

    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values

    # =====================================================
    # LOOP THROUGH BREAKOUTS (PRIMARY TRIGGER)
    # =====================================================
    for bo in breakouts:

        if bo.event_type != BREAKOUT:
            continue

        breakout_level = safe_float(bo.price)
        breakout_index = bo.index

        # look forward after breakout
        end = min(len(df), breakout_index + lookahead)

        if breakout_index >= len(df) - 2:
            continue

        # =================================================
        # SEARCH FOR RETEST STRUCTURE
        # =================================================
        for i in range(breakout_index + 1, end):

            price = close[i]

            # ---------------------------------------------
            # LPS CONDITION 1:
            # Retest near breakout level (support zone)
            # ---------------------------------------------
            in_support_zone = abs(price - breakout_level) / breakout_level <= tolerance

            # ---------------------------------------------
            # LPS CONDITION 2:
            # Must NOT break below support
            # ---------------------------------------------
            holds_support = low[i] >= breakout_level * (1 - tolerance * 2)

            # ---------------------------------------------
            # LPS CONDITION 3:
            # Prefer higher low vs recent swing structure
            # ---------------------------------------------
            higher_low = True
            if swing_lows:
                last_swing_low = swing_lows[-1].price
                higher_low = price >= last_swing_low

            # ---------------------------------------------
            # VOLUME CONFIRMATION (OPTIONAL)
            # ---------------------------------------------
            volume_confirmed = False
            try:
                vol_profile = confirm_volume_profile(
                    df.iloc[:i+1],
                    lookback=volume_lookback
                )
                volume_confirmed = (
                    vol_profile.get("rvol", 1.0) < 1.2 and
                    vol_profile.get("absorption_detected", False) is False
                )
            except:
                volume_confirmed = False

            # ---------------------------------------------
            # FINAL LPS VALIDATION
            # ---------------------------------------------
            if in_support_zone and holds_support and higher_low:

                confidence = 0.5

                if volume_confirmed:
                    confidence += 0.3

                if higher_low:
                    confidence += 0.2

                confidence = min(confidence, 1.0)

                lps_events.append(
                    MarketEvent(
                        event_type=LPS,
                        index=i,
                        timestamp=df["timestamp"].iloc[i] if "timestamp" in df.columns else None,
                        price=float(price),
                        timeframe=bo.timeframe,
                        confidence=confidence,
                        volume_confirmed=volume_confirmed,
                        metadata={
                            "breakout_level": breakout_level,
                            "breakout_index": breakout_index,
                            "retest": True,
                            "structure": "WYCKOFF_LPS"
                        }
                    )
                )

                # one LPS per breakout (avoid clustering noise)
                break

    # =====================================================
    # OUTPUT
    # =====================================================

    return {
        "valid": len(lps_events) > 0,
        "count": len(lps_events),
        "events": lps_events
    }