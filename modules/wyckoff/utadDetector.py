import numpy as np
import pandas as pd

from modules.wyckoff.schemas import (
    ManipulationEvent,
    TimeframeContext,
    TradingRange
)

from modules.wyckoff.common import (
    UTAD
)

from modules.wyckoff.volumeConfirmation import (
    confirm_volume_profile
)

# =========================================================
# UTAD PARAMETERS (STRUCTURAL ONLY)
# =========================================================

UTAD_BUFFER = 0.0015
REJECT_BUFFER = 0.0010

MIN_VOLUME_STRENGTH = 0.45
MIN_ABSORPTION = 0.35


# =========================================================
# RANGE ACCESSOR (SAFE)
# =========================================================

def get_latest_range(context: TimeframeContext) -> TradingRange:
    return context.ranges[-1] if context.ranges else None


# =========================================================
# VOLUME CONFIRMATION (INSTITUTIONAL FILTER)
# =========================================================

def volume_confirmed(df: pd.DataFrame) -> bool:
    profile = confirm_volume_profile(df)

    strength = profile.get("strength", 0.0)
    absorption = profile.get("absorption", 0.0)

    return (strength >= MIN_VOLUME_STRENGTH) or (absorption >= MIN_ABSORPTION)


# =========================================================
# STRUCTURAL CONDITIONS
# =========================================================

def is_sweep(high_price: float, range_high: float) -> bool:
    return high_price > range_high * (1 + UTAD_BUFFER)


def is_rejection(close_price: float, range_high: float) -> bool:
    return close_price < range_high * (1 - REJECT_BUFFER)


# =========================================================
# UTAD DETECTOR (CANONICAL ENGINE)
# =========================================================

def detect_utads(context: TimeframeContext):

    df = context.data
    range_obj = get_latest_range(context)

    if range_obj is None or len(df) < 2:
        return []

    range_low = range_obj.range_low
    range_high = range_obj.range_high

    vol_ok = volume_confirmed(df)
    range_size = max(range_high - range_low, 1e-6)

    utads = []

    highs = df["High"].values
    closes = df["Close"].values

    for i in range(1, len(df)):

        swept = is_sweep(highs[i], range_high)
        rejected = is_rejection(closes[i], range_high)

        if not (swept and rejected):
            continue

        displacement = abs(highs[i] - closes[i])
        raw_strength = min(1.0, displacement / range_size)

        strength = raw_strength * (1.2 if vol_ok else 0.7)

        event = ManipulationEvent(
            event_type=UTAD,   # ✅ canonical constant (no string drift)
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
                "rejected": True
            }
        )

        utads.append(event)

    # =====================================================
    # PIPELINE STATE INJECTION (CRITICAL FIX)
    # =====================================================

    context.utads.extend(utads)

    return utads