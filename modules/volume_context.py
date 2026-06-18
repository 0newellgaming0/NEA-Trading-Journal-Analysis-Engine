import os
import pandas as pd
import numpy as np
from modules.path_resolver import get_stock_data_path
from modules.volumeAnalysis import (
    up_volume_percentage,
    down_volume_percentage,
    obv_slope,
    ad_slope,
    institutional_accumulation_state
)

# =========================================================
# LOAD VOLUME ANALYSIS CONTEXT (RESTORED + FIXED)
# =========================================================
def load_volume_analysis(ticker, timeframe="intraday_60m", limit=40):

    try:
        file_path = get_stock_data_path(
            ticker,
            timeframe=timeframe
        )

        if not os.path.exists(file_path):
            return f"No volume data file found at:\n{file_path}"

        df = pd.read_csv(file_path)

        if df.empty:
            return "Volume file exists but is empty."

        df = df.tail(limit).copy()
        ticker_lower = ticker.lower()

        # =====================================================
        # TIMEFRAME-AWARE WINDOWS (FIXED, PRESERVING ORIGINAL LOGIC)
        # =====================================================
        if "intraday" in timeframe:
            rvol_window = 10
            vol_window = 10
        else:
            rvol_window = 20
            vol_window = 20

        # =====================================================
        # COLUMN RESOLUTION
        # =====================================================
        volume_col = f"volume_{ticker_lower}"
        close_col = f"close_{ticker_lower}"
        high_col = f"high_{ticker_lower}"
        low_col = f"low_{ticker_lower}"
        open_col = f"open_{ticker_lower}"

        if volume_col not in df.columns:
            volume_col = "volume"
        if close_col not in df.columns:
            close_col = "close"
        if high_col not in df.columns:
            high_col = "high"
        if low_col not in df.columns:
            low_col = "low"
        if open_col not in df.columns:
            open_col = "open"

        if volume_col not in df.columns:
            return "No volume column found."

        # =====================================================
        # NUMERIC CLEANUP
        # =====================================================
        numeric_cols = [volume_col, close_col, high_col, low_col, open_col]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.fillna(0)

        volume_series = df[volume_col]

        # =====================================================
        # CORE ANALYTICS
        # =====================================================
        df["rvol_5"] = volume_series / volume_series.rolling(5, min_periods=1).mean()

        df["rvol_20"] = volume_series / volume_series.rolling(rvol_window, min_periods=1).mean()

        df["vol_ma_5"] = volume_series.rolling(5, min_periods=1).mean()
        df["vol_ma_20"] = volume_series.rolling(vol_window, min_periods=1).mean()

        df["vol_std_20"] = volume_series.rolling(vol_window, min_periods=1).std()

        df["vol_zscore"] = (
            (volume_series - df["vol_ma_20"]) /
            df["vol_std_20"].replace(0, np.nan)
        ).fillna(0)

        # =====================================================
        # VOLUME FLOW ANALYTICS (RESTORED)
        # =====================================================
        df["up_volume_pct"] = up_volume_percentage(df[close_col], volume_series)
        df["down_volume_pct"] = down_volume_percentage(df[close_col], volume_series)

        df["obv_slope"] = obv_slope(df[close_col], volume_series)

        df["ad_slope"] = ad_slope(
            df[high_col],
            df[low_col],
            df[close_col],
            volume_series
        )

        # =====================================================
        # INSTITUTIONAL STATE (RESTORED BEHAVIOR)
        # =====================================================
        df["institutional_state"] = institutional_accumulation_state(
            df[close_col].tail(limit),
            df[high_col].tail(limit),
            df[low_col].tail(limit),
            volume_series.tail(limit)
        )

        latest = df.iloc[-1]

        inst_state = latest["institutional_state"]
        up_vol_pct = latest["up_volume_pct"]
        down_vol_pct = latest["down_volume_pct"]
        obv_trend = latest["obv_slope"]
        ad_trend = latest["ad_slope"]

        # =====================================================
        # SPIKE / CONTRACTION DETECTION (RESTORED FULL SET)
        # =====================================================
        df["spike"] = df["rvol_20"] >= 1.5
        df["major_spike"] = df["rvol_20"] >= 2.5
        df["extreme_spike"] = df["rvol_20"] >= 4.0
        df["contraction"] = df["rvol_20"] <= 0.8

        # =====================================================
        # PRICE ACTION CONTEXT
        # =====================================================
        if close_col in df.columns:
            df["price_change_pct"] = df[close_col].pct_change() * 100

            latest_close = round(float(df[close_col].iloc[-1]), 4)
            latest_price_change = round(float(df["price_change_pct"].iloc[-1]), 2)
        else:
            latest_close = "N/A"
            latest_price_change = "N/A"

        # =====================================================
        # DIRECTIONAL VOLUME
        # =====================================================
        if open_col in df.columns and close_col in df.columns:
            green_volume = df.loc[df[close_col] >= df[open_col], volume_col].sum()
            red_volume = df.loc[df[close_col] < df[open_col], volume_col].sum()
        else:
            green_volume = 0
            red_volume = 0

        # =====================================================
        # ACCUMULATION / DISTRIBUTION MODEL (RESTORED)
        # =====================================================
        if all(c in df.columns for c in [high_col, low_col, close_col]):

            hl_range = (df[high_col] - df[low_col]).replace(0, np.nan)

            money_flow_multiplier = (
                ((df[close_col] - df[low_col]) -
                 (df[high_col] - df[close_col])) / hl_range
            ).fillna(0)

            df["money_flow_volume"] = money_flow_multiplier * volume_series

            ad_value = int(df["money_flow_volume"].sum())

        else:
            ad_value = 0

        # =====================================================
        # RECENT METRICS (RESTORED FULL)
        # =====================================================
        latest_volume = int(volume_series.iloc[-1])

        avg_volume_5 = int(df["vol_ma_5"].iloc[-1])
        avg_volume_20 = int(df["vol_ma_20"].iloc[-1])

        latest_rvol_5 = round(float(df["rvol_5"].iloc[-1]), 2)
        latest_rvol_20 = round(float(df["rvol_20"].iloc[-1]), 2)

        latest_zscore = round(float(df["vol_zscore"].iloc[-1]), 2)

        spike_count = int(df["spike"].sum())
        major_spike_count = int(df["major_spike"].sum())
        extreme_spike_count = int(df["extreme_spike"].sum())
        contraction_count = int(df["contraction"].sum())

        latest_spike = bool(df["spike"].iloc[-1])
        latest_major_spike = bool(df["major_spike"].iloc[-1])
        latest_extreme_spike = bool(df["extreme_spike"].iloc[-1])
        latest_contraction = bool(df["contraction"].iloc[-1])

        # =====================================================
        # VOLUME TREND
        # =====================================================
        volume_trend = (
            "EXPANDING" if avg_volume_5 > avg_volume_20 else
            "CONTRACTING" if avg_volume_5 < avg_volume_20 else
            "NEUTRAL"
        )

        # =====================================================
        # PARTICIPATION CLASSIFICATION
        # =====================================================
        if latest_rvol_20 >= 4:
            participation = "EXTREME INSTITUTIONAL PARTICIPATION"
        elif latest_rvol_20 >= 2:
            participation = "HEAVY INSTITUTIONAL PARTICIPATION"
        elif latest_rvol_20 >= 1.3:
            participation = "MODERATE PARTICIPATION EXPANSION"
        elif latest_rvol_20 <= 0.7:
            participation = "PARTICIPATION VACUUM / LOW INTEREST"
        else:
            participation = "NORMAL PARTICIPATION"

        # =====================================================
        # INTERPRETATION ENGINE (RESTORED DEPTH)
        # =====================================================
        interpretation = []

        if latest_extreme_spike:
            interpretation.append("Extreme volume expansion detected.")
        elif latest_major_spike:
            interpretation.append("Major institutional spike detected.")
        elif latest_spike:
            interpretation.append("Volume spike above baseline.")

        if latest_contraction:
            interpretation.append("Participation contraction detected.")

        if latest_price_change != "N/A":
            if latest_price_change > 0 and latest_rvol_20 > 1.5:
                interpretation.append("Bullish expansion confirmed.")
            elif latest_price_change < 0 and latest_rvol_20 > 1.5:
                interpretation.append("Distribution pressure detected.")
            elif abs(latest_price_change) < 0.5 and latest_rvol_20 > 2:
                interpretation.append("Absorption/compression detected.")

        if green_volume > red_volume:
            interpretation.append("Buyer-dominant flow.")
        elif red_volume > green_volume:
            interpretation.append("Seller-dominant flow.")

        interpretation.append(f"Volume trend: {volume_trend}")

        # =====================================================
        # SNAPSHOTS
        # =====================================================
        recent_rvol = [round(v, 2) for v in df["rvol_20"].tail(5)]
        recent_volumes = [int(v) for v in volume_series.tail(5)]

        # =====================================================
        # FINAL OUTPUT (RESTORED FULL REPORT)
        # =====================================================
        return f"""
📊 Volume Analysis Summary ({timeframe})

==================================================

📌 Core Metrics
- Rows: {len(df)}
- Close: {latest_close}
- Change %: {latest_price_change}
- Volume: {latest_volume:,}

- RVOL(5): {latest_rvol_5}
- RVOL({rvol_window}): {latest_rvol_20}
- ZScore: {latest_zscore}

==================================================

📈 Participation State
- {participation}
- Institutional State: {inst_state}

==================================================

📊 Flow Metrics
- Up Volume %: {up_vol_pct:.2f}
- Down Volume %: {down_vol_pct:.2f}
- OBV Slope: {obv_trend:.2f}
- A/D Slope: {ad_trend:.2f}

==================================================

🧠 Order Flow
- Buyer Volume: {int(green_volume):,}
- Seller Volume: {int(red_volume):,}
- A/D Value: {ad_value:,}

==================================================

⚡ Events
- Spikes: {spike_count}
- Major: {major_spike_count}
- Extreme: {extreme_spike_count}
- Contraction: {contraction_count}

==================================================

🧠 Interpretation
- {' '.join(interpretation)}

==================================================

📉 Recent RVOL
{recent_rvol}

📉 Recent Volume
{recent_volumes}
"""
    except Exception as e:
        return f"Volume analysis error: {e}"