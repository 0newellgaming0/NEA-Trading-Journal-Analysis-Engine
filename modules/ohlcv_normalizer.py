import pandas as pd
import numpy as np

# =========================================================
# UNIFIED TIMESTAMP + DYNAMIC OHLCV NORMALIZER
# =========================================================

def normalize_timestamp(df):

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("OHLCV input is invalid")

    df = df.copy()

    # =====================================================
    # TIMESTAMP HANDLING (UNCHANGED LOGIC)
    # =====================================================

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    elif "datetime" in df.columns:
        df["timestamp"] = pd.to_datetime(df["datetime"], errors="coerce", utc=True)

    elif "date" in df.columns:
        df["timestamp"] = pd.to_datetime(df["date"], errors="coerce", utc=True)

    else:
        raise ValueError(f"Missing time column. Got: {list(df.columns)}")

    df = (
        df.dropna(subset=["timestamp"])
          .sort_values("timestamp")
          .reset_index(drop=True)
    )

    # =====================================================
    # DYNAMIC OHLCV DETECTION (NO SUFFIX ASSUMPTIONS)
    # =====================================================

    def find_col(prefix):
        """
        Finds column that ends with or starts with prefix pattern.
        Example matches:
        open_rbbn, high_TSLA, close123, volume_x
        """
        prefix = prefix.lower()

        for c in df.columns:
            cl = c.lower()

            # match patterns like:
            # high_rbbn, rbbn_high, high123, etc.
            if cl == prefix or cl.startswith(prefix) or cl.endswith(prefix):
                return c

        return None
        
    open_col = find_col("open")
    high_col = find_col("high")
    low_col = find_col("low")
    close_col = find_col("close")
    volume_col = find_col("volume")

    if open_col is None:
        raise ValueError(f"Missing Open column. Available: {list(df.columns)}")
        
    if high_col is None:
        raise ValueError(f"Missing High column. Available: {list(df.columns)}")

    if low_col is None:
        raise ValueError(f"Missing Low column. Available: {list(df.columns)}")

    if close_col is None:
        raise ValueError(f"Missing Close column. Available: {list(df.columns)}")

    if volume_col is None:
        raise ValueError(f"Missing Volume column. Available: {list(df.columns)}")

    # =====================================================
    # STANDARDIZED OUTPUT COLUMNS
    # =====================================================

    df["Open"] = pd.to_numeric(df[open_col], errors="coerce")
    df["High"] = pd.to_numeric(df[high_col], errors="coerce")
    df["Low"] = pd.to_numeric(df[low_col], errors="coerce")
    df["Close"] = pd.to_numeric(df[close_col], errors="coerce")
    df["Volume"] = pd.to_numeric(df[volume_col], errors="coerce")

    # =====================================================
    # VALIDATION (NO SILENT FAILS)
    # =====================================================

    required = ["High", "Low", "Close", "Volume"]

    if df[required].isna().any().any():
        raise ValueError("NaN detected after OHLCV normalization")

    if len(df) < 30:
        raise ValueError(f"Insufficient history ({len(df)} bars)")

    return df