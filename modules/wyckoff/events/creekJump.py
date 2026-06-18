import numpy as np
import pandas as pd
from typing import List, Dict, Any

from modules.wyckoff.common import (
    CREEK_JUMP,
    ICE_BREAK,
    BREAKOUT,
    BREAKDOWN,
    FALSE_BREAKOUT,
    FALSE_BREAKDOWN,
    SOS,
    SOW
)

from modules.wyckoff.schemas import (
    MarketEvent,
    TimeframeContext
)

# =========================================================
# CONFIG
# =========================================================

LOOKAHEAD_BARS = 3
BREAK_BUFFER_PCT = 0.0015  # small buffer to avoid wick noise


# =========================================================
# SAFE UTIL
# =========================================================

def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


def safe_mean(arr):
    try:
        if arr is None or len(arr) == 0:
            return 0.0
        return float(np.nanmean(arr))
    except:
        return 0.0


# =========================================================
# RANGE EXTRACTION
# =========================================================

def get_last_range(context: TimeframeContext):
    """
    Uses the most recent validated trading range if available.
    Falls back to recent swing-based approximation if missing.
    """
    if context.ranges:
        r = context.ranges[-1]
        return r.range_high, r.range_low

    # fallback: derive from recent price action
    df = context.data
    lookback = min(20, len(df))

    recent = df.tail(lookback)
    return float(recent["High"].max()), float(recent["Low"].min())


# =========================================================
# BREAK DETECTION
# =========================================================

def detect_breakout(df, i, range_high, range_low):
    close = df["Close"].values[i]
    high = df["High"].values[i]
    low = df["Low"].values[i]

    buffer_high = range_high * (1 + BREAK_BUFFER_PCT)
    buffer_low = range_low * (1 - BREAK_BUFFER_PCT)

    if high > buffer_high and close > range_high:
        return "UP_BREAK"

    if low < buffer_low and close < range_low:
        return "DOWN_BREAK"

    return None


# =========================================================
# CONFIRMATION (FAIL vs VALID CREEK JUMP)
# =========================================================

def confirm_follow_through(df, i, direction):
    """
    Checks whether breakout sustains or fails within next bars.
    """
    future_end = min(len(df), i + LOOKAHEAD_BARS)
    future = df.iloc[i:future_end]

    if len(future) < 2:
        return False

    if direction == "UP":
        return future["Close"].min() > df["Close"].iloc[i]

    if direction == "DOWN":
        return future["Close"].max() < df["Close"].iloc[i]

    return False


# =========================================================
# EVENT BUILDER
# =========================================================

def build_event(event_type, i, df, confidence=0.5):
    return MarketEvent(
        event_type=event_type,
        index=i,
        timestamp=df["timestamp"].iloc[i] if "timestamp" in df.columns else None,
        price=safe_float(df["Close"].iloc[i]),
        timeframe="",
        confidence=confidence,
        volume_confirmed=False,
        metadata={}
    )


# =========================================================
# MAIN DETECTOR
# =========================================================

def detect_creek_jumps(context: TimeframeContext) -> Dict[str, Any]:
    """
    Detects only:
    - CREEK_JUMP (valid breakout continuation)
    - ICE_BREAK (failed breakout / rejection)
    """

    df = context.data.copy().reset_index(drop=True)

    range_high, range_low = get_last_range(context)

    events: List[MarketEvent] = []

    if len(df) < 5:
        return {
            "valid": False,
            "events": [],
            "message": "Insufficient data"
        }

    for i in range(1, len(df) - LOOKAHEAD_BARS):

        breakout = detect_breakout(df, i, range_high, range_low)

        if not breakout:
            continue

        # -----------------------------
        # UPWARD BREAK (CREek JUMP or FAIL)
        # -----------------------------
        if breakout == "UP_BREAK":

            sustained = confirm_follow_through(df, i, "UP")

            if sustained:
                events.append(
                    build_event(
                        CREEK_JUMP,
                        i,
                        df,
                        confidence=0.75
                    )
                )
            else:
                events.append(
                    build_event(
                        ICE_BREAK,
                        i,
                        df,
                        confidence=0.65
                    )
                )

        # -----------------------------
        # DOWNWARD BREAK (CREek FAIL / SOW type)
        # -----------------------------
        elif breakout == "DOWN_BREAK":

            sustained = confirm_follow_through(df, i, "DOWN")

            if sustained:
                events.append(
                    build_event(
                        BREAKDOWN,
                        i,
                        df,
                        confidence=0.70
                    )
                )
            else:
                events.append(
                    build_event(
                        FALSE_BREAKDOWN,
                        i,
                        df,
                        confidence=0.60
                    )
                )

    return {
        "valid": len(events) > 0,
        "events": events,
        "range_high": range_high,
        "range_low": range_low,
        "count": len(events)
    }