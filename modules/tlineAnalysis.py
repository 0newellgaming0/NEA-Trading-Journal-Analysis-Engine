# ==========================================================
# T-Line Intraday Analysis Utilities
# ==========================================================
# Computes:
#   - EMA8 T-Line structure
#   - T-Line state (bullish / bearish / neutral)
#   - Hold / Break behavior
#   - Confidence scoring
#   - Rejection + failure signals
#   - Wyckoff context
# ==========================================================

import pandas as pd
import numpy as np
from modules.fractalEngine import (
    detect_liquidity_sweep,
    calculate_structural_position,
    classify_sequence
)

# ==========================================================
# SAFE HELPERS
# ==========================================================

def f(x):
    try:
        if isinstance(x, pd.Series):
            if x.empty:
                return np.nan
            x = x.iloc[-1]
        if pd.isna(x):
            return np.nan
        return float(x)
    except:
        return np.nan


def safe_last(series, default=np.nan):
    try:
        if series is None or len(series) == 0:
            return default
        return series.iloc[-1]
    except:
        return default

# ==========================================================
# INTRADAY INTERPRETATION LAYER (NEW)
# ==========================================================
def interpret_intraday_tline_state(state: str, slope: float) -> str:

    if state is None:
        return "No T-Line state data available."

    slope = 0.0 if slope is None else float(slope)

    # ===============================
    # BULLISH STRUCTURE
    # ===============================
    if state == "Bullish Trend":

        # strong momentum expansion
        if slope > 0.0005:
            return (
                "Strong intraday bullish expansion: EMA8 is sloping upward with price holding above dynamic support. "
                "Momentum is accelerating, indicating active institutional continuation participation."
            )

        # weakening bullish trend
        if -0.0005 <= slope <= 0.0005:
            return (
                "Bullish structure remains intact but momentum is flattening. "
                "Price is transitioning from expansion into consolidation or early distribution behavior."
            )

        # rare bearish slope inside bullish state
        return (
            "Bullish trend is structurally intact but slope deterioration suggests hidden supply absorption or early reversal risk. "
            "Monitor for breakdown of EMA8 support."
        )

    # ===============================
    # BEARISH STRUCTURE
    # ===============================
    if state == "Bearish Trend":

        # strong bearish expansion
        if slope < -0.0005:
            return (
                "Strong intraday bearish expansion: EMA8 is sloping downward with sustained price rejection below trend. "
                "Institutional distribution is active with continuation pressure."
            )

        # weakening bearish trend
        if -0.0005 <= slope <= 0.0005:
            return (
                "Bearish structure persists but downside momentum is slowing. "
                "Market is transitioning toward consolidation or potential reversal build."
            )

        # rare bullish slope inside bearish state
        return (
            "Bearish trend remains structurally active but upward slope shift suggests absorption and potential reversal formation. "
            "Watch for reclaim attempts above EMA8."
        )

    # ===============================
    # NEUTRAL / TRANSITION STATE
    # ===============================
    if state in ("Neutral / Weak Trend", "TRANSITION", "Neutral"):

        if abs(slope) < 0.0003:
            return (
                "Low volatility equilibrium: EMA8 is flat and price is rotational. "
                "Institutional activity is balanced with no directional commitment."
            )

        if slope > 0:
            return (
                "Early bullish transition: EMA8 slope is turning upward but structure is not confirmed. "
                "Potential breakout development phase."
            )

        if slope < 0:
            return (
                "Early bearish transition: EMA8 slope is turning downward with weakening structure. "
                "Potential breakdown development phase."
            )

    # ===============================
    # FALLBACK
    # ===============================
    return (
        "Intraday structure unclear: insufficient directional alignment between price and EMA8 structure. "
        "Expect rotational or unstable conditions."
    )

def interpret_intraday_hold_break(signal: str) -> str:

    if signal is None:
        return "No hold/break signal detected."

    signal = str(signal)

    # ===============================
    # BULLISH STRUCTURE
    # ===============================
    if signal == "Bullish Hold":
        return (
            "Strong bullish hold: price is consistently defending EMA8 support with controlled pullbacks. "
            "Suggests accumulation and continuation bias remains intact."
        )

    if signal == "Bullish Reclaim":
        return (
            "Bullish reclaim event: price briefly lost EMA8 but quickly regained it. "
            "This reflects absorption of selling pressure and responsive institutional buying. "
            "Continuation probability increases if follow-through holds above EMA8."
        )

    # ===============================
    # BEARISH STRUCTURE
    # ===============================
    if signal == "Bearish Hold":
        return (
            "Strong bearish hold: price is repeatedly failing to reclaim EMA8 from below. "
            "Indicates persistent distribution pressure and weak demand response."
        )

    if signal == "Bearish Breakdown":
        return (
            "Bearish breakdown confirmed: price lost EMA8 support and failed retest. "
            "Structure indicates active distribution with downside continuation risk."
        )

    # ===============================
    # WEAK / NEUTRAL STATES
    # ===============================
    if signal == "Neutral":
        return (
            "Neutral intraday structure: price is oscillating around EMA8 without directional commitment. "
            "No clear hold or break behavior; expect rotational conditions."
        )

    # ===============================
    # UNKNOWN PATTERN
    # ===============================
    return (
        "Unclassified hold/break behavior: signal does not match known intraday structure patterns. "
        "Interpret with caution and confirm against EMA8 alignment and slope."
    )

def interpret_intraday_wyckoff(state: str) -> str:

    if state is None:
        return "No Wyckoff state data available."

    state = str(state)

    # ================================
    # STRONG TREND PHASES
    # ================================

    if "Markup" in state:

        if "strong" in state.lower() or "expansion" in state.lower():
            return (
                "Strong intraday markup phase: aggressive institutional accumulation, "
                "trend acceleration above EMA structure, and continuation conditions dominant."
            )

        return (
            "Intraday markup phase: bullish expansion underway with sustained buying pressure. "
            "Price is trending with momentum and limited mean-reversion behavior."
        )

    if "Markdown" in state:

        if "strong" in state.lower() or "impulse" in state.lower():
            return (
                "Strong intraday markdown phase: heavy institutional distribution, "
                "accelerated downside expansion, and breakdown continuation conditions active."
            )

        return (
            "Intraday markdown phase: persistent selling pressure with weak demand absorption. "
            "Trend remains downward with continuation bias."
        )

    # ================================
    # BALANCE / RANGE STRUCTURE
    # ================================

    if "Range" in state or "Balance" in state:

        if "tight" in state.lower() or "compression" in state.lower():
            return (
                "Tight intraday balance: volatility compression near equilibrium. "
                "Institutional accumulation/distribution likely building for breakout expansion."
            )

        return (
            "Intraday equilibrium phase: rotational balance between buyers and sellers. "
            "No dominant directional control; absorption and distribution both active."
        )

    # ================================
    # TRANSITION PHASES
    # ================================

    if "Transition" in state:

        if "up" in state.lower() or "reclaim" in state.lower():
            return (
                "Bullish transition phase: early signs of reclaim and structural shift upward. "
                "Potential breakout initiation forming above EMA framework."
            )

        if "down" in state.lower() or "breakdown" in state.lower():
            return (
                "Bearish transition phase: early structural weakening and breakdown risk. "
                "Price may be shifting from balance into markdown expansion."
            )

        return (
            "Intraday transition phase: market is unstable with no confirmed directional bias. "
            "Breakout or breakdown likely approaching as structure resolves."
        )

    # ================================
    # DEFAULT FALLBACK
    # ================================

    return "No clear intraday Wyckoff context detected."
    
# ==========================================================
# CORE T-LINE CALCULATIONS
# ==========================================================

def ema(series: pd.Series, window: int = 8):
    return series.ewm(span=window, adjust=False).mean()


def ema_slope(series: pd.Series):
    return series.diff()

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):

    high = pd.Series(high).dropna()
    low = pd.Series(low).dropna()
    close = pd.Series(close).dropna()

    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)

    return tr.ewm(span=period, adjust=False).mean()
    
# ==========================================================
# FIXED T-LINE STOP (CRITICAL FIX)
# ==========================================================
def tline_stop_price(close: pd.Series,
                     ema8: pd.Series,
                     high: pd.Series,
                     low: pd.Series):

    import numpy as np
    import pandas as pd

    if close is None or ema8 is None or high is None or low is None:
        return np.nan

    df = pd.concat([close, ema8, high, low], axis=1).dropna()
    if df.empty:
        return np.nan

    c = df.iloc[-1, 0]
    e = df.iloc[-1, 1]

    # ATR calculation MUST exist in same module
    atr_series = atr(high, low, close, 14)

    atr_val = atr_series.dropna().iloc[-1] if not atr_series.dropna().empty else np.nan

    if pd.isna(atr_val):
        atr_val = abs(e) * 0.01  # fallback only if needed

    if c > e:
        return float(e - atr_val)

    return float(e + atr_val)
    
def trend_state_machine(close: pd.Series, ema8: pd.Series):

    c = f(close)
    t = f(ema8)
    slope = f(ema_slope(ema8))

    if c > t and slope > 0:
        return "UPTREND"

    if c < t and slope < 0:
        return "DOWNTREND"

    return "TRANSITION"
    
def market_regime(close: pd.Series, ema8: pd.Series):

    c = close
    t = ema8

    slope = ema_slope(ema8)

    latest_c = f(c)
    latest_t = f(t)
    latest_slope = f(slope)

    # --------------------------------------------------
    # STRUCTURE DETECTION
    # --------------------------------------------------

    below = c < t
    above = c > t

    lower_high_structure = (c < c.shift(1)) & below
    higher_low_structure = (c > c.shift(1)) & above

    breakdown_present = (c.shift(1) > t.shift(1)) & (c < t)
    reclaim_present = (c.shift(1) < t.shift(1)) & (c > t)

    cross_frequency = (c > t).rolling(5).apply(lambda x: len(set(x)) > 1)

    # --------------------------------------------------
    # REGIME LOGIC (STRUCTURE-FIRST)
    # --------------------------------------------------

    # CHOP ONLY IF TRUE ROTATION
    if (
        abs(latest_slope) < 0.001 and
        cross_frequency.iloc[-1] == 1
    ):
        return "CHOP"

    # TREND UP
    if (
        latest_c > latest_t and
        (latest_slope > 0 or higher_low_structure.sum() > 0 or reclaim_present.sum() > 0)
    ):
        return "TREND_UP"

    # TREND DOWN
    if (
        latest_c < latest_t and
        (latest_slope < 0 or lower_high_structure.sum() > 0 or breakdown_present.sum() > 0)
    ):
        return "TREND_DOWN"

    # TRANSITION (only true uncertainty state)
    return "TRANSITION" 

def fractal_regime_override(close, high, low, ema8, fractal_data=None):

    c = f(close)
    t = f(ema8)

    # --------------------------------------------------
    # STRUCTURE SIGNALS (FROM FRACTAL ENGINE)
    # --------------------------------------------------

    structural_pos = calculate_structural_position(
        c,
        max(close.tail(20)),
        min(close.tail(20))
    )

    sweep = detect_liquidity_sweep(
        f(high),
        f(low),
        c,
        max(close.tail(20)),
        min(close.tail(20))
    )

    # --------------------------------------------------
    # OVERRIDE LOGIC
    # --------------------------------------------------

    # STRONG DIRECTIONAL DOWN STRUCTURE
    if (
        c < t and
        structural_pos is not None and
        structural_pos < 0.4
    ):
        return "TREND_DOWN"

    # STRONG DIRECTIONAL UP STRUCTURE
    if (
        c > t and
        structural_pos is not None and
        structural_pos > 0.6
    ):
        return "TREND_UP"

    # LIQUIDITY EVENT OVERRIDE (IMPORTANT)
    if sweep:
        if sweep["type"] in ["BullishSweep", "BearishSweep"]:
            return "TRANSITION"

    return None
    
def tline_state(close: pd.Series, ema8: pd.Series):

    latest_close = f(close)
    latest_tline = f(ema8)
    slope = f(ema8.diff())

    if latest_close > latest_tline and slope > 0:
        return "Bullish Trend"

    if latest_close < latest_tline and slope < 0:
        return "Bearish Trend"

    return "Neutral / Weak Trend"


def tline_hold_break(close, high, low, ema8):

    c = f(close)
    h = f(high)
    l = f(low)
    t = f(ema8)

    if c > t and l >= t:
        return "Bullish Hold"

    if c < t and h <= t:
        return "Bearish Hold"

    if c > t and l < t:
        return "Bullish Reclaim"

    if c < t and h > t:
        return "Bearish Breakdown"

    return "Neutral"


def tline_score(close, ema8):

    c = f(close)
    t = f(ema8)
    slope = f(ema_slope(ema8))

    score = 0

    # EMA position (30)
    if c > t:
        score += 30
    else:
        score -= 30

    # slope (25)
    if slope > 0:
        score += 25
    else:
        score -= 25

    # structure alignment (25)
    if c > t and slope > 0:
        score += 25
    else:
        score -= 10

    # normalization to 0–100
    return max(0, min(100, score + 60))


def rejection_signal(high, low, close, ema8):

    bullish = (low < ema8) & (close > ema8)
    bearish = (high > ema8) & (close < ema8)

    signal = pd.Series("None", index=close.index)

    signal.loc[bullish] = "Bullish Rejection"
    signal.loc[bearish] = "Bearish Rejection"

    return signal

def detect_jhook(close, ema8):

    return (
        (close.shift(3) > ema8.shift(3)) &
        (close.shift(1) < ema8.shift(1)) &
        (close > ema8)
    ).map(lambda x: "J-Hook" if x else "None")
    
def detect_flag(close, ema8):

    slope = ema8.diff().rolling(3).mean()

    out = pd.Series("None", index=close.index)

    out.loc[(close > ema8) & (slope > 0)] = "Bull Flag"
    out.loc[(close < ema8) & (slope < 0)] = "Bear Flag"

    return out

def detect_squeeze(close, ema8):

    compression = (close - ema8).abs() / ema8

    return compression.map(lambda x: "Squeeze" if x < 0.01 else "None")

def detect_reclaim_trap(close, ema8):

    return (
        (close.shift(1) < ema8.shift(1)) &
        (close > ema8)
    ).map(lambda x: "Reclaim Trap" if x else "None")

def detect_structure_ladder(close, ema8):

    higher_low = (close > close.shift(1)) & (close > ema8)
    lower_high = (close < close.shift(1)) & (close < ema8)

    out = pd.Series("None", index=close.index)
    out.loc[higher_low] = "Higher Low Ladder"
    out.loc[lower_high] = "Lower High Ladder"

    return out

def detect_momentum_extension(close, ema8):

    dist = (close - ema8) / ema8

    return dist.map(lambda x: "Momentum Extension" if x > 0.05 else "None")    

def trend_failure(close, ema8):

    below = close < ema8
    above = close > ema8

    prev_below = below.shift(1, fill_value=False)
    prev_above = above.shift(1, fill_value=False)

    result = pd.Series("None", index=close.index)

    result.loc[below & prev_below] = "Bullish Failure"
    result.loc[above & prev_above] = "Bearish Failure"

    return result


def wyckoff_phase(close, ema8):

    spread = (close - ema8) / ema8.replace(0, np.nan)
    latest = f(spread)

    if abs(latest) < 0.01:
        return "Range / Balance"
    if latest > 0.05:
        return "Markup"
    if latest < -0.05:
        return "Markdown"

    return "Transition"


# ==========================================================
# MAIN INTRADAY ANALYSIS ENGINE
# ==========================================================
def analyze_tline_intraday(df: pd.DataFrame, ticker: str, label: str):

    try:

        if df is None or df.empty:
            return f"{label} T-LINE ANALYSIS UNAVAILABLE (EMPTY DATA)"

        ticker = ticker.lower()

        close = pd.to_numeric(df[f"close_{ticker}"], errors="coerce")
        high = pd.to_numeric(df[f"high_{ticker}"], errors="coerce")
        low = pd.to_numeric(df[f"low_{ticker}"], errors="coerce")

        ema8 = ema(close, 8)
        slope = ema_slope(ema8)
        
        # ALWAYS compute scalar stop directly from latest EMA/close
        tline_stop = tline_stop_price(close, ema8, high, low)

        # force final safety scalar (removes all Series edge cases)
        tline_stop = float(tline_stop) if tline_stop is not None and not pd.isna(tline_stop) else np.nan

        tline_stop_display = (
            f"{tline_stop:.4f}"
            if not np.isnan(tline_stop)
            else "N/A"
        )
        
        # ==========================================
        # PRESERVE TREND STATE MACHINE
        # ==========================================
        trend_raw = trend_state_machine(close, ema8)

        fractal_override = fractal_regime_override(
            close,
            high,
            low,
            ema8
        )

        if fractal_override is not None:
            regime = fractal_override
        else:
            regime = market_regime(close, ema8)

        score = tline_score(close, ema8)

        jhook = detect_jhook(close, ema8)
        flag = detect_flag(close, ema8)
        squeeze = detect_squeeze(close, ema8)
        trap = detect_reclaim_trap(close, ema8)
        ladder = detect_structure_ladder(close, ema8)
        momentum = detect_momentum_extension(close, ema8)

        # ==========================================
        # PRESERVE T-LINE STATE SEPARATELY
        # ==========================================
        tline = tline_state(close, ema8)

        hold_break = tline_hold_break(
            close,
            high,
            low,
            ema8
        )

        rejection = rejection_signal(
            high,
            low,
            close,
            ema8
        )

        failure = trend_failure(
            close,
            ema8
        )

        wyckoff = wyckoff_phase(
            close,
            ema8
        )

        # ==========================================
        # META CONSENSUS
        # ==========================================
        votes = {
            "trend": (
                1 if trend_raw == "UPTREND"
                else -1 if trend_raw == "DOWNTREND"
                else 0
            ),
            "tline": (
                1 if "Bullish" in tline
                else -1 if "Bearish" in tline
                else 0
            ),
            "regime": (
                1 if "UP" in regime
                else -1 if "DOWN" in regime
                else 0
            )
        }

        meta_score = sum(votes.values())

        if meta_score >= 2:
            meta_state = "BULLISH_META"
        elif meta_score <= -2:
            meta_state = "BEARISH_META"
        else:
            meta_state = "MIXED_META"

        consensus_sign = np.sign(meta_score)

        conflict_score = len(
            [
                v for v in votes.values()
                if consensus_sign != 0 and v != consensus_sign
            ]
        )

        # ==========================================
        # INTERPRETATIONS
        # ==========================================
        state_interp = interpret_intraday_tline_state(
            tline,
            f(slope)
        )

        hold_interp = interpret_intraday_hold_break(
            hold_break
        )

        wyckoff_interp = interpret_intraday_wyckoff(
            wyckoff
        )

        return f"""
==========================================================
{label} T-LINE ANALYSIS
==========================================================

T-Line State:
{tline}

Interpretation:
{state_interp}

T-Line Hold / Break:
{hold_break}

Interpretation:
{hold_interp}

EMA8:
{f(ema8):.2f}

EMA8 Slope:
{f(slope):.4f}

T-LINE STOP:
{tline_stop_display}

Trend Failure:
{safe_last(failure, "None")}

Rejection Signal:
{safe_last(rejection, "None")}

TREND STATE MACHINE:
{trend_raw}

T-LINE STATE:
{tline}

REGIME:
{regime}

T-LINE SCORE:
{score}/100

META CONSENSUS:
{meta_state}

META SCORE:
{meta_score}

CONFLICT SCORE:
{conflict_score}

FORMATIONS:
- J-Hook: {safe_last(jhook, "None")}
- Flag: {safe_last(flag, "None")}
- Squeeze: {safe_last(squeeze, "None")}
- Trap: {safe_last(trap, "None")}
- Ladder: {safe_last(ladder, "None")}
- Momentum: {safe_last(momentum, "None")}

Wyckoff Phase:
{wyckoff}

Interpretation:
{wyckoff_interp}

==========================================================
"""

    except Exception as e:

        return f"""
==========================================================
{label} T-LINE ANALYSIS
==========================================================

ERROR:
{str(e)}

==========================================================
"""

def analyze_multi_timeframe(df, ticker, label):

    tf_15 = analyze_tline_intraday(df[df["tf"] == "15M"], ticker, "15M")
    tf_60 = analyze_tline_intraday(df[df["tf"] == "60M"], ticker, "60M")
    tf_d  = analyze_tline_intraday(df[df["tf"] == "Daily"], ticker, "Daily")

    return {
        "15M": tf_15,
        "60M": tf_60,
        "Daily": tf_d,
        "confluence": compare_timeframes(tf_15, tf_60, tf_d)
    }
    
def compare_timeframes(tf15, tf60, tfd):

    def extract_state(text):
        if "Bullish Trend" in text:
            return "BULL"
        if "Bearish Trend" in text:
            return "BEAR"
        return "NEUTRAL"

    s15 = extract_state(tf15)
    s60 = extract_state(tf60)
    sd  = extract_state(tfd)

    conflicts = []
    alignment_score = len([x for x in [s15, s60, sd] if x == s60]) / 3
    
    if s15 != s60:
        conflicts.append("15M vs 60M conflict")

    if s60 != sd:
        conflicts.append("60M vs Daily conflict")

    if s15 == "BULL" and sd == "BEAR":
        conflicts.append("STRONG MULTI-TF DIVERGENCE (15M vs DAILY)")

    if s15 == s60 == sd:
        conflicts.append("FULL ALIGNMENT")

    return {
        "15M_state": s15,
        "60M_state": s60,
        "Daily_state": sd,
        "alignment_score": round(alignment_score, 2),
        "conflicts": conflicts
    }    