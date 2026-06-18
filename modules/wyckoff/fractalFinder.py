import numpy as np


# =========================================================
# FRACTAL DETECTION (BILL WILLIAMS CORE)
# =========================================================

def detect_fractals(df, min_strength_filter=False):

    """
    Returns:
    - bullish_fractals (swing highs)
    - bearish_fractals (swing lows)
    - structure points for Elliott/Fib
    """

    try:
        if df is None or len(df) < 5:
            return {
                "bullish_fractals": [],
                "bearish_fractals": []
            }

        high = df["High"].values
        low = df["Low"].values
        close = df["Close"].values

        bullish = []  # swing highs
        bearish = []  # swing lows

        # must start at index 2 and end len-2
        for i in range(2, len(df) - 2):

            # =========================
            # BULLISH FRACTAL (swing high)
            # =========================
            if (
                high[i] > high[i - 1] and
                high[i] > high[i - 2] and
                high[i] > high[i + 1] and
                high[i] > high[i + 2]
            ):

                bullish.append({
                    "index": i,
                    "price": float(high[i]),
                    "type": "BULLISH_FRACTAL",
                    "context": "swing_high"
                })

            # =========================
            # BEARISH FRACTAL (swing low)
            # =========================
            if (
                low[i] < low[i - 1] and
                low[i] < low[i - 2] and
                low[i] < low[i + 1] and
                low[i] < low[i + 2]
            ):

                bearish.append({
                    "index": i,
                    "price": float(low[i]),
                    "type": "BEARISH_FRACTAL",
                    "context": "swing_low"
                })

        return {
            "bullish_fractals": bullish,
            "bearish_fractals": bearish
        }

    except Exception as e:
        return {
            "bullish_fractals": [],
            "bearish_fractals": [],
            "error": str(e)
        }