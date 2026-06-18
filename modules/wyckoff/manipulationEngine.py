import numpy as np


def detect_manipulation(df, range_signal, volume_signal=None):
    """
    Detects:
    - Failed springs
    - Failed UTADs
    - Weak continuation sweeps
    """

    try:
        if df is None or len(df) < 2:
            return []

        high = df["High"].values
        low = df["Low"].values
        close = df["Close"].values

        range_high = range_signal.get("high")
        range_low = range_signal.get("low")

        if range_high is None or range_low is None:
            return []

        manipulations = []

        vol_factor = volume_signal.get("strength", 1.0) if volume_signal else 1.0

        range_size = max(range_high - range_low, 1e-6)

        for i in range(1, len(df)):

            # -----------------------------
            # Failed breakdown (no reclaim)
            # -----------------------------
            if low[i] < range_low and close[i] < range_low:
                strength = min(1.0, (range_low - low[i]) / range_size) * vol_factor

                manipulations.append({
                    "index": i,
                    "type": "FAILED_SPRING",
                    "price": float(close[i]),
                    "strength": float(strength),
                    "context": "bearish_continuation_after_sweep"
                })

            # -----------------------------
            # Failed breakout (no rejection)
            # -----------------------------
            if high[i] > range_high and close[i] > range_high:
                strength = min(1.0, (high[i] - range_high) / range_size) * vol_factor

                manipulations.append({
                    "index": i,
                    "type": "FAILED_UTAD",
                    "price": float(close[i]),
                    "strength": float(strength),
                    "context": "bullish_continuation_after_sweep"
                })

        return manipulations

    except Exception as e:
        return {"error": str(e), "manipulations": []}