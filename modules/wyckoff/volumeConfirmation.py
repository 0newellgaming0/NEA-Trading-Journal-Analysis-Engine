import numpy as np
import pandas as pd

from modules.wyckoff.common import (
    safe_float,
    safe_mean,
    clamp_confidence,
    normalize_volume,

    LOW_VOLUME,
    NORMAL_VOLUME,
    HIGH_VOLUME,
    CLIMACTIC_VOLUME,

    RVOL_LOW,
    RVOL_NORMAL,
    RVOL_HIGH,
    RVOL_EXTREME,

    WEAK_PARTICIPATION,
    NEUTRAL_PARTICIPATION,
    STRONG_PARTICIPATION,
    INSTITUTIONAL_PARTICIPATION,

    VOLUME_EXPANDING,
    VOLUME_CONTRACTING,
    VOLUME_NEUTRAL,

    PRICE_UP_VOLUME_UP,
    PRICE_UP_VOLUME_DOWN,
    PRICE_DOWN_VOLUME_UP,
    PRICE_DOWN_VOLUME_DOWN,

    CONFIRMED_BREAKOUT_VOLUME,
    WEAK_BREAKOUT_VOLUME,

    CONFIRMED_BREAKDOWN_VOLUME,
    WEAK_BREAKDOWN_VOLUME,

    SPRING_VOLUME_CONFIRMATION,
    UTAD_VOLUME_CONFIRMATION,
    NO_VOLUME_CONFIRMATION,

    INSTITUTIONAL_ACCUMULATION,
    INSTITUTIONAL_DISTRIBUTION,

    ABSORPTION_DETECTED,
    SUPPLY_OVERCOMING_DEMAND,
    DEMAND_OVERCOMING_SUPPLY,

    WEAK_VOLUME_SIGNAL,
    MODERATE_VOLUME_SIGNAL,
    STRONG_VOLUME_SIGNAL,
    INSTITUTIONAL_VOLUME_SIGNAL,

    HTF_VOLUME_ALIGNED,
    HTF_VOLUME_CONFLICT,

    MTF_VOLUME_CONFIRMATION,
    MTF_VOLUME_DIVERGENCE
)

# =========================================================
# CONFIG
# =========================================================

DEFAULT_LOOKBACK = 20

CLIMACTIC_RVOL = 3.0
HIGH_RVOL = 1.75
NORMAL_RVOL = 0.80

# =========================================================
# RELATIVE VOLUME
# =========================================================

def classify_rvol(rvol):
    if rvol >= CLIMACTIC_RVOL:
        return RVOL_EXTREME
    if rvol >= HIGH_RVOL:
        return RVOL_HIGH
    if rvol >= NORMAL_RVOL:
        return RVOL_NORMAL
    return RVOL_LOW


# =========================================================
# VOLUME STATE
# =========================================================

def classify_volume_state(rvol):
    if rvol >= CLIMACTIC_RVOL:
        return CLIMACTIC_VOLUME
    if rvol >= HIGH_RVOL:
        return HIGH_VOLUME
    if rvol >= NORMAL_RVOL:
        return NORMAL_VOLUME
    return LOW_VOLUME


# =========================================================
# PARTICIPATION
# =========================================================

def classify_participation(rvol):
    if rvol >= 3.0:
        return INSTITUTIONAL_PARTICIPATION
    if rvol >= 1.75:
        return STRONG_PARTICIPATION
    if rvol >= 1.0:
        return NEUTRAL_PARTICIPATION
    return WEAK_PARTICIPATION


# =========================================================
# VOLUME TREND
# =========================================================

def classify_volume_trend(volumes):
    try:
        if len(volumes) < 10:
            return VOLUME_NEUTRAL

        first = safe_mean(volumes[:5])
        last = safe_mean(volumes[-5:])

        if last > first * 1.10:
            return VOLUME_EXPANDING
        if last < first * 0.90:
            return VOLUME_CONTRACTING

        return VOLUME_NEUTRAL
    except:
        return VOLUME_NEUTRAL


# =========================================================
# PRICE / VOLUME RELATIONSHIP
# =========================================================

def classify_price_volume(price_change, volume_change):
    if price_change >= 0 and volume_change >= 0:
        return PRICE_UP_VOLUME_UP
    if price_change >= 0 and volume_change < 0:
        return PRICE_UP_VOLUME_DOWN
    if price_change < 0 and volume_change >= 0:
        return PRICE_DOWN_VOLUME_UP
    return PRICE_DOWN_VOLUME_DOWN


# =========================================================
# EFFORT VS RESULT
# =========================================================

def classify_effort_result(rvol, price_change_pct):
    expected_move = rvol * 0.01
    if price_change_pct >= expected_move:
        return "EFFORT_RESULT_CONFIRMATION"
    return "EFFORT_RESULT_DIVERGENCE"


# =========================================================
# ABSORPTION ANALYSIS
# =========================================================

def detect_absorption(df, lookback):
    try:
        recent = df.tail(lookback)

        spread = recent["High"] - recent["Low"]
        avg_spread = safe_mean(spread)

        volumes = recent["Volume"].values
        avg_volume = safe_mean(volumes)

        latest_volume = safe_float(volumes[-1])
        latest_spread = safe_float(spread.iloc[-1])

        return (
            latest_volume > avg_volume * 1.75 and
            latest_spread < avg_spread
        )
    except:
        return False


# =========================================================
# COMPOSITE OPERATOR ACTIVITY
# =========================================================

def classify_operator_activity(absorption_detected, price_change, rvol):
    if absorption_detected and price_change > 0:
        return INSTITUTIONAL_ACCUMULATION

    if absorption_detected and price_change < 0:
        return INSTITUTIONAL_DISTRIBUTION

    if price_change > 0 and rvol > 1.25:
        return DEMAND_OVERCOMING_SUPPLY

    if price_change < 0 and rvol > 1.25:
        return SUPPLY_OVERCOMING_DEMAND

    return None


# =========================================================
# CONFIDENCE
# =========================================================

def classify_volume_confidence(rvol):
    if rvol >= 3.0:
        return INSTITUTIONAL_VOLUME_SIGNAL
    if rvol >= 1.75:
        return STRONG_VOLUME_SIGNAL
    if rvol >= 1.0:
        return MODERATE_VOLUME_SIGNAL
    return WEAK_VOLUME_SIGNAL


# =========================================================
# BREAKOUT CONFIRMATION
# =========================================================

def breakout_volume_confirmation(breakout_direction, rvol):
    if breakout_direction == "UP":
        return CONFIRMED_BREAKOUT_VOLUME if rvol >= 1.5 else WEAK_BREAKOUT_VOLUME

    if breakout_direction == "DOWN":
        return CONFIRMED_BREAKDOWN_VOLUME if rvol >= 1.5 else WEAK_BREAKDOWN_VOLUME

    return None


# =========================================================
# SPRING / UTAD CONFIRMATION
# =========================================================

def manipulation_volume_confirmation(event_type, rvol):
    if event_type == "SPRING":
        return SPRING_VOLUME_CONFIRMATION if rvol >= 1.25 else NO_VOLUME_CONFIRMATION

    if event_type == "UTAD":
        return UTAD_VOLUME_CONFIRMATION if rvol >= 1.25 else NO_VOLUME_CONFIRMATION

    return NO_VOLUME_CONFIRMATION


# =========================================================
# MTF ALIGNMENT
# =========================================================

def classify_mtf_alignment(current_rvol, higher_timeframe_rvol=None):
    if higher_timeframe_rvol is None:
        return None

    if current_rvol >= 1.0 and higher_timeframe_rvol >= 1.0:
        return HTF_VOLUME_ALIGNED

    return HTF_VOLUME_CONFLICT


# =========================================================
# MAIN ENGINE
# =========================================================

def confirm_volume_profile(
    df,
    lookback=DEFAULT_LOOKBACK,
    breakout_direction=None,
    event_type=None,
    higher_timeframe_rvol=None
):
    try:
        if len(df) < lookback:
            return {"strength": 0.0, "valid": False}

        recent = df.tail(lookback)

        volumes = recent["Volume"].values
        closes = recent["Close"].values

        if len(closes) < 2:
            return {"strength": 0.0, "valid": False}

        avg_volume = safe_mean(volumes)
        latest_volume = safe_float(volumes[-1])

        rvol = normalize_volume(latest_volume, avg_volume)

        volume_state = classify_volume_state(rvol)
        rvol_state = classify_rvol(rvol)
        participation = classify_participation(rvol)
        volume_trend = classify_volume_trend(volumes)

        latest_price_change = closes[-1] - closes[-2]
        latest_price_change_pct = latest_price_change / max(abs(closes[-2]), 1e-6)

        volume_change = latest_volume - safe_mean(volumes[:-1])

        price_volume_relationship = classify_price_volume(
            latest_price_change,
            volume_change
        )

        effort_result = classify_effort_result(rvol, latest_price_change_pct)

        absorption_detected = detect_absorption(df, lookback)

        operator_activity = classify_operator_activity(
            absorption_detected,
            latest_price_change,
            rvol
        )

        confidence_tier = classify_volume_confidence(rvol)

        breakout_confirmation = breakout_volume_confirmation(
            breakout_direction,
            rvol
        )

        manipulation_confirmation = manipulation_volume_confirmation(
            event_type,
            rvol
        )

        mtf_alignment = classify_mtf_alignment(
            rvol,
            higher_timeframe_rvol
        )

        confidence = clamp_confidence(min(rvol / 3.0, 1.0))

        return {
            "valid": True,
            "strength": confidence,
            "rvol": float(rvol),
            "volume_state": volume_state,
            "rvol_classification": rvol_state,
            "participation": participation,
            "volume_trend": volume_trend,
            "price_volume_relationship": price_volume_relationship,
            "effort_result": effort_result,
            "absorption_detected": absorption_detected,
            "absorption_classification": ABSORPTION_DETECTED if absorption_detected else None,
            "operator_activity": operator_activity,
            "volume_confidence": confidence_tier,
            "breakout_confirmation": breakout_confirmation,
            "manipulation_confirmation": manipulation_confirmation,
            "mtf_alignment": mtf_alignment,
            "mtf_status":
                MTF_VOLUME_CONFIRMATION if mtf_alignment == HTF_VOLUME_ALIGNED
                else MTF_VOLUME_DIVERGENCE if mtf_alignment == HTF_VOLUME_CONFLICT
                else None
        }

    except Exception as e:
        return {
            "valid": False,
            "strength": 0.0,
            "error": str(e)
        }