# =========================================================
# secondaryTest.py
# Wyckoff Secondary Test Detector (Phase-agnostic)
# =========================================================

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from modules.wyckoff.schemas import (
    TimeframeContext,
    FractalPoint,
    BreakoutEvent,
    ManipulationEvent,
    MarketEvent
)

# Optional volume confirmation (graceful fallback)
try:
    from modules.wyckoff.volume_profile import confirm_volume_profile
except:
    confirm_volume_profile = None


# =========================================================
# CONSTANTS
# =========================================================

SECONDARY_TEST = "SECONDARY_TEST"

TEST_AFTER_BREAKOUT = "TEST_AFTER_BREAKOUT"
TEST_AFTER_SPRING = "TEST_AFTER_SPRING"
TEST_AFTER_UTAD = "TEST_AFTER_UTAD"

TOUCH_TOLERANCE_DEFAULT = 0.0025   # 0.25%
EXTENDED_TOLERANCE = 0.005         # 0.5%


# =========================================================
# SAFE UTILITIES
# =========================================================

def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


def price_within_tolerance(price, level, tolerance):
    if level == 0:
        return False
    return abs(price - level) / level <= tolerance


def compute_atr_like(df, window=14):
    """
    Lightweight ATR proxy using high-low range.
    """
    try:
        if len(df) < 2:
            return 0.0

        recent = df.tail(window)
        tr = recent["High"] - recent["Low"]
        return float(np.mean(tr)) if len(tr) else 0.0
    except:
        return 0.0


# =========================================================
# SECONDARY TEST STRUCTURE
# =========================================================

class SecondaryTestEvent:
    def __init__(
        self,
        index: int,
        timestamp: Any,
        price: float,
        test_type: str,
        source_event_type: str,
        reference_level: float,
        timeframe: str,
        confidence: float,
        metadata: Dict[str, Any]
    ):
        self.index = index
        self.timestamp = timestamp
        self.price = price
        self.test_type = test_type
        self.source_event_type = source_event_type
        self.reference_level = reference_level
        self.timeframe = timeframe
        self.confidence = confidence
        self.metadata = metadata or {}


# =========================================================
# LEVEL EXTRACTION
# =========================================================

def extract_levels(context: TimeframeContext):
    """
    Extract key structural levels from prior events.
    """
    levels = []

    # Breakout levels
    for b in context.breakouts:
        if hasattr(b, "breakout_level"):
            levels.append(("BREAKOUT", b.index, b.breakout_level, b.timestamp))

    # Spring / UTAD reference levels
    for s in context.springs:
        levels.append(("SPRING", s.index, s.price, s.timestamp))

    for u in context.utads:
        levels.append(("UTAD", u.index, u.price, u.timestamp))

    return sorted(levels, key=lambda x: x[1])


# =========================================================
# SECONDARY TEST DETECTION CORE
# =========================================================

def detect_secondary_tests(
    context: TimeframeContext,
    df: pd.DataFrame,
    tolerance: float = TOUCH_TOLERANCE_DEFAULT,
    use_volume_confirmation: bool = True
) -> Dict[str, Any]:

    df = df.copy().reset_index(drop=True)

    levels = extract_levels(context)
    if not levels:
        return {
            "valid": False,
            "secondary_tests": [],
            "reason": "NO_REFERENCE_LEVELS"
        }

    atr_like = compute_atr_like(df)

    tests: List[SecondaryTestEvent] = []

    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values

    for level_type, level_index, level_price, level_ts in levels:

        # Secondary tests must occur AFTER the reference event
        for i in range(level_index + 1, len(df)):

            price = closes[i]

            # dynamic tolerance adjustment using ATR proxy
            dynamic_tol = tolerance
            if atr_like > 0:
                dynamic_tol = max(tolerance, atr_like / max(level_price, 1e-6))

            touched = price_within_tolerance(price, level_price, dynamic_tol)

            if not touched:
                continue

            # Volume confirmation (optional)
            volume_ok = False
            volume_data = None

            if use_volume_confirmation and confirm_volume_profile:
                try:
                    volume_data = confirm_volume_profile(df.iloc[:i+1])
                    volume_ok = volume_data.get("strength", 0.0) >= 0.5
                except:
                    volume_ok = False

            # Confidence model (structure-first)
            confidence = 0.5

            if volume_ok:
                confidence += 0.2

            # stronger confidence if clean retest (low deviation)
            deviation = abs(price - level_price) / max(level_price, 1e-6)
            if deviation < tolerance / 2:
                confidence += 0.2

            # classify test type
            if level_type == "BREAKOUT":
                test_type = TEST_AFTER_BREAKOUT
            elif level_type == "SPRING":
                test_type = TEST_AFTER_SPRING
            elif level_type == "UTAD":
                test_type = TEST_AFTER_UTAD
            else:
                test_type = SECONDARY_TEST

            tests.append(
                SecondaryTestEvent(
                    index=i,
                    timestamp=df["timestamp"].iloc[i],
                    price=price,
                    test_type=test_type,
                    source_event_type=level_type,
                    reference_level=level_price,
                    timeframe=context.timeframe,
                    confidence=confidence,
                    metadata={
                        "level_index": level_index,
                        "deviation": deviation,
                        "volume_confirmed": volume_ok,
                        "atr_like": atr_like,
                        "dynamic_tolerance": dynamic_tol
                    }
                )
            )

            # Only first valid test per level (prevents noise explosion)
            break

    return {
        "valid": len(tests) > 0,
        "secondary_tests": tests,
        "count": len(tests),
        "timeframe": context.timeframe
    }


# =========================================================
# CONTEXT INTEGRATION WRAPPER
# =========================================================

def run_secondary_test_scan(
    context: TimeframeContext,
    df: pd.DataFrame
) -> Dict[str, Any]:

    result = detect_secondary_tests(context, df)

    # attach to context if valid
    if result["valid"]:
        if not hasattr(context, "metadata"):
            context.metadata = {}

        context.metadata["secondary_tests"] = result["secondary_tests"]

    return result