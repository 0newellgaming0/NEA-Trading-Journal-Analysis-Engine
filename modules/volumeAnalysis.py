# ==========================================================
# Volume Analysis Utilities
# ==========================================================
# Computes:
#   - Relative Volume (RVOL)
#   - Volume spikes
#   - Volume contractions / expansions
# ==========================================================

import pandas as pd
import numpy as np

def rvol(volume: pd.Series, window: int = 20) -> pd.Series:
    """
    Relative Volume: current volume vs rolling average
    """
    return volume / volume.rolling(window, min_periods=1).mean()

def detect_volume_spike(volume: pd.Series, window: int = 20, multiplier: float = 1.5) -> pd.Series:
    """
    Returns boolean Series where volume spikes occur
    """
    rv = rvol(volume, window)
    return rv > multiplier

def detect_volume_contraction(volume: pd.Series, window: int = 20, threshold: float = 0.8) -> pd.Series:
    """
    Returns boolean Series where volume contracts below threshold
    """
    rv = rvol(volume, window)
    return rv < threshold

# ----------------------------------------------------------
# Up Volume %
# ----------------------------------------------------------

def up_volume_percentage(close: pd.Series,
                         volume: pd.Series,
                         window: int = 20) -> pd.Series:

    up_vol = np.where(close.diff() > 0, volume, 0)

    up_vol = pd.Series(
        up_vol,
        index=volume.index
    )

    total_vol = volume.rolling(window, min_periods=1).sum()

    return (
        up_vol.rolling(window, min_periods=1).sum()
        / total_vol.replace(0, np.nan)
    ) * 100


# ----------------------------------------------------------
# Down Volume %
# ----------------------------------------------------------

def down_volume_percentage(close: pd.Series,
                           volume: pd.Series,
                           window: int = 20) -> pd.Series:

    down_vol = np.where(close.diff() < 0, volume, 0)

    down_vol = pd.Series(
        down_vol,
        index=volume.index
    )

    total_vol = volume.rolling(window, min_periods=1).sum()

    return (
        down_vol.rolling(window, min_periods=1).sum()
        / total_vol.replace(0, np.nan)
    ) * 100


# ----------------------------------------------------------
# OBV
# ----------------------------------------------------------

def obv(close: pd.Series,
        volume: pd.Series) -> pd.Series:

    direction = np.sign(close.diff()).fillna(0)

    return (direction * volume).cumsum()


# ----------------------------------------------------------
# OBV Slope
# ----------------------------------------------------------

def obv_slope(close: pd.Series,
              volume: pd.Series,
              window: int = 20) -> pd.Series:

    obv_line = obv(close, volume)

    return (
        obv_line
        .diff(window)
        .divide(window)
    )


# ----------------------------------------------------------
# Accumulation / Distribution Line
# ----------------------------------------------------------

def accumulation_distribution(high: pd.Series,
                              low: pd.Series,
                              close: pd.Series,
                              volume: pd.Series) -> pd.Series:

    denominator = (high - low).replace(0, np.nan)

    mfm = (
        ((close - low) - (high - close))
        / denominator
    )

    mfv = mfm.fillna(0) * volume

    return mfv.cumsum()


# ----------------------------------------------------------
# A/D Slope
# ----------------------------------------------------------

def ad_slope(high: pd.Series,
             low: pd.Series,
             close: pd.Series,
             volume: pd.Series,
             window: int = 20) -> pd.Series:

    ad_line = accumulation_distribution(
        high,
        low,
        close,
        volume
    )

    return (
        ad_line
        .diff(window)
        .divide(window)
    )


# ----------------------------------------------------------
# Large Volume Up Days
# ----------------------------------------------------------

def large_volume_up_days(close: pd.Series,
                         volume: pd.Series,
                         volume_window: int = 20,
                         multiplier: float = 1.5) -> pd.Series:

    avg_vol = volume.rolling(
        volume_window,
        min_periods=1
    ).mean()

    return (
        (close.diff() > 0)
        &
        (volume > avg_vol * multiplier)
    )


# ----------------------------------------------------------
# Large Volume Down Days
# ----------------------------------------------------------

def large_volume_down_days(close: pd.Series,
                           volume: pd.Series,
                           volume_window: int = 20,
                           multiplier: float = 1.5) -> pd.Series:

    avg_vol = volume.rolling(
        volume_window,
        min_periods=1
    ).mean()

    return (
        (close.diff() < 0)
        &
        (volume > avg_vol * multiplier)
    )


# ----------------------------------------------------------
# Institutional Classification
# ----------------------------------------------------------

def institutional_accumulation_state(
    close: pd.Series,
    high: pd.Series,
    low: pd.Series,
    volume: pd.Series,
    window: int = 20
) -> pd.Series:

    up_pct = up_volume_percentage(
        close,
        volume,
        window
    )

    obv_trend = obv_slope(
        close,
        volume,
        window
    )

    ad_trend = ad_slope(
        high,
        low,
        close,
        volume,
        window
    )

    lv_up = (
        large_volume_up_days(
            close,
            volume
        )
        .rolling(window, min_periods=1)
        .sum()
    )

    lv_down = (
        large_volume_down_days(
            close,
            volume
        )
        .rolling(window, min_periods=1)
        .sum()
    )

    conditions_accumulation = (
        (up_pct > 55)
        &
        (obv_trend > 0)
        &
        (ad_trend > 0)
        &
        (lv_up > lv_down)
    )

    conditions_distribution = (
        (up_pct < 45)
        &
        (obv_trend < 0)
        &
        (ad_trend < 0)
        &
        (lv_down > lv_up)
    )

    result = pd.Series(
        "Neutral",
        index=close.index
    )

    result.loc[
        conditions_accumulation
    ] = "Active Accumulation"

    result.loc[
        conditions_distribution
    ] = "Active Distribution"

    return result
