# ==========================================================
# HISTORICAL ANALYSIS ENGINE
# PROFESSIONAL STRUCTURAL ANALYSIS + T-LINE FRAMEWORK
# ==========================================================

import pandas as pd
import numpy as np
import logging
import re


# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger("historicalAnalysis")

if not logger.handlers:

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "[HISTORICAL_ANALYSIS] %(levelname)s - %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.setLevel(logging.INFO)


# ==========================================================
# COLUMN FLATTENER
# ==========================================================

def force_flat_columns(df: pd.DataFrame) -> pd.DataFrame:

    logger.info("Flattening dataframe columns...")

    try:

        if isinstance(df.columns, pd.MultiIndex):

            df.columns = [
                "_".join(map(str, c)).strip().lower()
                for c in df.columns
            ]

        df.columns = [
            str(c).strip().lower()
            for c in df.columns
        ]

        logger.info("Column flattening complete")

        return df

    except Exception as e:

        logger.exception(f"force_flat_columns failed: {e}")

        raise


# ==========================================================
# SAFE FLOAT
# ==========================================================

def f(x):

    try:

        if isinstance(x, pd.Series):
            x = x.iloc[-1]

        if pd.isna(x):
            return np.nan

        return float(x)

    except Exception:

        return np.nan


# ==========================================================
# BASIC INDICATORS
# ==========================================================

def sma(series: pd.Series, window: int):

    logger.info(f"Calculating SMA{window}")

    try:

        return series.rolling(
            window,
            min_periods=1
        ).mean()

    except Exception as e:

        logger.exception(f"SMA{window} failed: {e}")

        return pd.Series(np.nan, index=series.index)


def ema(series: pd.Series, window: int):

    logger.info(f"Calculating EMA{window}")

    try:

        return series.ewm(
            span=window,
            adjust=False
        ).mean()

    except Exception as e:

        logger.exception(f"EMA{window} failed: {e}")

        return pd.Series(np.nan, index=series.index)


def rvol(volume: pd.Series, window: int = 20):

    logger.info("Calculating RVOL")

    try:

        return volume / volume.rolling(
            window,
            min_periods=1
        ).mean()

    except Exception as e:

        logger.exception(f"RVOL failed: {e}")

        return pd.Series(np.nan, index=volume.index)


def rsi(close: pd.Series, window: int = 14):

    logger.info("Calculating RSI")

    try:

        delta = close.diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(
            window,
            min_periods=1
        ).mean()

        avg_loss = loss.rolling(
            window,
            min_periods=1
        ).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        return 100 - (100 / (1 + rs))

    except Exception as e:

        logger.exception(f"RSI failed: {e}")

        return pd.Series(np.nan, index=close.index)


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14
):

    logger.info("Calculating ATR")

    try:

        prev_close = close.shift(1)

        tr = pd.concat([

            high - low,

            (high - prev_close).abs(),

            (low - prev_close).abs()

        ], axis=1).max(axis=1)

        return tr.rolling(
            window,
            min_periods=1
        ).mean()

    except Exception as e:

        logger.exception(f"ATR failed: {e}")

        return pd.Series(np.nan, index=close.index)


def volatility(close: pd.Series, window: int = 30):

    logger.info("Calculating Volatility")

    try:

        return (
            close.pct_change()
            .rolling(window, min_periods=1)
            .std()
            * np.sqrt(252)
            * 100
        )

    except Exception as e:

        logger.exception(f"Volatility failed: {e}")

        return pd.Series(np.nan, index=close.index)


def liquidity(close: pd.Series, volume: pd.Series):

    logger.info("Calculating Liquidity")

    try:

        v5 = volume.rolling(5, min_periods=1).mean()
        v20 = volume.rolling(20, min_periods=1).mean()

        dv = close * volume

        d5 = dv.rolling(5, min_periods=1).mean()
        d20 = dv.rolling(20, min_periods=1).mean()

        return (
            (
                v5 / v20.replace(0, np.nan)
            ) +
            (
                d5 / d20.replace(0, np.nan)
            )
        ) / 2

    except Exception as e:

        logger.exception(f"Liquidity failed: {e}")

        return pd.Series(np.nan, index=close.index)


def compression(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series
):

    logger.info("Calculating Compression")

    try:

        pr = (
            (high - low)
            / close.replace(0, np.nan)
        ) * 100

        r20 = pr.rolling(
            20,
            min_periods=1
        ).mean()

        r50 = r20.rolling(
            50,
            min_periods=1
        ).mean()

        return r20 / r50.replace(0, np.nan)

    except Exception as e:

        logger.exception(f"Compression failed: {e}")

        return pd.Series(np.nan, index=close.index)


def clv(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series
):

    logger.info("Calculating CLV")

    try:

        rng = (high - low).replace(0, np.nan)

        return (close - low) / rng

    except Exception as e:

        logger.exception(f"CLV failed: {e}")

        return pd.Series(np.nan, index=close.index)


# ==========================================================
# RETURNS
# ==========================================================

def calculate_returns(close: pd.Series):

    logger.info("Calculating returns")

    try:

        def r(period):

            if len(close) <= period:
                return np.nan

            return (
                close.pct_change(period)
                .iloc[-1]
            ) * 100

        return {

            "1D": r(1),
            "1W": r(5),
            "1M": r(21),
            "3M": r(63),
            "6M": r(126),
            "1Y": r(252)

        }

    except Exception as e:

        logger.exception(f"Returns failed: {e}")

        return {}


# ==========================================================
# T-LINE STATE
# ==========================================================

def tline_state(close, ema8):

    logger.info("Calculating T-Line state")

    try:

        latest_close = f(close.iloc[-1])

        latest_tline = f(ema8.iloc[-1])

        slope = f(ema8.diff().iloc[-1])

        if latest_close > latest_tline and slope > 0:
            return "Bullish Trend"

        if latest_close < latest_tline and slope < 0:
            return "Bearish Trend"

        return "Neutral / Weak Trend"

    except Exception as e:

        logger.exception(f"T-Line state failed: {e}")

        return "Unknown"


# ==========================================================
# T-LINE HOLD/BREAK
# ==========================================================

def tline_hold_break(close, high, low, ema8):

    logger.info("Calculating T-Line hold/break")

    try:

        c = f(close.iloc[-1])
        h = f(high.iloc[-1])
        l = f(low.iloc[-1])
        t = f(ema8.iloc[-1])

        # ==================================================
        # BULLISH HOLD
        # ==================================================

        if c > t and l >= t:
            return "Bullish Hold"

        # ==================================================
        # BEARISH HOLD
        # ==================================================

        if c < t and h <= t:
            return "Bearish Hold"

        # ==================================================
        # BULLISH RECLAIM
        # ==================================================

        if c > t and l < t:
            return "Bullish Reclaim"

        # ==================================================
        # BEARISH BREAKDOWN
        # ==================================================

        if c < t and h > t:
            return "Bearish Breakdown"

        return "Neutral"

    except Exception as e:

        logger.exception(
            f"T-Line hold/break failed: {e}"
        )

        return "Unknown"


# ==========================================================
# EMA SLOPE
# ==========================================================

def ema_slope(series):

    logger.info("Calculating EMA slope")

    try:

        return series.diff()

    except Exception as e:

        logger.exception(f"EMA slope failed: {e}")

        return pd.Series(np.nan, index=series.index)


# ==========================================================
# STRONG CANDLE
# ==========================================================

def strong_candle(open_, high, low, close):

    logger.info("Detecting strong continuation candle")

    try:

        body = (close - open_).abs()

        rng = (high - low).replace(0, np.nan)

        return (body / rng) > 0.6

    except Exception as e:

        logger.exception(f"Strong candle failed: {e}")

        return pd.Series(False, index=close.index)


# ==========================================================
# REJECTION SIGNAL
# ==========================================================

def rejection_signal(high, low, close, ema8):

    logger.info("Detecting rejection signals")

    try:

        bullish = (low < ema8) & (close > ema8)

        bearish = (high > ema8) & (close < ema8)

        signal = pd.Series(
            "None",
            index=close.index
        )

        signal[bullish] = "Bullish Rejection"

        signal[bearish] = "Bearish Rejection"

        return signal

    except Exception as e:

        logger.exception(f"Rejection signal failed: {e}")

        return pd.Series("None", index=close.index)

# ==========================================================
# TREND FAILURE
# ==========================================================

def trend_failure(close, ema8):

    logger.info("Detecting trend failure")

    try:

        below = (close < ema8).astype(bool)
        above = (close > ema8).astype(bool)

        previous_below = below.shift(1, fill_value=False)
        previous_above = above.shift(1, fill_value=False)

        bull_fail = below & previous_below
        bear_fail = above & previous_above

        result = pd.Series(
            "None",
            index=close.index,
            dtype="object"
        )

        result.loc[bull_fail] = "Bullish Failure"
        result.loc[bear_fail] = "Bearish Failure"

        return result

    except Exception as e:

        logger.exception(f"Trend failure failed: {e}")

        return pd.Series(
            "None",
            index=close.index,
            dtype="object"
        )

# ==========================================================
# T-LINE CONFIDENCE
# ==========================================================

def tline_confidence(close, ema8):

    logger.info("Calculating T-Line confidence")

    try:

        score = pd.Series(
            0,
            index=close.index
        )

        slope = ema8.diff()

        score += (close > ema8).astype(int)
        score += (slope > 0).astype(int)

        score -= (close < ema8).astype(int)
        score -= (slope < 0).astype(int)

        return score.clip(-3, 3)

    except Exception as e:

        logger.exception(f"T-Line confidence failed: {e}")

        return pd.Series(0, index=close.index)


# ==========================================================
# ATR TARGETS
# ==========================================================

def atr_targets(close, ema8, atr_series):

    logger.info("Calculating ATR targets")

    try:

        c = f(close.iloc[-1])
        t = f(ema8.iloc[-1])
        a = f(atr_series.iloc[-1])

        return {

            "bullish_stop": t - a,
            "bearish_stop": t + a,
            "bullish_target": c + (2 * a),
            "bearish_target": c - (2 * a)

        }

    except Exception as e:

        logger.exception(f"ATR targets failed: {e}")

        return {

            "bullish_stop": np.nan,
            "bearish_stop": np.nan,
            "bullish_target": np.nan,
            "bearish_target": np.nan

        }


# ==========================================================
# WYCKOFF PHASE
# ==========================================================

def wyckoff_phase(close, ema8):

    logger.info("Estimating Wyckoff phase")

    try:

        spread = (
            (close - ema8)
            / ema8.replace(0, np.nan)
        ) * 100

        latest = f(spread.iloc[-1])

        if abs(latest) < 1:
            return "Phase B - Range"

        if latest > 5:
            return "Phase E - Markup"

        if latest > 2:
            return "Phase D - Trend"

        if latest < -5:
            return "Markdown"

        return "Phase C - Trap/Test"

    except Exception as e:

        logger.exception(f"Wyckoff phase failed: {e}")

        return "Unknown"

# ==========================================================
# INTERPRETATION ENGINE (NEW - SAFE ADDITION)
# ==========================================================

def interpret_tline_state(state: str, slope: float) -> str:
    logger.info("Interpreting T-Line state")

    if state == "Bullish Trend":
        if slope > 0:
            return "Strong institutional accumulation trend with positive EMA8 slope confirming continuation pressure."
        return "Bullish structure present but weakening momentum due to flattening EMA8 slope."

    if state == "Bearish Trend":
        if slope < 0:
            return "Strong distribution phase with accelerating downside pressure confirmed by negative EMA8 slope."
        return "Bearish structure present but weakening downside momentum due to flattening slope."

    return "Price is transitioning between institutional phases with no clear directional control."


def interpret_hold_break(signal: str) -> str:
    logger.info("Interpreting hold/break structure")

    mapping = {

        "Bullish Hold":
            "Price continues respecting T-Line support, indicating sustained institutional accumulation and orderly trend continuation.",

        "Bearish Hold":
            "Price remains below T-Line resistance, signaling continued distribution pressure and weak demand participation.",

        "Bullish Reclaim":
            "Price reclaimed the T-Line after temporary weakness, suggesting recovery in short-term momentum and possible continuation of the broader bullish structure.",

        "Bearish Breakdown":
            "Price lost T-Line support and failed to reclaim it intraperiod, indicating weakening momentum and elevated risk of deeper retracement.",

        "Neutral":
            "Price interaction with the T-Line remains indecisive, reflecting transitional or rotational market behavior."
    }

    return mapping.get(signal, "No interpretation available.")
    
def build_tline_context(df, latest):
    logger.info("Building T-Line interpretation context")

    return {
        "trend_interpretation": interpret_tline_state(
            latest["TLineState"] if "TLineState" in latest else "Unknown",
            f(latest["EMASlope"])
        ),
        "hold_break_interpretation": interpret_hold_break(
            latest["TLineHoldBreak"] if "TLineHoldBreak" in latest else "Unknown"
        )
    }    


# ==========================================================
# MAIN ENGINE
# ==========================================================

def analyze_historical_data(
    df: pd.DataFrame,
    ticker: str
):

    logger.info("Starting historical analysis...")

    try:

        df = force_flat_columns(df)

        ticker = ticker.lower()

        close = pd.to_numeric(
            df[f"close_{ticker}"],
            errors="coerce"
        )

        high = pd.to_numeric(
            df[f"high_{ticker}"],
            errors="coerce"
        )

        low = pd.to_numeric(
            df[f"low_{ticker}"],
            errors="coerce"
        )

        open_ = pd.to_numeric(
            df[f"open_{ticker}"],
            errors="coerce"
        )

        volume = pd.to_numeric(
            df[f"volume_{ticker}"],
            errors="coerce"
        )

        logger.info(f"Loaded ticker series: {ticker.upper()}")

        # ==================================================
        # INDICATORS
        # ==================================================

        df["SMA20"] = sma(close, 20)
        df["SMA50"] = sma(close, 50)
        df["SMA200"] = sma(close, 200)

        df["EMA8"] = ema(close, 8)
        df["EMA9"] = ema(close, 9)
        df["EMA21"] = ema(close, 21)

        df["EMASlope"] = ema_slope(df["EMA8"])

        df["RVOL"] = rvol(volume)

        df["RSI"] = rsi(close)

        df["ATR"] = atr(
            high,
            low,
            close
        )

        df["Volatility"] = volatility(close)

        df["LiquidityScore"] = liquidity(
            close,
            volume
        )

        df["CompressionScore"] = compression(
            high,
            low,
            close
        )

        df["CLV"] = clv(
            high,
            low,
            close
        )

        df["StrongCandle"] = strong_candle(
            open_,
            high,
            low,
            close
        )

        df["RejectionSignal"] = rejection_signal(
            high,
            low,
            close,
            df["EMA8"]
        )

        df["TrendFailure"] = trend_failure(
            close,
            df["EMA8"]
        )

        df["TLineConfidence"] = tline_confidence(
            close,
            df["EMA8"]
        )

        # ==================================================
        # STATES
        # ==================================================

        latest = df.iloc[-1]

        returns = calculate_returns(close)

        tline_trend = tline_state(
            close,
            df["EMA8"]
        )

        hold_break = tline_hold_break(
            close,
            high,
            low,
            df["EMA8"]
        )
        
        logger.info(f"T-Line State: {tline_trend}")
        logger.info(f"T-Line Hold/Break: {hold_break}")
        logger.info("Generating T-Line interpretations...")
        
        # ==========================================================
        # INTERPRETATIONS (NEW)
        # ==========================================================

        tline_interpretation = interpret_tline_state(
            tline_trend,
            f(df["EMA8"].diff().iloc[-1])
        )

        hold_break_interpretation = interpret_hold_break(
            hold_break
        )

        wyckoff = wyckoff_phase(
            close,
            df["EMA8"]
        )

        targets = atr_targets(
            close,
            df["EMA8"],
            df["ATR"]
        )

        # ==================================================
        # TREND STRUCTURE
        # ==================================================

        c = f(latest["SMA20"])
        s50 = f(latest["SMA50"])
        s200 = f(latest["SMA200"])
        px = f(close.iloc[-1])

        if px > c > s50 > s200:
            trend = "Momentum Expansion"

        elif px > s50 > s200:
            trend = "Constructive Bullish Structure"

        elif px < c < s50:
            trend = "Weakening Structure"

        else:
            trend = "Neutral Structure"

        # ==================================================
        # STATES
        # ==================================================

        rvol_val = f(latest["RVOL"])
        rsi_val = f(latest["RSI"])
        comp_val = f(latest["CompressionScore"])

        participation_state = (
            "High Participation"
            if rvol_val > 2 else
            "Low Participation"
            if rvol_val < 0.8 else
            "Normal Participation"
        )

        volatility_state = (
            "Compression Regime"
            if comp_val < 0.8 else
            "Expansion Regime"
            if comp_val > 1.2 else
            "Normal Volatility"
        )

        momentum_state = (
            "Overbought / Strong Momentum"
            if rsi_val > 70 else
            "Oversold / Weak Momentum"
            if rsi_val < 30 else
            "Neutral Momentum"
        )

        # ==================================================
        # FULL PROMPT
        # ==================================================

        prompt_summary = f"""
==========================================================
HISTORICAL ANALYSIS REPORT
==========================================================

Ticker: {ticker.upper()}

==========================================================
TREND STRUCTURE
==========================================================

Primary Trend Structure:
{trend}

Close Price:
{f(close.iloc[-1]):.2f}

SMA20 / SMA50 / SMA200:
{f(latest["SMA20"]):.2f} /
{f(latest["SMA50"]):.2f} /
{f(latest["SMA200"]):.2f}

EMA9 / EMA21:
{f(latest["EMA9"]):.2f} /
{f(latest["EMA21"]):.2f}

==========================================================
PERFORMANCE
==========================================================

1D Return: {returns["1D"]:.2f}%
1W Return: {returns["1W"]:.2f}%
1M Return: {returns["1M"]:.2f}%
3M Return: {returns["3M"]:.2f}%
6M Return: {returns["6M"]:.2f}%
1Y Return: {returns["1Y"]:.2f}%

==========================================================
LIQUIDITY
==========================================================

RVOL:
{rvol_val:.2f}

Liquidity Score:
{f(latest["LiquidityScore"]):.2f}

Participation:
{participation_state}

==========================================================
VOLATILITY
==========================================================

ATR:
{f(latest["ATR"]):.2f}

Volatility:
{f(latest["Volatility"]):.2f}%

Compression Score:
{comp_val:.2f}

State:
{volatility_state}

==========================================================
MOMENTUM
==========================================================

RSI:
{rsi_val:.2f}

State:
{momentum_state}

CLV:
{f(latest["CLV"]):.2f}

==========================================================
T-LINE ANALYSIS
==========================================================

T-Line State:
{tline_trend}

T-Line Hold / Break:
{hold_break}

EMA8:
{f(latest["EMA8"]):.2f}

EMA8 Slope:
{f(latest["EMASlope"]):.4f}

T-Line Confidence:
{f(latest["TLineConfidence"]):.2f}

Trend Failure:
{latest["TrendFailure"]}

Rejection Signal:
{latest["RejectionSignal"]}

Strong Continuation Candle:
{bool(latest["StrongCandle"])}

==========================================================
WYCKOFF CONTEXT
==========================================================

Estimated Wyckoff Phase:
{wyckoff}

==========================================================
T-LINE INTERPRETATION LAYER
==========================================================

T-Line Context Interpretation:
{tline_interpretation}

Hold / Break Interpretation:
{hold_break_interpretation}

Note:
These interpretations represent institutional behavior inference,
not raw mechanical signals.

==========================================================
RISK MANAGEMENT
==========================================================

Bullish Stop:
{targets["bullish_stop"]:.2f}

Bearish Stop:
{targets["bearish_stop"]:.2f}

Bullish Target:
{targets["bullish_target"]:.2f}

Bearish Target:
{targets["bearish_target"]:.2f}

==========================================================
"""

        logger.info(
            "Historical analysis completed successfully"
        )

        return {

            "ticker": ticker.upper(),

            "dataframe": df,

            "trend": trend,

            "returns": returns,

            "latest_snapshot": latest.to_dict(),

            "prompt_summary": prompt_summary,

            "tline_state": tline_trend,

            "wyckoff_phase": wyckoff,

            "targets": targets

        }

    except Exception as e:

        logger.exception(
            f"Historical analysis failed: {e}"
        )

        return {

            "ticker": ticker.upper(),

            "dataframe": df,

            "trend": "Unknown",

            "returns": {},

            "latest_snapshot": {},

            "prompt_summary": "",

            "error": str(e)

        }

