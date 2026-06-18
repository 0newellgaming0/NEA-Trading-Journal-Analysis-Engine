from typing import List, Dict, Any
import numpy as np
import pandas as pd

from modules.wyckoff.common import (
    BC,
    CLIMACTIC_VOLUME,
    HIGH_VOLUME,
    CLIMACTIC_VOLUME,
    PRICE_UP_VOLUME_UP,
    PRICE_UP_VOLUME_DOWN,
    ABSORPTION_VOLUME,
    DISTRIBUTION_VOLUME,
    INSTITUTIONAL_DISTRIBUTION,
    SUPPLY_OVERCOMING_DEMAND
)

from modules.wyckoff.schemas import (
    BreakoutEvent,
    TimeframeContext
)

# =========================================================
# BUYING CLIMAX DETECTOR (BC)
# =========================================================

def safe_mean(x):
    try:
        return float(np.nanmean(x))
    except:
        return 0.0


def safe_std(x):
    try:
        return float(np.nanstd(x))
    except:
        return 0.0


def detect_buying_climax(context: TimeframeContext) -> Dict[str, Any]:
    """
    Detect BUYING CLIMAX (BC) conditions:
    - Parabolic price expansion
    - Climax volume spike
    - Effort vs result divergence
    - Exhaustion at highs
    """

    df = context.data.copy().reset_index(drop=True)

    highs = df["High"].values
    lows = df["Low"].values
    closes = df["Close"].values

    volume = df["Volume"].values if "Volume" in df.columns else np.zeros(len(df))

    events: List[BreakoutEvent] = []

    vol_mean = safe_mean(volume)
    vol_std = safe_std(volume)

    price_range = highs - lows

    for i in range(10, len(df) - 2):

        # ----------------------------
        # CLIMACTIC CONDITIONS
        # ----------------------------
        is_climax_vol = volume[i] > vol_mean + (2.5 * vol_std)

        is_expansion = price_range[i] > np.mean(price_range[max(0, i-10):i]) * 1.8

        upper_wick = highs[i] - max(closes[i], opens[i]) if "Open" in df else highs[i] - closes[i]

        wick_expansion = upper_wick > (price_range[i] * 0.5)

        # ----------------------------
        # EFFORT VS RESULT FAILURE
        # ----------------------------
        next_move = closes[i+1] - closes[i]

        distribution_signal = (
            is_climax_vol and
            is_expansion and
            next_move < 0  # rejection after buying pressure
        )

        if distribution_signal:

            events.append(
                BreakoutEvent(
                    event_type=BC,
                    index=i,
                    timestamp=df["timestamp"].iloc[i] if "timestamp" in df else None,
                    price=float(closes[i]),
                    breakout_level=float(highs[i]),
                    timeframe=context.timeframe,
                    confidence=float(np.clip(
                        0.6 +
                        (0.2 if is_climax_vol else 0) +
                        (0.1 if wick_expansion else 0),
                        0.0,
                        1.0
                    )),
                    volume_confirmed=is_climax_vol,
                    institutional_confirmed=volume[i] > vol_mean * 3,
                    metadata={
                        "price_range": float(price_range[i]),
                        "volume": float(volume[i]),
                        "vol_mean": float(vol_mean),
                        "vol_std": float(vol_std),
                        "type": "BUYING_CLIMAX"
                    }
                )
            )

    context.breakouts.extend(events)

    return {
        "timeframe": context.timeframe,
        "buying_climax_count": len(events),
        "events": events
    }