from typing import List, Dict, Any

import numpy as np
import pandas as pd

from modules.wyckoff.common import (
    AR,
    SC,
    FRACTAL_LOW,
    FRACTAL_HIGH,
)

from modules.wyckoff.schemas import (
    ManipulationEvent,
    TimeframeContext
)

from modules.wyckoff.fractalDetector import detect_fractals
from modules.wyckoff.volume import confirm_volume_profile


# =========================================================
# CONFIGURATION
# =========================================================

SC_LOOKBACK_WINDOW = 10
AR_LOOKFORWARD_WINDOW = 30

MIN_AR_MOVE = 0.03  # 3% minimum rally displacement


# =========================================================
# SAFE UTILITIES
# =========================================================

def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


# =========================================================
# SELLING CLIMAX DETECTION
# =========================================================

def detect_selling_climax(fractals, df):
    """
    Identify SC points using:
    - FRACTAL_LOW
    - localized extreme low
    - high volume confirmation
    """

    sc_points = []

    for f in fractals:
        if f.fractal_type != FRACTAL_LOW:
            continue

        idx = f.index

        if idx < SC_LOOKBACK_WINDOW:
            continue

        window = df.iloc[max(0, idx - SC_LOOKBACK_WINDOW): idx + 1]

        low = window["Low"].values
        volume = window["Volume"].values

        if len(low) < 5:
            continue

        # SC condition: extreme low in local window
        if f.price <= np.min(low):

            vol_profile = confirm_volume_profile(window)

            if vol_profile.get("rvol", 0) >= 1.75:
                sc_points.append({
                    "index": idx,
                    "price": f.price,
                    "timestamp": f.timestamp,
                    "confidence": vol_profile.get("strength", 0.0)
                })

    return sc_points


# =========================================================
# AUTOMATIC RALLY DETECTION
# =========================================================

def detect_automatic_rallies(context: TimeframeContext) -> List[ManipulationEvent]:
    """
    Detect Wyckoff Automatic Rally (AR):
    Occurs AFTER Selling Climax (SC)
    """

    df = context.data.copy().reset_index(drop=True)

    fractals_result = detect_fractals(df, timeframe=context.timeframe)
    fractals = fractals_result["fractals"]

    sc_points = detect_selling_climax(fractals, df)

    ar_events: List[ManipulationEvent] = []

    closes = df["Close"].values
    highs = df["High"].values

    for sc in sc_points:

        sc_idx = sc["index"]

        # search forward for AR
        end_idx = min(len(df), sc_idx + AR_LOOKFORWARD_WINDOW)

        sc_price = sc["price"]
        local_high = sc_price

        for i in range(sc_idx + 1, end_idx):

            local_high = max(local_high, highs[i])

            price_move = (closes[i] - sc_price) / max(sc_price, 1e-6)

            if price_move < MIN_AR_MOVE:
                continue

            # volume confirmation
            window = df.iloc[max(0, i - 5): i + 1]
            vol_profile = confirm_volume_profile(window)

            rvol = vol_profile.get("rvol", 0)
            valid_volume = vol_profile.get("valid", False)

            # AR condition:
            # - meaningful rally from SC low
            # - volume expansion or confirmation
            # - structural lift from selling pressure
            if valid_volume and rvol >= 1.2:

                ar_event = ManipulationEvent(
                    event_type=AR,
                    index=i,
                    timestamp=df["timestamp"].iloc[i],
                    price=safe_float(closes[i]),
                    timeframe=context.timeframe,
                    confidence=min(1.0, vol_profile.get("strength", 0.5)),
                    volume_confirmed=True,
                    metadata={
                        "sc_index": sc_idx,
                        "sc_price": sc_price,
                        "rally_from_sc_pct": price_move,
                        "local_range_high": float(local_high),
                        "rvol": rvol
                    }
                )

                ar_events.append(ar_event)

                # stop after first valid AR per SC
                break

    return ar_events