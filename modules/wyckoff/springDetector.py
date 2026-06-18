import numpy as np
import pandas as pd

from modules.wyckoff.schemas import (
    ManipulationEvent,
    TimeframeContext,
    TradingRange
)

from modules.wyckoff.common import (
    SPRING
)

from modules.wyckoff.volumeConfirmation import (
    confirm_volume_profile
)

# =========================================================
# SPRING PARAMETERS (STRUCTURAL THRESHOLDS)
# =========================================================

SPRING_BUFFER = 0.0015
RECLAIM_BUFFER = 0.0010

MIN_VOLUME_STRENGTH = 0.45
MIN_ABSORPTION = 0.35


# =========================================================
# RANGE ACCESSOR (SAFE)
# =========================================================

def get_latest_range(context: TimeframeContext) -> TradingRange:
    return context.ranges[-1] if context.ranges else None


# =========================================================
# VOLUME VALIDATION (INSTITUTIONAL FILTER)
# =========================================================

def volume_confirmed(df: pd.DataFrame) -> bool:
    profile = confirm_volume_profile(df)

    strength = profile.get("strength", 0.0)
    absorption = profile.get("absorption", 0.0)

    return (strength >= MIN_VOLUME_STRENGTH) or (absorption >= MIN_ABSORPTION)


# =========================================================
# STRUCTURAL CONDITIONS
# =========================================================

def is_sweep(low_price: float, range_low: float) -> bool:
    return low_price < range_low * (1 - SPRING_BUFFER)


def is_reclaim(close_price: float, range_low: float) -> bool:
    return close_price > range_low * (1 + RECLAIM_BUFFER)


# =========================================================
# SPRING DETECTOR (CANONICAL PIPELINE ENGINE)
# =========================================================

def detect_springs(context: TimeframeContext):

    df = context.data
    range_obj = get_latest_range(context)

    if range_obj is None or len(df) < 2:
        return []

    range_low = range_obj.range_low
    range_high = range_obj.range_high

    vol_ok = volume_confirmed(df)
    range_size = max(range_high - range_low, 1e-6)

    springs = []

    lows = df["Low"].values
    closes = df["Close"].values

    for i in range(1, len(df)):

        swept = is_sweep(lows[i], range_low)
        reclaimed = is_reclaim(closes[i], range_low)

        if not (swept and reclaimed):
            continue

        displacement = abs(closes[i] - lows[i])
        raw_strength = min(1.0, displacement / range_size)

        # institutional scaling
        strength = raw_strength * (1.2 if vol_ok else 0.7)

        event = ManipulationEvent(
            event_type=SPRING,   # ✅ canonical constant (NO STRING DRIFT)
            index=i,
            timestamp=df["timestamp"].iloc[i],
            price=float(closes[i]),
            timeframe=context.timeframe,
            confidence=round(strength, 4),
            volume_confirmed=vol_ok,
            metadata={
                "range_low": range_low,
                "range_high": range_high,
                "swept": True,
                "reclaimed": True
            }
        )

        springs.append(event)

    # =====================================================
    # PIPELINE STATE INJECTION (CRITICAL FIX)
    # =====================================================

    context.springs.extend(springs)

    return springs