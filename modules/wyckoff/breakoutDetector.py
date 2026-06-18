import numpy as np
import pandas as pd

from modules.wyckoff.schemas import (
    BreakoutEvent,
    TimeframeContext
)

from modules.wyckoff.volumeConfirmation import (
    confirm_volume_profile
)

from modules.wyckoff.common import (
    FRACTAL_HIGH,
    FRACTAL_LOW
)

# =========================================================
# BREAKOUT THRESHOLDS (STRUCTURAL ONLY)
# =========================================================

BREAKOUT_BUFFER = 0.001  # structural tolerance (0.1%)
FALSE_BREAK_BUFFER = 0.0025

MIN_VOLUME_STRENGTH = 0.45
MIN_ABSORPTION = 0.35

# =========================================================
# RANGE EXTRACTION HELPERS
# =========================================================

def get_latest_range(context: TimeframeContext):
    """
    Uses last known range from rangeFinder output.
    """
    if context.ranges:
        return context.ranges[-1]
    return None


# =========================================================
# WAVE ALIGNMENT FILTER (NO ROLE INTERPRETATION)
# =========================================================

def wave_alignment_ok(context: TimeframeContext, direction: str):
    """
    Pure structural wave confirmation:
    - Does NOT interpret meaning
    - Only checks directional wave support
    """

    if not context.waves or len(context.waves) < 2:
        return False

    last_wave = context.waves[-1]

    # upward breakout requires upward wave structure
    if direction == "UP":
        return last_wave.end_price >= last_wave.start_price

    if direction == "DOWN":
        return last_wave.end_price <= last_wave.start_price

    return False


# =========================================================
# VOLUME CONFIRMATION WRAPPER
# =========================================================

def volume_ok(df: pd.DataFrame):
    """
    Uses institutional volume profile logic only.
    """

    profile = confirm_volume_profile(df)

    strength = profile.get("strength", 0.0)
    absorption = profile.get("absorption", 0.0)

    return (
        strength >= MIN_VOLUME_STRENGTH
        or absorption >= MIN_ABSORPTION
    )


# =========================================================
# BREAKOUT VALIDATION CORE
# =========================================================

def evaluate_breakout(price, level, direction):
    """
    Structural breakout validation only.
    """

    if direction == "UP":
        return price > level * (1 + BREAKOUT_BUFFER)

    if direction == "DOWN":
        return price < level * (1 - BREAKOUT_BUFFER)

    return False


def evaluate_false_break(price, level, direction):
    """
    Detects weak structural failure through reversal proximity.
    """

    if direction == "UP":
        return price < level * (1 - FALSE_BREAK_BUFFER)

    if direction == "DOWN":
        return price > level * (1 + FALSE_BREAK_BUFFER)

    return False


# =========================================================
# BREAKOUT DETECTOR (MAIN ENGINE)
# =========================================================

def detect_breakouts(context: TimeframeContext):

    df = context.data

    range_obj = get_latest_range(context)

    if range_obj is None:
        return {
            "breakouts": [],
            "false_breakouts": [],
            "false_breakdowns": []
        }

    breakouts = []
    false_breakouts = []
    false_breakdowns = []

    level_high = range_obj.range_high
    level_low = range_obj.range_low

    latest_price = float(df["Close"].iloc[-1])

    # =====================================================
    # UPWARD BREAKOUT LOGIC
    # =====================================================

    if evaluate_breakout(latest_price, level_high, "UP"):

        wave_ok = wave_alignment_ok(context, "UP")
        vol_ok = volume_ok(df)

        if wave_ok and vol_ok:

            breakouts.append(
                BreakoutEvent(
                    event_type="BREAKOUT",
                    index=len(df) - 1,
                    timestamp=df["timestamp"].iloc[-1],
                    price=latest_price,
                    breakout_level=level_high,
                    timeframe=context.timeframe,
                    confidence=0.85,
                    volume_confirmed=True,
                    institutional_confirmed=True,
                    metadata={
                        "direction": "UP"
                    }
                )
            )

        else:

            false_breakouts.append(
                BreakoutEvent(
                    event_type="FALSE_BREAKOUT",
                    index=len(df) - 1,
                    timestamp=df["timestamp"].iloc[-1],
                    price=latest_price,
                    breakout_level=level_high,
                    timeframe=context.timeframe,
                    confidence=0.40,
                    volume_confirmed=vol_ok,
                    institutional_confirmed=False,
                    metadata={
                        "direction": "UP",
                        "wave_ok": wave_ok
                    }
                )
            )

    # =====================================================
    # DOWNWARD BREAKOUT LOGIC
    # =====================================================

    if evaluate_breakout(latest_price, level_low, "DOWN"):

        wave_ok = wave_alignment_ok(context, "DOWN")
        vol_ok = volume_ok(df)

        if wave_ok and vol_ok:

            breakouts.append(
                BreakoutEvent(
                    event_type="BREAKOUT",
                    index=len(df) - 1,
                    timestamp=df["timestamp"].iloc[-1],
                    price=latest_price,
                    breakout_level=level_low,
                    timeframe=context.timeframe,
                    confidence=0.85,
                    volume_confirmed=True,
                    institutional_confirmed=True,
                    metadata={
                        "direction": "DOWN"
                    }
                )
            )

        else:

            false_breakdowns.append(
                BreakoutEvent(
                    event_type="FALSE_BREAKDOWN",
                    index=len(df) - 1,
                    timestamp=df["timestamp"].iloc[-1],
                    price=latest_price,
                    breakout_level=level_low,
                    timeframe=context.timeframe,
                    confidence=0.40,
                    volume_confirmed=vol_ok,
                    institutional_confirmed=False,
                    metadata={
                        "direction": "DOWN",
                        "wave_ok": wave_ok
                    }
                )
            )

    # =====================================================
    # RETURN STRUCTURED OUTPUT
    # =====================================================

    return {
        "breakouts": breakouts,
        "false_breakouts": false_breakouts,
        "false_breakdowns": false_breakdowns
    }