from typing import List, Dict, Any
import numpy as np
import pandas as pd

from modules.wyckoff.common import (
    BACKUP,
    FRACTAL_HIGH,
    FRACTAL_LOW,
    MarketEvent
)

# =========================================================
# BACKING UP ACTION DETECTOR (WYCKOFF ONLY)
# =========================================================

LOOKBACK_RANGE = 20
BREAKOUT_BUFFER = 0.0015   # 0.15% tolerance above level
PULLBACK_TOLERANCE = 0.01  # 1% pullback window
VOLUME_CONTRACTION_RATIO = 0.8


# =========================================================
# SAFE UTILITIES
# =========================================================

def safe_mean(arr):
    try:
        arr = np.asarray(arr, dtype=float)
        return float(np.nanmean(arr)) if len(arr) else 0.0
    except:
        return 0.0


def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0


# =========================================================
# CORE STRUCTURE: DETECT PRIOR BREAKOUT LEVEL
# =========================================================

def detect_breakout(df: pd.DataFrame, lookback: int):
    """
    Detect most recent valid breakout above rolling resistance.
    """
    highs = df["High"].values
    closes = df["Close"].values

    for i in range(lookback, len(df)):
        resistance = np.max(highs[i - lookback:i])

        # breakout condition (close above structure)
        if closes[i] > resistance * (1 + BREAKOUT_BUFFER):
            return {
                "index": i,
                "level": resistance,
                "price": closes[i],
                "volume": safe_float(df["Volume"].iloc[i]) if "Volume" in df.columns else 0.0
            }

    return None


# =========================================================
# BACKUP ACTION VALIDATION
# =========================================================

def detect_backup_action(df: pd.DataFrame, timeframe: str = "Daily") -> List[MarketEvent]:

    if len(df) < LOOKBACK_RANGE * 2:
        return []

    events = []

    breakout = detect_breakout(df, LOOKBACK_RANGE)

    if not breakout:
        return events

    b_idx = breakout["index"]
    level = breakout["level"]
    breakout_volume = breakout["volume"]

    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values

    # =====================================================
    # SEARCH FOR BACKING UP ACTION AFTER BREAKOUT
    # =====================================================
    for i in range(b_idx + 1, len(df)):

        price = closes[i]
        low = lows[i]
        vol = safe_float(df["Volume"].iloc[i]) if "Volume" in df.columns else 0.0

        # -----------------------------
        # CONDITION 1: Pullback toward breakout level
        # -----------------------------
        pullback_into_zone = (
            low <= level * (1 + PULLBACK_TOLERANCE) and
            price >= level * (1 - PULLBACK_TOLERANCE)
        )

        # -----------------------------
        # CONDITION 2: Hold above breakout (no failure)
        # -----------------------------
        holds_structure = price >= level * (1 - BREAKOUT_BUFFER)

        # -----------------------------
        # CONDITION 3: Volume contraction (key Wyckoff signature)
        # -----------------------------
        volume_contracts = vol < breakout_volume * VOLUME_CONTRACTION_RATIO

        # -----------------------------
        # VALID BACKUP ACTION
        # -----------------------------
        if pullback_into_zone and holds_structure and volume_contracts:

            events.append(
                MarketEvent(
                    event_type=BACKUP,
                    index=i,
                    timestamp=df["timestamp"].iloc[i] if "timestamp" in df.columns else None,
                    price=price,
                    timeframe=timeframe,
                    confidence=0.75,
                    volume_confirmed=True,
                    metadata={
                        "breakout_index": b_idx,
                        "breakout_level": level,
                        "breakout_price": breakout["price"],
                        "pullback_low": low,
                        "volume_ratio": safe_float(vol / max(breakout_volume, 1e-6)),
                        "structure": "BACKING_UP_ACTION"
                    }
                )
            )

            # Only first valid backup is needed (Wyckoff singular event)
            break

    return events