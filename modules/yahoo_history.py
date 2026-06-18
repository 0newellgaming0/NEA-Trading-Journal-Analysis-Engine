# =========================================================
# LOAD YAHOO HISTORICAL DATA (REFINED INSTITUTIONAL VERSION)
# MODULE: modules/yahoo_history.py
# =========================================================
from modules.path_resolver import get_stock_data_path

def load_yahoo_history(ticker, timeframe="daily", limit=80, debug=False):

    try:
        import pandas as pd
        import numpy as np
        import os

        # =====================================================
        # PATH RESOLUTION
        # =====================================================
        file_path = get_stock_data_path(ticker, timeframe=timeframe)

        if not os.path.exists(file_path):
            return f"No historical data file found at:\n{file_path}"

        df = pd.read_csv(file_path)

        if df.empty:
            return "Historical file exists but is empty."

        df = df.tail(limit).copy()

        # =====================================================
        # SAFE NUMERIC CONVERSION
        # =====================================================
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        ticker_lower = ticker.lower()

        def resolve_col(df, base):
            pref = f"{base}_{ticker_lower}"
            return pref if pref in df.columns else base

        close_col = resolve_col(df, "close")
        volume_col = resolve_col(df, "volume")
        high_col = resolve_col(df, "high")
        low_col = resolve_col(df, "low")

        # =====================================================
        # CORE METRICS
        # =====================================================
        latest_close = df[close_col].iloc[-1]
        latest_volume = df[volume_col].iloc[-1]
        period_high = df[high_col].max()
        period_low = df[low_col].min()
        last_5_closes = df[close_col].tail(5).tolist()

        # =====================================================
        # CENTRALIZED AO/AC ENGINE
        # =====================================================
        def calc_ao_ac(data):
            median = (data[high_col] + data[low_col]) / 2

            ao = (
                median.rolling(5, min_periods=5).mean()
                - median.rolling(34, min_periods=34).mean()
            )

            ac = ao - ao.rolling(5, min_periods=5).mean()

            return ao, ac

        ao, ac = calc_ao_ac(df)

        df["ao"] = ao
        df["ac"] = ac

        df["ao_prev"] = df["ao"].shift(1)

        df["ao_ac_confirm"] = (
            ((df["ac"] > 0) & (df["ao"] > df["ao_prev"])) |
            ((df["ac"] < 0) & (df["ao"] < df["ao_prev"]))
        )

        latest_ao = df["ao"].dropna().iloc[-1] if df["ao"].notna().any() else 0
        latest_ac = df["ac"].dropna().iloc[-1] if df["ac"].notna().any() else 0
        prev_ao = df["ao"].dropna().iloc[-2] if df["ao"].notna().sum() > 1 else np.nan

        latest_confirm = bool(df["ao_ac_confirm"].iloc[-1]) if len(df) else False

        # =====================================================
        # AO STATE
        # =====================================================
        if latest_ao > 0:
            ao_state = "Positive AO → short-term strength above equilibrium"
        elif latest_ao < 0:
            ao_state = "Negative AO → short-term weakness below equilibrium"
        else:
            ao_state = "Neutral AO"

        if not pd.isna(prev_ao):
            if latest_ao > prev_ao:
                ao_trend = "AO rising → momentum expansion improving"
            elif latest_ao < prev_ao:
                ao_trend = "AO falling → momentum contraction increasing"
            else:
                ao_trend = "AO flat"
        else:
            ao_trend = "AO trend unavailable"

        # =====================================================
        # AC STATE
        # =====================================================
        if latest_ac > 0:
            ac_state = "AC positive → acceleration building"
        elif latest_ac < 0:
            ac_state = "AC negative → deceleration present"
        else:
            ac_state = "AC neutral"

        # =====================================================
        # REGIME
        # =====================================================
        if latest_ao > 0 and latest_ac > 0:
            regime = "Bullish expansion (trend strengthening)"

        elif latest_ao > 0 and latest_ac < 0:
            if not pd.isna(prev_ao) and latest_ao < prev_ao:
                regime = "Bullish re-acceleration setup (pullback absorption)"
            else:
                regime = "Bullish but losing momentum (pullback risk)"

        elif latest_ao < 0 and latest_ac < 0:
            regime = "Bearish expansion (trend strengthening)"

        elif latest_ao < 0 and latest_ac > 0:
            regime = "Bearish exhaustion / recovery attempt"

        else:
            regime = "Neutral / transition structure"

        # =====================================================
        # MULTI-TIMEFRAME ENGINE
        # =====================================================
        def tf_engine(tf):
            try:
                path = get_stock_data_path(ticker, timeframe=tf)

                if not os.path.exists(path):
                    return None

                tf_df = pd.read_csv(path).tail(limit)

                for c in tf_df.columns:
                    tf_df[c] = pd.to_numeric(tf_df[c], errors="coerce")

                h = resolve_col(tf_df, "high")
                l = resolve_col(tf_df, "low")

                if h not in tf_df.columns or l not in tf_df.columns:
                    return None

                median = (tf_df[h] + tf_df[l]) / 2
                ao_t = median.rolling(5, min_periods=5).mean() - median.rolling(34, min_periods=34).mean()
                ac_t = ao_t - ao_t.rolling(5, min_periods=5).mean()

                ao_v = ao_t.dropna().iloc[-1] if ao_t.notna().any() else 0
                ac_v = ac_t.dropna().iloc[-1] if ac_t.notna().any() else 0

                if ao_v > 0 and ac_v > 0:
                    reg = "Expanding bullish momentum"
                elif ao_v > 0 and ac_v < 0:
                    reg = "Slowing bullish momentum"
                elif ao_v < 0 and ac_v < 0:
                    reg = "Expanding bearish momentum"
                elif ao_v < 0 and ac_v > 0:
                    reg = "Recovering bearish momentum"
                else:
                    reg = "Neutral / transition"

                return {
                    "ao": float(ao_v),
                    "ac": float(ac_v),
                    "regime": reg
                }

            except Exception as e:
                if debug:
                    print(f"TF error {tf}: {e}")
                return None

        tf_snapshots = {
            "intraday_15m": tf_engine("intraday_15m"),
            "intraday_60m": tf_engine("intraday_60m"),
            "daily": tf_engine("daily")
        }

        # =====================================================
        # OUTPUT
        # =====================================================
        tf_label = timeframe.replace("_", " ").title()

        confirm_text = (
            "AO/AC structures aligned (confirming momentum continuity)"
            if latest_confirm else
            "No AO/AC structural confirmation"
        )

        return f"""
Recent {limit} {tf_label} Bars Summary:
- Rows loaded: {len(df)}
- Latest Close: {latest_close}
- Latest Volume: {latest_volume}
- Period High: {period_high}
- Period Low: {period_low}
- Last 5 Closes: {last_5_closes}

📊 Momentum Engine (AO / AC):

- AO: {latest_ao:.6f}
- AC: {latest_ac:.6f}

📌 AO State:
{ao_state}
{ao_trend}

📌 AC State:
{ac_state}

📊 Regime:
{regime}

🔍 Alignment:
{confirm_text}

# =====================================================
# MULTI-TIMEFRAME MOMENTUM CONTEXT (AO / AC)
# =====================================================

15m:
- AO: {tf_snapshots.get("intraday_15m", {}).get("ao", "N/A")}
- AC: {tf_snapshots.get("intraday_15m", {}).get("ac", "N/A")}
- Regime: {tf_snapshots.get("intraday_15m", {}).get("regime", "N/A")}

60m:
- AO: {tf_snapshots.get("intraday_60m", {}).get("ao", "N/A")}
- AC: {tf_snapshots.get("intraday_60m", {}).get("ac", "N/A")}
- Regime: {tf_snapshots.get("intraday_60m", {}).get("regime", "N/A")}

Daily:
- AO: {tf_snapshots.get("daily", {}).get("ao", "N/A")}
- AC: {tf_snapshots.get("daily", {}).get("ac", "N/A")}
- Regime: {tf_snapshots.get("daily", {}).get("regime", "N/A")}
"""

    except Exception as e:
        return f"History load error: {e}"