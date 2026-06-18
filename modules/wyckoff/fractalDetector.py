import numpy as np
import pandas as pd

from modules.wyckoff.common import (
    FractalPoint,
    FRACTAL_HIGH,
    FRACTAL_LOW,

    MINOR_FRACTAL,
    INTERMEDIATE_FRACTAL,
    MAJOR_FRACTAL,
    PRIMARY_FRACTAL,
    SUPER_FRACTAL,

    TREND_FRACTAL,
    REVERSAL_FRACTAL,
    LIQUIDITY_FRACTAL,
    BREAK_FRACTAL
)

# =========================================================
# WINDOWS
# =========================================================

MINOR_WINDOW = 5
MAJOR_WINDOW = 13


# =========================================================
# LOCAL EXTREMA (STABILIZED)
# =========================================================

def is_local_max(arr, i, window):
    left = max(0, i - window)
    right = min(len(arr), i + window + 1)
    segment = arr[left:right]
    return np.isclose(arr[i], np.max(segment))


def is_local_min(arr, i, window):
    left = max(0, i - window)
    right = min(len(arr), i + window + 1)
    segment = arr[left:right]
    return np.isclose(arr[i], np.min(segment))


# =========================================================
# STRENGTH SCORING (HARDENED)
# =========================================================

def score_fractal_strength(df, i, lookahead=10):
    try:
        high = df["High"].values
        low = df["Low"].values
        close = df["Close"].values

        start = max(0, i - 5)

        base_range = np.mean(high[start:i + 1] - low[start:i + 1])
        if base_range == 0:
            base_range = 1e-6

        future_end = min(len(df), i + lookahead)

        future_high = np.max(high[i:future_end]) if future_end > i else high[i]
        future_low = np.min(low[i:future_end]) if future_end > i else low[i]

        forward_move = max(
            abs(future_high - close[i]),
            abs(close[i] - future_low)
        )

        strength = forward_move / base_range

        return float(np.clip(strength / 2.0, 0.0, 1.0))

    except:
        return 0.0


# =========================================================
# DEGREE CLASSIFICATION
# =========================================================

def classify_degree(strength):
    if strength >= 0.85:
        return SUPER_FRACTAL
    if strength >= 0.70:
        return PRIMARY_FRACTAL
    if strength >= 0.55:
        return MAJOR_FRACTAL
    if strength >= 0.40:
        return INTERMEDIATE_FRACTAL
    return MINOR_FRACTAL


# =========================================================
# FRACTAL ROLE CLASSIFICATION (STRUCTURE-BASED ONLY)
# =========================================================

def classify_role(i, df, high, low):
    # volatility context instead of index artifacts
    recent_range = np.mean(high[max(0, i-5):i+1] - low[max(0, i-5):i+1])

    if i < 10:
        return TREND_FRACTAL

    if recent_range > np.mean(high - low) * 1.5:
        return LIQUIDITY_FRACTAL

    if recent_range < np.mean(high - low) * 0.5:
        return BREAK_FRACTAL

    return REVERSAL_FRACTAL


# =========================================================
# BUILD FRACTAL POINT
# =========================================================

def build_point(df, i, ftype, timeframe, high, low):
    strength = score_fractal_strength(df, i)
    degree = classify_degree(strength)
    role = classify_role(i, df, high, low)

    return FractalPoint(
        index=i,
        timestamp=df["timestamp"].iloc[i],
        price=float(df["Close"].iloc[i]),

        fractal_type=ftype,
        degree=degree,
        timeframe=timeframe,
        strength=strength,

        metadata={
            "high": float(high[i]),
            "low": float(low[i]),
            "role": role
        }
    )


# =========================================================
# MAIN DETECTOR (DEDUPED + PRIORITY BASED)
# =========================================================

def detect_fractals(df, timeframe="Daily"):
    df = df.copy().reset_index(drop=True)

    highs = df["High"].values
    lows = df["Low"].values

    fractals = []

    max_window = max(MINOR_WINDOW, MAJOR_WINDOW)

    for i in range(max_window, len(df) - max_window):

        # -----------------------------
        # HIGH FRACTAL (PRIORITY: MAJOR > MINOR)
        # -----------------------------
        high_detected = False

        if is_local_max(highs, i, MAJOR_WINDOW):
            fractals.append(build_point(df, i, FRACTAL_HIGH, timeframe, highs, lows))
            high_detected = True

        elif is_local_max(highs, i, MINOR_WINDOW):
            fractals.append(build_point(df, i, FRACTAL_HIGH, timeframe, highs, lows))
            high_detected = True

        # -----------------------------
        # LOW FRACTAL (PRIORITY: MAJOR > MINOR)
        # -----------------------------
        low_detected = False

        if is_local_min(lows, i, MAJOR_WINDOW):
            fractals.append(build_point(df, i, FRACTAL_LOW, timeframe, highs, lows))
            low_detected = True

        elif is_local_min(lows, i, MINOR_WINDOW):
            fractals.append(build_point(df, i, FRACTAL_LOW, timeframe, highs, lows))
            low_detected = True

    fractals.sort(key=lambda x: x.index)

    return {
        "timeframe": timeframe,
        "fractals": fractals
    }