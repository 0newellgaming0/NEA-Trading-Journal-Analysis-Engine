import numpy as np
import pandas as pd

from modules.wyckoff.schemas import (
    BreakoutEvent,
    TimeframeContext
)

from modules.wyckoff.volumeConfirmation import (
    confirm_volume_profile
)

# =========================================================
# STRUCTURAL PARAMETERS (EVENT LAYER ONLY)
# =========================================================

BREAKOUT_BUFFER = 0.001  # structural breach threshold

MIN_VOLUME_STRENGTH = 0.45
MIN_ABSORPTION = 0.35

# =========================================================
# RANGE ACCESSOR (FROM rangeFinder OUTPUT)
# =========================================================

def get_latest_range(context: TimeframeContext):
    if context.ranges:
        return context.ranges[-1]
    return None


# =========================================================
# VOLUME CONFIRMATION (INSTITUTIONAL FILTER ONLY)
# =========================================================

def volume_ok(df: pd.DataFrame) -> bool:
    profile = confirm_volume_profile(df)

    return (
        profile.get("strength", 0.0) >= MIN_VOLUME_STRENGTH
        or profile.get("absorption", 0.0) >= MIN_ABSORPTION
    )


# =========================================================
# STRUCTURAL BREAK CONDITION (PURE LOGIC)
# =========================================================

def is_breakout(price: float, level: float, direction: str) -> bool:

    if direction == "UP":
        return price > level * (1 + BREAKOUT_BUFFER)

    if direction == "DOWN":
        return price < level * (1 - BREAKOUT_BUFFER)

    return False


# =========================================================
# MAIN BREAKOUT EVENT EMITTER
# =========================================================

def detect_breakouts(context: TimeframeContext):
    """
    PURE EVENT EMITTER
    - No classification
    - No false breakout logic
    - No decision branching
    - Only emits BreakoutEvent when structure + volume align
    """

    df = context.data
    range_obj = get_latest_range(context)

    if range_obj is None or len(df) < 2:
        return []

    latest_price = float(df["Close"].iloc[-1])
    timestamp = df["timestamp"].iloc[-1]
    index = len(df) - 1

    vol_ok = volume_ok(df)

    events = []

    # =====================================================
    # UPWARD BREAKOUT EVENT
    # =====================================================

    if is_breakout(latest_price, range_obj.range_high, "UP"):

        events.append(
            BreakoutEvent(
                event_type="BREAKOUT",
                index=index,
                timestamp=timestamp,
                price=latest_price,
                breakout_level=range_obj.range_high,
                timeframe=context.timeframe,
                confidence=0.75 if vol_ok else 0.55,
                volume_confirmed=vol_ok,
                institutional_confirmed=vol_ok,
                metadata={
                    "direction": "UP",
                    "range_low": range_obj.range_low,
                    "range_high": range_obj.range_high
                }
            )
        )

    # =====================================================
    # DOWNWARD BREAKOUT EVENT
    # =====================================================

    if is_breakout(latest_price, range_obj.range_low, "DOWN"):

        events.append(
            BreakoutEvent(
                event_type="BREAKOUT",
                index=index,
                timestamp=timestamp,
                price=latest_price,
                breakout_level=range_obj.range_low,
                timeframe=context.timeframe,
                confidence=0.75 if vol_ok else 0.55,
                volume_confirmed=vol_ok,
                institutional_confirmed=vol_ok,
                metadata={
                    "direction": "DOWN",
                    "range_low": range_obj.range_low,
                    "range_high": range_obj.range_high
                }
            )
        )

    return events