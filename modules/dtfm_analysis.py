# =========================================================
# DUAL TIME FRAME MOMENTUM MODULE (DTFM)
# 60M vs DAILY STRUCTURAL MOMENTUM ENGINE
# =========================================================

import numpy as np
from modules.ohlcv_normalizer import normalize_timestamp


# =========================================================
# CORE ENGINE
# =========================================================

def analyze_dual_timeframe_momentum(
    df_60m,
    df_daily,
    ticker,
    timeframe_label="DTFM"
):

    try:

        # =====================================================
        # NORMALIZATION
        # =====================================================

        df_60m = normalize_timestamp(df_60m)
        df_daily = normalize_timestamp(df_daily)

        ticker = ticker.lower()

        close_col = f"close_{ticker}"
        high_col = f"high_{ticker}"
        low_col = f"low_{ticker}"
        volume_col = f"volume_{ticker}"

        # =====================================================
        # VALIDATION
        # =====================================================

        required_cols = [close_col, high_col, low_col, volume_col]

        for col in required_cols:

            if col not in df_60m.columns:
                return f"""
===========================
📊 DUAL TIME FRAME MOMENTUM ENGINE ERROR
===========================

Ticker: {ticker.upper()}
Missing 60M column: {col}

===========================
"""

            if col not in df_daily.columns:
                return f"""
===========================
📊 DUAL TIME FRAME MOMENTUM ENGINE ERROR
===========================

Ticker: {ticker.upper()}
Missing Daily column: {col}

===========================
"""

        if len(df_60m) < 30 or len(df_daily) < 30:
            return f"""
===========================
📊 DUAL TIME FRAME MOMENTUM ENGINE
===========================

Ticker: {ticker.upper()}

Insufficient data.

===========================
"""

        # =====================================================
        # EXTRACT OHLCV
        # =====================================================

        m60_close = df_60m[close_col].values
        m60_high = df_60m[high_col].values
        m60_low = df_60m[low_col].values
        m60_volume = df_60m[volume_col].values

        d_close = df_daily[close_col].values
        d_high = df_daily[high_col].values
        d_low = df_daily[low_col].values
        d_volume = df_daily[volume_col].values

        # =====================================================
        # MOMENTUM (SAFE RESTORED)
        # =====================================================

        m60_return_20 = 0.0
        daily_return_20 = 0.0

        if len(m60_close) >= 20:
            m60_return_20 = ((m60_close[-1] / m60_close[-20]) - 1) * 100

        if len(d_close) >= 20:
            daily_return_20 = ((d_close[-1] / d_close[-20]) - 1) * 100

        # =====================================================
        # SLOPE (SAFE RESTORED)
        # =====================================================

        m60_slope = np.nan
        daily_slope = np.nan

        if len(m60_close) >= 20:
            m60_slope = np.polyfit(range(20), m60_close[-20:], 1)[0]

        if len(d_close) >= 20:
            daily_slope = np.polyfit(range(20), d_close[-20:], 1)[0]

        # =====================================================
        # RANGE EXPANSION (RESTORED STRUCTURE)
        # =====================================================

        m60_range_ratio = 1.0
        daily_range_ratio = 1.0

        if len(m60_high) >= 30:
            m60_recent_range = np.mean(m60_high[-10:] - m60_low[-10:])
            m60_prior_range = np.mean(m60_high[-30:-10] - m60_low[-30:-10])
            m60_range_ratio = m60_recent_range / max(m60_prior_range, 1e-6)

        if len(d_high) >= 30:
            daily_recent_range = np.mean(d_high[-10:] - d_low[-10:])
            daily_prior_range = np.mean(d_high[-30:-10] - d_low[-30:-10])
            daily_range_ratio = daily_recent_range / max(daily_prior_range, 1e-6)

        # =====================================================
        # VOLUME EXPANSION (RESTORED STRUCTURE)
        # =====================================================

        m60_vol_ratio = 1.0
        daily_vol_ratio = 1.0

        if len(m60_volume) >= 30:
            m60_recent_vol = np.mean(m60_volume[-10:])
            m60_prior_vol = np.mean(m60_volume[-30:-10])
            m60_vol_ratio = m60_recent_vol / max(m60_prior_vol, 1e-6)

        if len(d_volume) >= 30:
            daily_recent_vol = np.mean(d_volume[-10:])
            daily_prior_vol = np.mean(d_volume[-30:-10])
            daily_vol_ratio = daily_recent_vol / max(daily_prior_vol, 1e-6)

        # =====================================================
        # STRUCTURE POSITION (RESTORED LOGIC)
        # =====================================================

        m60_position = 50.0
        daily_position = 50.0

        if len(m60_high) >= 20:
            m60_high_20 = np.max(m60_high[-20:])
            m60_low_20 = np.min(m60_low[-20:])
            m60_position = ((m60_close[-1] - m60_low_20) /
                            max(m60_high_20 - m60_low_20, 1e-6)) * 100

        if len(d_high) >= 20:
            daily_high_20 = np.max(d_high[-20:])
            daily_low_20 = np.min(d_low[-20:])
            daily_position = ((d_close[-1] - daily_low_20) /
                              max(daily_high_20 - daily_low_20, 1e-6)) * 100

        # =====================================================
        # ALIGNMENT (UNCHANGED)
        # =====================================================

        divergence = m60_return_20 - daily_return_20

        if m60_return_20 > 0 and daily_return_20 > 0:
            regime = "BULLISH ALIGNMENT"

        elif m60_return_20 < 0 and daily_return_20 < 0:
            regime = "BEARISH ALIGNMENT"

        elif m60_return_20 > 0 and daily_return_20 < 0:
            regime = "COUNTERTREND RECOVERY"

        else:
            regime = "DISTRIBUTION RISK"

        # =====================================================
        # INTERPRETATION (RESTORED)
        # =====================================================

        explanation = []

        if m60_return_20 > daily_return_20:
            explanation.append("60M momentum exceeds Daily momentum.")

        if m60_vol_ratio > 1.2:
            explanation.append("60M participation expanding.")

        if daily_vol_ratio > 1.2:
            explanation.append("Daily participation expanding.")

        if m60_range_ratio > 1.2:
            explanation.append("60M volatility expansion detected.")

        if daily_range_ratio > 1.2:
            explanation.append("Daily volatility expansion detected.")

        if m60_position > 80:
            explanation.append("60M near upper structure.")

        if daily_position > 80:
            explanation.append("Daily near upper structure.")

        # =====================================================
        # OUTPUT (UNCHANGED FORMAT RESTORED)
        # =====================================================

        return f"""
===========================
📊 DUAL TIME FRAME MOMENTUM ENGINE
===========================

Ticker: {ticker.upper()}

---------------------------
60M STRUCTURE
---------------------------
20-Bar Return: {m60_return_20:.2f}%
Slope: {m60_slope}
Range Expansion: {m60_range_ratio:.2f}
Volume Expansion: {m60_vol_ratio:.2f}
Position: {m60_position:.2f}%

---------------------------
DAILY STRUCTURE
---------------------------
20-Bar Return: {daily_return_20:.2f}%
Slope: {daily_slope}
Range Expansion: {daily_range_ratio:.2f}
Volume Expansion: {daily_vol_ratio:.2f}
Position: {daily_position:.2f}%

---------------------------
CROSS-TF
---------------------------
Regime: {regime}
Divergence: {divergence:.2f}%

---------------------------
INTERPRETATION
---------------------------
{chr(10).join('- ' + x for x in explanation)}

===========================
END
===========================
"""

    except Exception as e:

        return f"""
===========================
📊 DUAL TIME FRAME MOMENTUM ENGINE ERROR
===========================

Ticker: {ticker.upper()}
Error: {str(e)}

===========================
"""