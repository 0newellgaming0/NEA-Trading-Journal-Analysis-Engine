# ==========================================================
# MULTI-TIMEFRAME CANDLESTICK ANALYSIS ENGINE (FULL FIXED + EXPANDED)
# ==========================================================

import pandas as pd
import numpy as np
import logging

__all__ = [
    "analyze_multitimeframe_candlesticks",
    "analyze_single_timeframe",
    "format_candlestick_for_journal"
]

# ==========================================================
# LOGGER
# ==========================================================

logger = logging.getLogger("candlestickAnalysis")

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[CANDLESTICK_ANALYSIS] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ==========================================================
# SAFE FLOAT
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


# ==========================================================
# COLUMN NORMALIZATION
# ==========================================================

def force_flat_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(map(str, c)).strip().lower() for c in df.columns]
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

# ==========================================================
# OHLCV NORMALIZER (SELF-CONTAINED - NO EXTERNAL DEPENDENCIES)
# ==========================================================

def normalize_candlestick_ohlcv(df, ticker=None):
    df = df.copy().reset_index(drop=True)

    t = ticker.lower() if ticker else ""

    def pick(col_options):
        for c in col_options:
            if c in df.columns:
                return pd.to_numeric(df[c], errors="coerce")
        return pd.Series(np.nan, index=df.index)

    df["open"] = pick([f"open_{t}", "open", "Open"])
    df["high"] = pick([f"high_{t}", "high", "High"])
    df["low"] = pick([f"low_{t}", "low", "Low"])
    df["close"] = pick([f"close_{t}", "close", "Close"])
    df["volume"] = pick([f"volume_{t}", "volume", "Volume"])

    return df

# ==========================================================
# CANDLE STRUCTURE
# ==========================================================

def candle_structure(open_, high, low, close):

    body = (close - open_).abs()

    rng = (high - low).astype(float)
    rng = rng.mask(rng == 0, np.nan)

    upper_shadow = high - pd.concat([open_, close], axis=1).max(axis=1)
    lower_shadow = pd.concat([open_, close], axis=1).min(axis=1) - low

    return {
        "Body": body,
        "Range": rng,
        "BodyRatio": body / rng,
        "UpperShadow": upper_shadow,
        "LowerShadow": lower_shadow
    }

# ==========================================================
# SINGLE CANDLE PATTERNS (FIXED + SAFE + NON-CONFLICTING)
# ==========================================================

def detect_single_patterns(df):

    pattern = pd.Series(None, index=df.index, dtype="object")

    for i in range(len(df)):

        r = df.iloc[i]

        o = f(r["open"])
        c = f(r["close"])
        body = f(r["Body"])
        rng = f(r["Range"])
        upper = f(r["UpperShadow"])
        lower = f(r["LowerShadow"])
        br = f(r["BodyRatio"])

        if pd.isna(o) or pd.isna(c) or pd.isna(rng) or rng == 0:
            continue

        # ---------------- MARUBOZU ----------------
        if pd.notna(br) and br >= 0.85:
            pattern.iloc[i] = "Bullish Marubozu" if c > o else "Bearish Marubozu"
            continue

        # ---------------- DOJI FIRST (highest priority indecision) ----------------
        if pd.notna(br) and br <= 0.08:
            pattern.iloc[i] = "Doji"
            continue

        # ---------------- HAMMER / HANGING MAN ----------------
        if rng > 0 and body <= rng * 0.3 and lower >= body * 2 and upper <= body * 1.5:
            pattern.iloc[i] = "Hammer" if c > o else "Hanging Man"
            continue

        # ---------------- INVERTED HAMMER / SHOOTING STAR ----------------
        if rng > 0 and body <= rng * 0.3 and upper >= body * 2 and lower <= body * 1.5:
            pattern.iloc[i] = "Inverted Hammer" if c > o else "Shooting Star"
            continue

        # ---------------- SPINNING / UNCERTAINTY ----------------
        if pd.notna(br) and br <= 0.25:
            pattern.iloc[i] = "Spinning Top"

    return pattern


# ==========================================================
# TWO CANDLE PATTERNS (FIXED PRIORITY + CLEAN LOGIC)
# ==========================================================

def detect_two_candle_patterns(df):

    pattern = pd.Series(None, index=df.index, dtype="object")

    for i in range(1, len(df)):

        p = df.iloc[i - 1]
        c = df.iloc[i]

        po, pc = f(p["open"]), f(p["close"])
        co, cc = f(c["open"]), f(c["close"])

        if any(pd.isna(x) for x in [po, pc, co, cc]):
            continue

        # ---------------- ENGULFING (HIGHEST PRIORITY) ----------------
        if pc < po and cc > co and co < pc and cc > po:
            pattern.iloc[i] = "Bullish Engulfing"
            continue

        if pc > po and cc < co and co > pc and cc < po:
            pattern.iloc[i] = "Bearish Engulfing"
            continue

        # ---------------- MIDPOINT REVERSALS ----------------
        if pc < po and cc > co and cc > (po + pc) / 2:
            pattern.iloc[i] = "Piercing Line"
            continue

        if pc > po and cc < co and cc < (po + pc) / 2:
            pattern.iloc[i] = "Dark Cloud Cover"
            continue

    return pattern


# ==========================================================
# THREE CANDLE PATTERNS (FIXED STRUCTURE + NO OVERLAP ISSUES)
# ==========================================================

def detect_three_candle_patterns(df):

    pattern = pd.Series(None, index=df.index, dtype="object")

    for i in range(2, len(df)):

        f1 = df.iloc[i - 2]
        f2 = df.iloc[i - 1]
        f3 = df.iloc[i]

        fo, fc = f(f1["open"]), f(f1["close"])
        mo, mc = f(f2["open"]), f(f2["close"])
        to, tc = f(f3["open"]), f(f3["close"])

        if any(pd.isna(x) for x in [fo, fc, mo, mc, to, tc]):
            continue

        mid = (fo + fc) / 2
        middle_body = abs(mc - mo)
        middle_range = max(f(f2["high"]) - f(f2["low"]), 1e-9)

        # ---------------- MORNING STAR ----------------
        if fc < fo and middle_body / middle_range <= 0.3 and tc > to and tc > mid:
            pattern.iloc[i] = "Morning Star"
            continue

        # ---------------- EVENING STAR ----------------
        if fc > fo and middle_body / middle_range <= 0.3 and tc < to and tc < mid:
            pattern.iloc[i] = "Evening Star"
            continue

    return pattern

# ==========================================================
# ADVANCED PATTERNS (FIXED - STRONG vs WEAK vs NOISE TAGGING + CONTEXT SENSITIVITY)
# ==========================================================

def detect_advanced_patterns(df):

    pattern = pd.Series(None, index=df.index, dtype="object")

    for i in range(4, len(df)):

        c0 = df.iloc[i]
        c1 = df.iloc[i - 1]
        c2 = df.iloc[i - 2]

        o = f(c0["open"])
        h = f(c0["high"])
        l = f(c0["low"])
        c = f(c0["close"])

        body = f(c0["Body"])
        br = f(c0["BodyRatio"])

        prev_o = f(c1["open"])
        prev_c = f(c1["close"])
        prev_h = f(c1["high"])
        prev_l = f(c1["low"])

        prev2_o = f(c2["open"])
        prev2_c = f(c2["close"])
        prev2_h = f(c2["high"])
        prev2_l = f(c2["low"])

        prev3_o = f(df.iloc[i - 3]["open"])
        prev3_c = f(df.iloc[i - 3]["close"])
        prev3_h = f(df.iloc[i - 3]["high"])
        prev3_l = f(df.iloc[i - 3]["low"])

        # --------------------------------------------------
        # SAFETY
        # --------------------------------------------------

        values = [
            o, h, l, c,
            body, br,
            prev_o, prev_c, prev_h, prev_l,
            prev2_o, prev2_c, prev2_h, prev2_l,
            prev3_o, prev3_c, prev3_h, prev3_l
        ]

        if any(pd.isna(v) for v in values):
            continue

        prev_bull = prev_c > prev_o
        prev_bear = prev_c < prev_o

        prev2_bull = prev2_c > prev2_o
        prev2_bear = prev2_c < prev2_o

        prev3_bull = prev3_c > prev3_o
        prev3_bear = prev3_c < prev3_o

        prev_body_high = max(prev_o, prev_c)
        prev_body_low = min(prev_o, prev_c)

        curr_body_high = max(o, c)
        curr_body_low = min(o, c)

        curr_range = max(h - l, 1e-9)
        middle_range = max(prev_h - prev_l, 1e-9)

        detected = None
        context_tag = "Noise"
        strength_tag = "Noise"

        # ==================================================
        # STRICT DOJI / SINGLE CANDLE STRUCTURES
        # ==================================================

        if br <= 0.05:

            if h == l == o == c:
                detected = "Four Price Doji"
                context_tag = "Weak Structure"
                strength_tag = "Weak Structure"

            elif curr_range > 3 * max(body, 1e-9):
                detected = "Rickshaw Man"
                context_tag = "Weak Structure"
                strength_tag = "Weak Structure"

            elif (h - max(o, c)) > (min(o, c) - l):
                detected = "Gravestone Doji"
                context_tag = "Weak Structure"
                strength_tag = "Weak Structure"

            else:
                detected = "Dragonfly Doji"
                context_tag = "Weak Structure"
                strength_tag = "Weak Structure"

        elif br <= 0.10:
            detected = "Doji"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        elif br <= 0.20 and curr_range > 3 * max(body, 1e-9):
            detected = "High Wave Candle"
            context_tag = "Noise"
            strength_tag = "Weak Structure"

        elif br <= 0.30:
            detected = "Spinning Top"
            context_tag = "Noise"
            strength_tag = "Weak Structure"

        # ==================================================
        # 3-CANDLE REVERSALS (STRONG ONLY WHEN CONTEXT MATCHES)
        # ==================================================

        if (
            prev2_bear and
            abs(prev2_c - prev2_o) >= (prev2_h - prev2_l) * 0.50 and
            abs(prev_c - prev_o) <= (prev_h - prev_l) * 0.10 and
            c > o and
            c > ((prev2_o + prev2_c) / 2)
        ):
            detected = "Morning Doji Star"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev2_bull and
            abs(prev2_c - prev2_o) >= (prev2_h - prev2_l) * 0.50 and
            abs(prev_c - prev_o) <= (prev_h - prev_l) * 0.10 and
            c < o and
            c < ((prev2_o + prev2_c) / 2)
        ):
            detected = "Evening Doji Star"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev2_bear and
            abs(prev2_c - prev2_o) >= (prev2_h - prev2_l) * 0.50 and
            abs(prev_c - prev_o) <= (prev_h - prev_l) * 0.50 and
            c > o and
            c > ((prev2_o + prev2_c) / 2)
        ):
            detected = "Morning Star"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev2_bull and
            abs(prev2_c - prev2_o) >= (prev2_h - prev2_l) * 0.50 and
            abs(prev_c - prev_o) <= (prev_h - prev_l) * 0.50 and
            c < o and
            c < ((prev2_o + prev2_c) / 2)
        ):
            detected = "Evening Star"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # 2-CANDLE ENGULFING (STRUCTURE DEPENDENT)
        # ==================================================

        elif (
            prev_bear and
            c > o and
            curr_body_low <= prev_body_low and
            curr_body_high >= prev_body_high
        ):
            detected = "Bullish Engulfing"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev_bull and
            c < o and
            curr_body_low <= prev_body_low and
            curr_body_high >= prev_body_high
        ):
            detected = "Bearish Engulfing"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # HARAMI (WEAK STRUCTURE BY NATURE)
        # ==================================================

        elif (
            prev_bear and
            c > o and
            curr_body_high <= prev_body_high and
            curr_body_low >= prev_body_low
        ):
            detected = "Bullish Harami"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        elif (
            prev_bull and
            c < o and
            curr_body_high <= prev_body_high and
            curr_body_low >= prev_body_low
        ):
            detected = "Bearish Harami"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        elif (
            prev_bear and
            br <= 0.10 and
            curr_body_high <= prev_body_high and
            curr_body_low >= prev_body_low
        ):
            detected = "Bullish Harami Cross"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        elif (
            prev_bull and
            br <= 0.10 and
            curr_body_high <= prev_body_high and
            curr_body_low >= prev_body_low
        ):
            detected = "Bearish Harami Cross"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        # ==================================================
        # TWEEZERS (NOISE FILTERED UNLESS STRUCTURAL EXTREME)
        # ==================================================

        elif body > 0 and abs(h - prev_h) <= max(body * 0.10, 0.01):
            detected = "Tweezer Top"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        elif body > 0 and abs(l - prev_l) <= max(body * 0.10, 0.01):
            detected = "Tweezer Bottom"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        # ==================================================
        # THREE SOLDIERS / THREE CROWS (STRONG CONTINUATION ONLY)
        # ==================================================

        elif (
            prev2_bull and
            prev_bull and
            c > o and
            prev2_c > prev2_o and
            prev_c > prev_o and
            c > prev_c and
            prev_c > prev2_c
        ):
            detected = "Three White Soldiers"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev2_bear and
            prev_bear and
            c < o and
            prev2_c < prev2_o and
            prev_c < prev_o and
            c < prev_c and
            prev_c < prev2_c
        ):
            detected = "Three Black Crows"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # GAPS (STRUCTURAL ONLY)
        # ==================================================

        elif l > prev_h:
            detected = "Rising Window"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif h < prev_l:
            detected = "Falling Window"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # BELT HOLD (NOISE FILTERED)
        # ==================================================

        elif (
            br > 0.65 and
            (prev_bull or prev_bear) and
            body >= curr_range * 0.70
        ):

            if (
                abs(o - l) <= max(body * 0.15, 0.01) and
                c > o and
                prev_bear
            ):
                detected = "Bullish Belt Hold"
                context_tag = "Strong Reversal"
                strength_tag = "Strong Reversal"

            elif (
                abs(o - h) <= max(body * 0.15, 0.01) and
                c < o and
                prev_bull
            ):
                detected = "Bearish Belt Hold"
                context_tag = "Strong Reversal"
                strength_tag = "Strong Reversal"

        # ==================================================
        # THREE METHODS (TREND CONTINUATION ONLY)
        # ==================================================

        elif (
            prev3_bull and
            prev2_bear and
            prev_bear and
            c > o and
            c > prev3_c
        ):
            detected = "Rising Three Methods"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev3_bear and
            prev2_bull and
            prev_bull and
            c < o and
            c < prev3_c
        ):
            detected = "Falling Three Methods"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # SEPARATING LINES (STRUCTURAL ONLY)
        # ==================================================

        elif (
            prev_bear and
            c > o and
            abs(o - prev_c) <= middle_range * 0.15 and
            c > prev_h and
            prev_h - prev_l > middle_range * 0.8
        ):
            detected = "Separating Lines"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev_bull and
            c < o and
            abs(o - prev_c) <= middle_range * 0.15 and
            c < prev_l and
            prev_h - prev_l > middle_range * 0.8
        ):
            detected = "Separating Lines"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # THREE OUTSIDE (STRUCTURAL)
        # ==================================================

        elif (
            prev2_bear and
            prev_bull and
            prev_body_high >= max(prev2_o, prev2_c) and
            prev_body_low <= min(prev2_o, prev2_c) and
            c > prev_c
        ):
            detected = "Three Outside Up"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev2_bull and
            prev_bear and
            prev_body_high >= max(prev2_o, prev2_c) and
            prev_body_low <= min(prev2_o, prev2_c) and
            c < prev_c
        ):
            detected = "Three Outside Down"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # THREE INSIDE (WEAK STRUCTURE)
        # ==================================================

        elif (
            prev2_bear and
            prev_bull and
            max(prev_o, prev_c) <= max(prev2_o, prev2_c) and
            min(prev_o, prev_c) >= min(prev2_o, prev2_c) and
            c > prev_c
        ):
            detected = "Three Inside Up"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        elif (
            prev2_bull and
            prev_bear and
            max(prev_o, prev_c) <= max(prev2_o, prev2_c) and
            min(prev_o, prev_c) >= min(prev2_o, prev2_c) and
            c < prev_c
        ):
            detected = "Three Inside Down"
            context_tag = "Weak Structure"
            strength_tag = "Weak Structure"

        # ==================================================
        # COUNTERATTACK LINES (NOISE CLASSIFIED)
        # ==================================================

        elif (
            prev_bear and
            c > o and
            abs(c - prev_c) <= curr_range * 0.25 and
            c >= (prev_o + prev_c) / 2
        ):
            detected = "Bullish Counterattack"
            context_tag = "Noise"
            strength_tag = "Noise"

        elif (
            prev_bull and
            c < o and
            abs(c - prev_c) <= curr_range * 0.25 and
            c <= (prev_o + prev_c) / 2
        ):
            detected = "Bearish Counterattack"
            context_tag = "Noise"
            strength_tag = "Noise"

        # ==================================================
        # BREAKAWAY GAP
        # ==================================================

        elif (
            prev3_bull and
            prev2_bull and
            prev_bull and
            l > prev_h
        ):
            detected = "Breakaway Gap"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev3_bear and
            prev2_bear and
            prev_bear and
            h < prev_l
        ):
            detected = "Breakaway Gap"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # EXHAUSTION GAP
        # ==================================================

        elif (
            prev_bull and
            prev2_bull and
            l > prev_h and
            c < h
        ):
            detected = "Exhaustion Gap"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev_bear and
            prev2_bear and
            h < prev_l and
            c > l
        ):
            detected = "Exhaustion Gap"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # ABANDONED BABY (STRONG REVERSAL ONLY)
        # ==================================================

        elif (
            prev2_bear and
            abs(prev_c - prev_o) <= (prev_h - prev_l) * 0.10 and
            prev_l > prev2_h and
            c > o and
            l > prev_h
        ):
            detected = "Abandoned Baby"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        elif (
            prev2_bull and
            abs(prev_c - prev_o) <= (prev_h - prev_l) * 0.10 and
            prev_h < prev2_l and
            c < o and
            h < prev_l
        ):
            detected = "Abandoned Baby"
            context_tag = "Strong Reversal"
            strength_tag = "Strong Reversal"

        # ==================================================
        # DELIBERATION (NOISE SUPPRESSION)
        # ==================================================

        elif (
            br <= 0.25 and
            curr_range < middle_range * 0.75 and
            body < middle_range * 0.25 and
            not (prev_bull and c > o and curr_range > middle_range * 1.5) and
            not (prev_bear and c < o and curr_range > middle_range * 1.5)
        ):
            detected = "Deliberation Pattern"
            context_tag = "Noise"
            strength_tag = "Noise"

        pattern.iloc[i] = detected

    return pattern

# ==========================================================
# INTERPRETATION ENGINE (UNCHANGED)
# ==========================================================

def interpret_pattern(pattern):

    mapping = {
        "Hammer": "Small body with long lower wick after downtrend.",
        "Inverted Hammer": "Long upper wick after downtrend.",
        "Bullish Engulfing": "Bullish candle fully engulfs prior bearish candle.",
        "Piercing Line": "Bullish close above midpoint of prior bearish candle.",
        "Morning Star": "Three-candle bullish reversal.",
        "Morning Doji Star": "Morning star with Doji center candle.",
        "Three White Soldiers": "Three strong bullish candles.",
        "Dragonfly Doji": "Long lower shadow rejection.",
        "Bullish Harami": "Small bullish candle inside bearish candle.",
        "Bullish Harami Cross": "Doji inside bearish candle.",
        "Tweezer Bottom": "Two candles with matching lows.",
        "Shooting Star": "Long upper wick after uptrend.",
        "Hanging Man": "Bearish reversal at top.",
        "Bearish Engulfing": "Bearish engulfing structure.",
        "Dark Cloud Cover": "Bearish close below midpoint.",
        "Evening Star": "Three-candle bearish reversal.",
        "Evening Doji Star": "Evening star with Doji middle.",
        "Three Black Crows": "Three strong bearish candles.",
        "Gravestone Doji": "Long upper shadow rejection.",
        "Bearish Harami": "Bearish small body inside bullish candle.",
        "Bearish Harami Cross": "Doji inside bullish candle.",
        "Tweezer Top": "Matching highs rejection.",
        "Deliberation Pattern": "Momentum exhaustion.",
        "Doji": "Open and close nearly equal.",
        "Spinning Top": "Small body with wicks.",
        "High Wave Candle": "Extreme volatility.",
        "Rickshaw Man": "Full indecision structure.",
        "Four Price Doji": "All prices equal.",
        "Rising Window": "Bullish gap.",
        "Falling Window": "Bearish gap.",
        "Side-by-Side White Lines": "Bullish continuation.",
        "Separating Lines": "Trend continuation.",
        "Thrusting Pattern": "Partial continuation.",
        "Ladder Bottom": "Multi-candle bullish recovery.",
        # CONTINUATION
        "Rising Three Methods": "Bullish continuation after consolidation.",
        "Falling Three Methods": "Bearish continuation after consolidation.",
        "Separating Lines": "Strong gap continuation in trend direction.",

        # STRUCTURE
        "Three Inside Up": "Bullish reversal after inside consolidation.",
        "Three Inside Down": "Bearish reversal after inside consolidation.",
        "Three Outside Up": "Strong bullish engulf continuation.",
        "Three Outside Down": "Strong bearish engulf continuation.",

        # EDGE CASES
        "Abandoned Baby": "High-probability gap reversal.",
        "Belt Hold": "Strong directional opening candle.",
        "Counterattack Lines": "Rejection of prior close equilibrium.",

        # GAPS
        "Breakaway Gap": "Structural trend initiation gap.",
        "Exhaustion Gap": "Final push before reversal.",

        "Rising Window": "Bullish gap continuation.",
        "Falling Window": "Bearish gap continuation.",
        "Bullish Belt Hold": "Strong bullish opening drive with rejection of lower prices.",
        "Bearish Belt Hold": "Strong bearish opening drive with rejection of higher prices.",        

        "Deliberation Pattern": "Market exhaustion / hesitation phase."        
    }

    return mapping.get(pattern, "No interpretation available.")


# ==========================================================
# ✅ NEW: ACTIONABLE PATTERN ENGINE
# ==========================================================
def actionable_pattern(pattern):

    if not pattern or pd.isna(pattern):
        return "No actionable setup identified."

    key = str(pattern).strip()  # 🔥 FIX 1: normalize whitespace

    actions = {
        "Hammer": "Bullish reversal setup. Wait for confirmation break above candle high before entry. Stop below wick low.",
        "Inverted Hammer": "Potential reversal. Require bullish confirmation candle before entry.",
        "Bullish Engulfing": "Momentum long setup. Entry on continuation or break of engulf high.",
        "Piercing Line": "Bullish reversal signal. Consider long if follow-through confirms strength.",
        "Morning Star": "Strong reversal pattern. Favor long entries on confirmation close.",
        "Morning Doji Star": "High-quality reversal. Wait for breakout confirmation before scaling in.",
        "Three White Soldiers": "Strong bullish trend continuation. Hold longs; avoid early exits.",
        "Dragonfly Doji": "Reversal warning. Watch for bullish confirmation before entry.",
        "Bullish Harami": "Consolidation. Wait for breakout direction confirmation.",
        "Bullish Harami Cross": "Indecision. No trade until expansion candle appears.",
        "Tweezer Bottom": "Support confirmation. Long bias on breakout confirmation.",
        "Shooting Star": "Bearish reversal signal. Consider exit longs or short on confirmation.",
        "Hanging Man": "Distribution warning. Tighten stops or reduce exposure.",
        "Bearish Engulfing": "Short setup. Enter on breakdown continuation.",
        "Dark Cloud Cover": "Bearish continuation. Look for downside follow-through.",
        "Evening Star": "Strong bearish reversal. Favor shorts after confirmation.",
        "Evening Doji Star": "High-probability reversal. Wait for breakdown confirmation.",
        "Three Black Crows": "Strong bearish trend. Hold shorts; avoid countertrend longs.",
        "Gravestone Doji": "Top rejection. Prepare for downside reversal.",
        "Bearish Harami": "Weakness building. Watch for breakdown confirmation.",
        "Bearish Harami Cross": "Indecision with bearish bias. Wait for confirmation.",
        "Tweezer Top": "Resistance rejection. Short bias on breakdown.",
        "Doji": "Indecision. Stand aside.",
        "Spinning Top": "Market uncertainty. Wait for directional expansion.",
        "High Wave Candle": "Volatility expansion. Reduce size or avoid entries.",
        "Rickshaw Man": "No-trade zone. Extreme indecision.",
        "Four Price Doji": "Market frozen. No actionable edge.",
        "Rising Window": "Bullish gap. Continuation long bias.",
        "Falling Window": "Bearish gap. Continuation short bias.",
        # CONTINUATION ADDITIONS
        "Rising Three Methods": "Continuation long. Enter on breakout continuation.",
        "Falling Three Methods": "Continuation short. Enter on breakdown continuation.",
        "Separating Lines": "Trend continuation in open direction.",

        # EDGE STRUCTURE
        "Abandoned Baby": "High probability reversal. Wait for confirmation break.",
        "Belt Hold": "Directional strength candle. Trade in open direction with confirmation.",
        "Counterattack Lines": "Rejection of equilibrium. Wait for directional break.",

        # GAP STRUCTURE
        "Breakaway Gap": "Trend initiation. Trade in gap direction.",
        "Exhaustion Gap": "Reversal risk. Prepare to fade continuation.",

        # STRUCTURAL PATTERNS
        "Three Inside Up": "Bullish reversal. Enter on breakout confirmation.",
        "Three Inside Down": "Bearish reversal. Enter on breakdown confirmation.",
        "Three Outside Up": "Strong bullish expansion. Hold longs.",
        "Three Outside Down": "Strong bearish expansion. Hold shorts.",
        "Bullish Belt Hold": "Strong bullish continuation or reversal signal. Consider momentum entry on confirmation.",
        "Bearish Belt Hold": "Strong bearish continuation or breakdown signal. Consider short continuation entries.",        

        "Deliberation Pattern": "No trade. Market exhaustion phase."        
    }

    return actions.get(key, "No actionable setup identified.")

# ==========================================================
# TRADE SETUP ENGINE (NEW LAYER)
# ==========================================================

def build_trade_setup(pattern, direction, df=None, i=-1):

    if not pattern or pattern == "No Pattern":
        return {
            "bias": "NEUTRAL",
            "entry": "No setup",
            "stop": "N/A",
            "target": "N/A",
            "context": "No pattern detected",
            "entry_price_hint": np.nan,
            "stop_price_hint": np.nan,
            "structure_high": np.nan,
            "structure_low": np.nan
        }

    key = str(pattern).strip()

    # fallback safety
    high = low = close = np.nan

    if df is not None and len(df) > 0:

        if i < 0:
            i = len(df) - 1

        if 0 <= i < len(df):
            row = df.iloc[i]

            high = f(row["high"])
            low = f(row["low"])
            close = f(row["close"])

    setups = {

        # ================= BULLISH REVERSALS =================
        "Hammer": {
            "bias": "LONG",
            "entry": "Break above candle high",
            "stop": "Below wick low",
            "target": "1.5R to 3R extension",
            "context": "Reversal after sell pressure exhaustion"
        },

        "Bullish Engulfing": {
            "bias": "LONG",
            "entry": "Break above engulf high or close confirmation",
            "stop": "Below engulf low",
            "target": "Trend continuation / prior swing high",
            "context": "Momentum shift / liquidity grab reversal"
        },

        "Morning Star": {
            "bias": "LONG",
            "entry": "Break above 3rd candle high",
            "stop": "Below star low",
            "target": "Prior resistance / structure high",
            "context": "Wyckoff spring-style reversal structure"
        },

        "Morning Doji Star": {
            "bias": "LONG",
            "entry": "Break above confirmation candle high",
            "stop": "Below doji low",
            "target": "Prior resistance / trend reversal",
            "context": "High-quality bullish reversal structure"
        },

        "Dragonfly Doji": {
            "bias": "LONG",
            "entry": "Confirmation candle above high",
            "stop": "Below rejection wick",
            "target": "Range midpoint or breakout continuation",
            "context": "Liquidity sweep + rejection"
        },

        # ================= BEARISH REVERSALS =================
        "Shooting Star": {
            "bias": "SHORT",
            "entry": "Break below candle low",
            "stop": "Above wick high",
            "target": "Support / prior liquidity zone",
            "context": "Exhaustion at resistance"
        },

        "Bearish Engulfing": {
            "bias": "SHORT",
            "entry": "Break below engulf low",
            "stop": "Above engulf high",
            "target": "Downtrend continuation / liquidity gap",
            "context": "Distribution signal"
        },

        "Evening Star": {
            "bias": "SHORT",
            "entry": "Break below 3rd candle low",
            "stop": "Above star high",
            "target": "Prior support / breakdown extension",
            "context": "Wyckoff distribution / top formation"
        },

        "Evening Doji Star": {
            "bias": "SHORT",
            "entry": "Break below confirmation candle low",
            "stop": "Above doji high",
            "target": "Prior support / trend reversal",
            "context": "High-quality bearish reversal structure"
        },

        "Gravestone Doji": {
            "bias": "SHORT",
            "entry": "Break below candle low",
            "stop": "Above rejection high",
            "target": "Range low / liquidity sweep",
            "context": "Rejection of highs"
        },

        "Hanging Man": {
            "bias": "SHORT",
            "entry": "Break below candle low",
            "stop": "Above candle high",
            "target": "Support / downside continuation",
            "context": "Distribution warning after advance"
        },

        # ================= CONTINUATION =================
        "Three White Soldiers": {
            "bias": "LONG",
            "entry": "Pullback continuation or breakout",
            "stop": "Below last soldier low",
            "target": "Trend extension",
            "context": "Strong institutional accumulation"
        },

        "Three Black Crows": {
            "bias": "SHORT",
            "entry": "Pullback continuation or breakdown",
            "stop": "Above last crow high",
            "target": "Trend extension",
            "context": "Institutional distribution"
        },

        "Rising Window": {
            "bias": "LONG",
            "entry": "Retest of gap or breakout continuation",
            "stop": "Below gap low",
            "target": "Trend continuation",
            "context": "Imbalance / liquidity gap"
        },

        "Falling Window": {
            "bias": "SHORT",
            "entry": "Retest rejection or continuation breakdown",
            "stop": "Above gap high",
            "target": "Downtrend continuation",
            "context": "Bearish imbalance"
        },

        "Piercing Line": {
            "bias": "LONG",
            "entry": "Break above second candle high or close above confirmation level",
            "stop": "Below first candle low",
            "target": "Prior resistance / midpoint expansion",
            "context": "Bullish reversal after bearish pressure exhaustion"
        },

        "Dark Cloud Cover": {
            "bias": "SHORT",
            "entry": "Break below second candle low or bearish close confirmation",
            "stop": "Above first candle high",
            "target": "Prior support / continuation lower",
            "context": "Bearish reversal after bullish exhaustion"
        },

        "Bullish Harami": {
            "bias": "LONG",
            "entry": "Break above mother candle high",
            "stop": "Below mother candle low",
            "target": "Range expansion upward",
            "context": "Consolidation before bullish breakout"
        },

        "Bullish Harami Cross": {
            "bias": "LONG",
            "entry": "Break above mother candle high",
            "stop": "Below mother candle low",
            "target": "Range expansion upward",
            "context": "Bullish harami doji structure"
        },

        "Bearish Harami": {
            "bias": "SHORT",
            "entry": "Break below mother candle low",
            "stop": "Above mother candle high",
            "target": "Range expansion downward",
            "context": "Consolidation before bearish breakdown"
        },

        "Bearish Harami Cross": {
            "bias": "SHORT",
            "entry": "Break below mother candle low",
            "stop": "Above mother candle high",
            "target": "Range expansion downward",
            "context": "Bearish harami doji structure"
        },

        "Tweezer Top": {
            "bias": "SHORT",
            "entry": "Break below confirmation candle low",
            "stop": "Above twin highs",
            "target": "Support zone / liquidity sweep",
            "context": "Double rejection at resistance"
        },

        "Tweezer Bottom": {
            "bias": "LONG",
            "entry": "Break above confirmation candle high",
            "stop": "Below twin lows",
            "target": "Resistance / liquidity expansion",
            "context": "Double rejection at support"
        },

        "Doji": {
            "bias": "NEUTRAL",
            "entry": "No trade - wait for confirmation candle",
            "stop": "N/A",
            "target": "N/A",
            "context": "Indecision candle - requires expansion"
        },

        "Spinning Top": {
            "bias": "NEUTRAL",
            "entry": "Wait for breakout of range high/low",
            "stop": "Opposite side of breakout",
            "target": "Trend continuation once resolved",
            "context": "Market indecision / equilibrium"
        },

        "High Wave Candle": {
            "bias": "NEUTRAL",
            "entry": "Wait for directional confirmation",
            "stop": "Outside volatility range",
            "target": "Trend continuation after expansion",
            "context": "Volatility spike / liquidity instability"
        },

        "Rickshaw Man": {
            "bias": "NEUTRAL",
            "entry": "No trade",
            "stop": "N/A",
            "target": "N/A",
            "context": "Extreme indecision - market equilibrium"
        },

        "Four Price Doji": {
            "bias": "NEUTRAL",
            "entry": "No trade",
            "stop": "N/A",
            "target": "N/A",
            "context": "Market frozen - no liquidity movement"
        },

        # ==================================================
        # CONTINUATION PATTERNS (INSTITUTIONAL FLOW)
        # ==================================================

        "Rising Three Methods": {
            "bias": "LONG",
            "entry": "Break above final candle high",
            "stop": "Below pattern low",
            "target": "Trend continuation extension",
            "context": "Bullish continuation with consolidation pullback"
        },

        "Falling Three Methods": {
            "bias": "SHORT",
            "entry": "Break below final candle low",
            "stop": "Above pattern high",
            "target": "Trend continuation extension",
            "context": "Bearish continuation with consolidation pullback"
        },

        "Separating Lines": {
            "bias": "CONTINUATION",
            "entry": "Follow direction of strong same-direction open",
            "stop": "Opposite candle extreme",
            "target": "Trend continuation",
            "context": "Gap-open continuation of dominant trend"
        },

        # ==================================================
        # EDGE CASE REVERSALS
        # ==================================================

        "Abandoned Baby": {
            "bias": "REVERSAL (HIGH CONFIDENCE)",
            "entry": "Break opposite direction of gap candle",
            "stop": "Beyond isolated candle extreme",
            "target": "Strong reversal / liquidity vacuum fill",
            "context": "Rare exhaustion + gap isolation reversal"
        },

        "Bullish Belt Hold": {
            "bias": "LONG",
            "entry": "Break continuation in candle direction",
            "stop": "Below candle low",
            "target": "Trend continuation",
            "context": "Strong bullish opening drive"
        },

        "Bearish Belt Hold": {
            "bias": "SHORT",
            "entry": "Break continuation in candle direction",
            "stop": "Above candle high",
            "target": "Trend continuation",
            "context": "Strong bearish opening drive"
        },

        "Counterattack Lines": {
            "bias": "REVERSAL SIGNAL",
            "entry": "Break confirmation above/below equal close zone",
            "stop": "Opposite candle extreme",
            "target": "Mean reversion / prior structure",
            "context": "Price rejection of prior close level"
        },

        # ==================================================
        # GAP STRUCTURE DIFFERENTIATION
        # ==================================================

        "Breakaway Gap": {
            "bias": "EXPANSION / TREND START",
            "entry": "Continuation in gap direction",
            "stop": "Fill of gap invalidation",
            "target": "Trend leg expansion",
            "context": "Structural break initiating trend phase"
        },

        # ==================================================
        # EXHAUSTION PATTERNS
        # ==================================================

        "Exhaustion Gap": {
            "bias": "REVERSAL WARNING",
            "entry": "Fade gap after failure to continue",
            "stop": "Beyond gap extreme",
            "target": "Gap fill / reversal leg",
            "context": "Final liquidity push before reversal"
        },

        # ==================================================
        # THREE-CANDLE INSTITUTIONAL STRUCTURES
        # ==================================================

        "Three Inside Up": {
            "bias": "LONG",
            "entry": "Break above 3rd candle high",
            "stop": "Below pattern low",
            "target": "Trend reversal continuation",
            "context": "Bullish confirmation after inside structure"
        },

        "Three Inside Down": {
            "bias": "SHORT",
            "entry": "Break below 3rd candle low",
            "stop": "Above pattern high",
            "target": "Trend reversal continuation",
            "context": "Bearish confirmation after inside structure"
        },

        "Three Outside Up": {
            "bias": "LONG",
            "entry": "Break above engulf high",
            "stop": "Below engulf low",
            "target": "Trend expansion",
            "context": "Strong bullish outside reversal structure"
        },

        "Three Outside Down": {
            "bias": "SHORT",
            "entry": "Break below engulf low",
            "stop": "Above engulf high",
            "target": "Trend expansion",
            "context": "Strong bearish outside reversal structure"
        },

        # ==================================================
        # DELIBERATION (INTERPRET ONLY — NOT TRADE-ACTIVE)
        # ==================================================

        "Deliberation Pattern": {
            "bias": "NEUTRAL",
            "entry": "No trade - requires breakout confirmation",
            "stop": "N/A",
            "target": "N/A",
            "context": "Exhaustion / hesitation near trend end - interpret only"
        }
    }

    setup = setups.get(key)

    if not setup:
        return {
            "bias": "NEUTRAL",
            "entry": "No structured setup",
            "stop": "N/A",
            "target": "N/A",
            "context": "No institutional edge defined",
            "entry_price_hint": close,
            "stop_price_hint": np.nan,
            "structure_high": high,
            "structure_low": low
        }

    setup = setup.copy()

    setup["reference_high"] = high
    setup["reference_low"] = low
    setup["reference_close"] = close

    # ======================================================
    # JOURNAL PRICE PACK (NEW)
    # ======================================================

    setup["entry_price_hint"] = close

    if setup["bias"] == "LONG":
        setup["stop_price_hint"] = low
    elif setup["bias"] == "SHORT":
        setup["stop_price_hint"] = high
    else:
        setup["stop_price_hint"] = np.nan

    setup["structure_high"] = high
    setup["structure_low"] = low

    return setup

# ==========================================================
# VOLUME CONFIRMATION (FIXED - VOLUME REGIME CLASSIFICATION + SIGNAL VALIDITY GATE)
# ==========================================================

def volume_confirmation(volume, patterns):

    try:

        volume = pd.to_numeric(volume, errors="coerce")

        confirmation = pd.Series(
            False,
            index=patterns.index,
            dtype=bool
        )

        rolling_mean = volume.rolling(20, min_periods=5).mean()
        rolling_std = volume.rolling(20, min_periods=5).std()

        volume_regime = pd.Series(
            index=patterns.index,
            dtype="object"
        )

        for i in range(len(patterns)):

            v = f(volume.iloc[i])
            mean = f(rolling_mean.iloc[i])
            std = f(rolling_std.iloc[i])

            if pd.isna(v) or pd.isna(mean) or mean <= 0:
                volume_regime.iloc[i] = "UNKNOWN"
                continue

            z = (v - mean) / (std if std > 0 else 1e-9)

            if z >= 2.0:
                regime = "EXPANSION"
            elif z >= 1.0:
                regime = "BREAKOUT"
            elif z >= -0.5:
                regime = "AVERAGE"
            else:
                regime = "COMPRESSION"

            volume_regime.iloc[i] = regime

        for i in range(len(patterns)):

            p = patterns.iloc[i]

            if pd.isna(p):
                continue

            p = str(p).strip()

            v = f(volume.iloc[i])
            mean = f(rolling_mean.iloc[i])
            std = f(rolling_std.iloc[i])

            if pd.isna(v) or pd.isna(mean) or mean <= 0:
                continue

            z = (v - mean) / (std if std > 0 else 1e-9)
            regime = volume_regime.iloc[i]

            # ==================================================
            # VOLUME REGIME GATING RULES
            # ==================================================

            if regime == "EXPANSION":

                if p in BULLISH_PATTERNS:
                    confirmation.iloc[i] = True
                elif p in BEARISH_PATTERNS:
                    confirmation.iloc[i] = True
                else:
                    confirmation.iloc[i] = False

            elif regime == "BREAKOUT":

                if p in BULLISH_PATTERNS and z >= 1.2:
                    confirmation.iloc[i] = True
                elif p in BEARISH_PATTERNS and z >= 1.2:
                    confirmation.iloc[i] = True
                else:
                    confirmation.iloc[i] = False

            elif regime == "AVERAGE":

                if p in BULLISH_PATTERNS:
                    confirmation.iloc[i] = v >= mean * 1.10
                elif p in BEARISH_PATTERNS:
                    confirmation.iloc[i] = v >= mean * 1.08
                else:
                    confirmation.iloc[i] = False

            elif regime == "COMPRESSION":

                if p in BULLISH_PATTERNS:
                    confirmation.iloc[i] = False
                elif p in BEARISH_PATTERNS:
                    confirmation.iloc[i] = False
                else:
                    confirmation.iloc[i] = False

            else:

                confirmation.iloc[i] = False

        return confirmation

    except Exception as e:

        logger.warning(
            f"Volume confirmation failed: {e}"
        )

        return pd.Series(
            False,
            index=patterns.index,
            dtype=bool
        )

# ==========================================================
# PATTERN DIRECTION MAP (FIXED + COMPLETE)
# ==========================================================

BULLISH_PATTERNS = {
    "Hammer",
    "Bullish Engulfing",
    "Morning Star",
    "Morning Doji Star",
    "Bullish Harami",
    "Bullish Harami Cross",
    "Piercing Line",
    "Dragonfly Doji",
    "Tweezer Bottom",
    "Three White Soldiers",
    "Rising Window",

    # CONTINUATION / STRUCTURAL BULLISH
    "Rising Three Methods",
    "Separating Lines",
    "Three Inside Up",
    "Three Outside Up",

    # FIXED MISSING BULLISH STRUCTURES
    "Bullish Belt Hold",
    "Counterattack Lines",
    "Breakaway Gap"
}

BEARISH_PATTERNS = {
    "Shooting Star",
    "Bearish Engulfing",
    "Evening Star",
    "Evening Doji Star",
    "Bearish Harami",
    "Bearish Harami Cross",
    "Dark Cloud Cover",
    "Gravestone Doji",
    "Tweezer Top",
    "Three Black Crows",
    "Falling Window",
    "Hanging Man",

    # CONTINUATION / STRUCTURAL BEARISH
    "Falling Three Methods",
    "Three Inside Down",
    "Three Outside Down",

    # FIXED MISSING BEARISH STRUCTURES
    "Bearish Belt Hold",
    "Counterattack Lines",
    "Breakaway Gap"
}

def get_pattern_direction(pattern):

    if pattern in BULLISH_PATTERNS:
        return "Bullish"

    if pattern in BEARISH_PATTERNS:
        return "Bearish"

    return "Neutral"
    
def confirm_candlestick_patterns(df):

    states = pd.Series("None", index=df.index, dtype="object")
    scores = pd.Series(0.0, index=df.index)

    triggers = pd.Series(np.nan, index=df.index)
    failures = pd.Series(np.nan, index=df.index)
    directions = pd.Series("Neutral", index=df.index)

    avg_volume = (
        df["volume"]
        .rolling(20, min_periods=5)
        .mean()
    )

    vol_std = (
        df["volume"]
        .rolling(20, min_periods=5)
        .std()
    )

    for i in range(len(df) - 2):

        pattern = str(df.iloc[i]["CandlestickPattern"])

        if pattern == "No Pattern":
            continue

        score = 20.0
        confidence_contribution = 0.0

        pattern_high = f(df.iloc[i]["high"])
        pattern_low = f(df.iloc[i]["low"])

        next_close = f(df.iloc[i + 1]["close"])
        next_volume = f(df.iloc[i + 1]["volume"])

        follow_close = f(df.iloc[i + 2]["close"])

        vol_avg = f(avg_volume.iloc[i])
        vol_sigma = f(vol_std.iloc[i])

        current_volume = f(df.iloc[i]["volume"])

        trend_up = f(df.iloc[i]["close"]) > f(df.iloc[i]["SMA20"])
        trend_down = f(df.iloc[i]["close"]) < f(df.iloc[i]["SMA20"])

        # ==================================================
        # VOLUME CONFIDENCE CONTRIBUTION (NOT BOOLEAN)
        # ==================================================

        volume_strength = 0.0
        if vol_avg and vol_avg > 0:
            volume_strength = current_volume / vol_avg

        volume_z = 0.0
        if vol_sigma and vol_sigma > 0:
            volume_z = (current_volume - vol_avg) / vol_sigma

        confirmed = False
        failed = False

        # ==================================================
        # BULLISH
        # ==================================================

        if pattern in BULLISH_PATTERNS:

            triggers.iloc[i] = pattern_high
            failures.iloc[i] = pattern_low
            directions.iloc[i] = "Bullish"

            if next_close > pattern_high:

                score += 25
                confidence_contribution += 25

                if volume_strength >= 1.0:
                    score += min(20, volume_strength * 10)
                    confidence_contribution += min(20, volume_strength * 10)
                else:
                    score -= 5

                if volume_z >= 1.5:
                    score += 10
                    confidence_contribution += 10

                if trend_up:
                    score += 15
                    confidence_contribution += 15

                if follow_close > next_close:
                    score += 10
                    confidence_contribution += 10

                confirmed = True

            elif next_close < pattern_low:
                failed = True

        # ==================================================
        # BEARISH
        # ==================================================

        elif pattern in BEARISH_PATTERNS:

            triggers.iloc[i] = pattern_low
            failures.iloc[i] = pattern_high
            directions.iloc[i] = "Bearish"

            if next_close < pattern_low:

                score += 25
                confidence_contribution += 25

                if volume_strength >= 1.0:
                    score += min(25, volume_strength * 12)
                    confidence_contribution += min(25, volume_strength * 12)

                if volume_z >= 1.5:
                    score += 10
                    confidence_contribution += 10

                if trend_down:
                    score += 15
                    confidence_contribution += 15

                if follow_close < next_close:
                    score += 10
                    confidence_contribution += 10

                confirmed = True

            elif next_close > pattern_high:
                failed = True

        # ==================================================
        # STRUCTURED STATE ASSIGNMENT (NON-BINARY)
        # ==================================================

        final_score = min(100.0, max(0.0, score + (confidence_contribution * 0.1)))

        if failed:

            states.iloc[i] = "Failed"
            scores.iloc[i] = 0.0

        elif confirmed:

            if final_score >= 90:
                states.iloc[i] = "Institutional"

            elif final_score >= 75:
                states.iloc[i] = "Confirmed"

            elif final_score >= 50:
                states.iloc[i] = "Neutral"

            else:
                states.iloc[i] = "Weak"

            scores.iloc[i] = final_score

        else:

            states.iloc[i] = "Neutral"
            scores.iloc[i] = final_score * 0.5

        # ==================================================
        # CONFIDENCE CONTRIBUTION EXPOSED TO MT ENGINE
        # ==================================================

        scores.iloc[i] = min(100.0, scores.iloc[i] + (confidence_contribution * 0.15))

    return (
        states,
        scores,
        triggers,
        failures,
        directions
    )

def evaluate_stop_state(df, signal_index, stop_price, direction, lookahead=1):

    if signal_index is None or signal_index >= len(df) - 1:
        return {
            "stop_status": "UNKNOWN",
            "breached": False,
            "breach_index": None,
            "reason": "No forward candles to evaluate"
        }

    if pd.isna(stop_price):
        return {
            "stop_status": "UNKNOWN",
            "breached": False,
            "breach_index": None,
            "reason": "Invalid stop price"
        }

    for j in range(signal_index + 1, min(signal_index + lookahead + 1, len(df))):

        close = f(df.iloc[j]["close"])
        low = f(df.iloc[j]["low"])
        high = f(df.iloc[j]["high"])

        if direction == "LONG":
            if close < stop_price or low < stop_price:
                return {
                    "stop_status": "BREACHED",
                    "breached": True,
                    "breach_index": j,
                    "reason": "Price closed/broke below long stop"
                }

        elif direction == "SHORT":
            if close > stop_price or high > stop_price:
                return {
                    "stop_status": "BREACHED",
                    "breached": True,
                    "breach_index": j,
                    "reason": "Price closed/broke above short stop"
                }

    return {
        "stop_status": "VALID",
        "breached": False,
        "breach_index": None,
        "reason": "Stop not violated in lookahead window"
    }
    
# ==========================================================
# SINGLE TIMEFRAME ANALYSIS (FIXED - TIMEFRAME ISOLATED)
# ==========================================================
def analyze_single_timeframe(df, ticker, label):

    df = normalize_candlestick_ohlcv(df, ticker)

    df["SMA20"] = df["close"].rolling(20, min_periods=5).mean()

    structure = candle_structure(
        df["open"],
        df["high"],
        df["low"],
        df["close"]
    )

    df["Body"] = structure["Body"]
    df["Range"] = structure["Range"]
    df["BodyRatio"] = structure["BodyRatio"]
    df["UpperShadow"] = structure["UpperShadow"]
    df["LowerShadow"] = structure["LowerShadow"]

    # ==========================================================
    # PATTERN DETECTION ENGINE
    # ==========================================================

    single = detect_single_patterns(df)
    double = detect_two_candle_patterns(df)
    triple = detect_three_candle_patterns(df)
    advanced = detect_advanced_patterns(df)

    patterns = pd.DataFrame({
        "single": single,
        "double": double,
        "triple": triple,
        "advanced": advanced
    })

    priority = {
        "advanced": 4,
        "triple": 3,
        "double": 2,
        "single": 1
    }

    def resolve_pattern(row):

        best_pattern = "No Pattern"
        best_rank = 0

        for source in ["advanced", "triple", "double", "single"]:

            pattern = row[source]

            if pd.isna(pattern):
                continue

            rank = priority[source]

            if rank > best_rank:
                best_pattern = pattern
                best_rank = rank

        return best_pattern

    # ----------------------------------------------------------
    # STORE ALL DETECTED PATTERNS
    # ----------------------------------------------------------

    df["CandlestickPatterns"] = patterns.apply(
        lambda row: {
            "single": row["single"],
            "double": row["double"],
            "triple": row["triple"],
            "advanced": row["advanced"]
        },
        axis=1
    )

    # ----------------------------------------------------------
    # PRIMARY PATTERN COLUMN (REQUIRED)
    # ----------------------------------------------------------

    df["CandlestickPattern"] = patterns.apply(
        resolve_pattern,
        axis=1
    )

    # ----------------------------------------------------------
    # VOLUME CONFIRMATION (ENHANCED SEVERITY)
    # ==========================================================

    volume_series = pd.to_numeric(df["volume"], errors="coerce")

    vol_mean = volume_series.rolling(20, min_periods=5).mean()
    vol_std = volume_series.rolling(20, min_periods=5).std()

    vol_z = (volume_series - vol_mean) / (vol_std.replace(0, 1e-9))

    volume_strength = pd.Series(index=df.index, dtype="float")

    for i in range(len(df)):

        v = f(volume_series.iloc[i])
        z = f(vol_z.iloc[i])

        if pd.isna(v) or pd.isna(z):
            volume_strength.iloc[i] = 0.0
            continue

        if z >= 2.0:
            volume_strength.iloc[i] = 1.0
        elif z >= 1.0:
            volume_strength.iloc[i] = 0.75
        elif z >= 0.0:
            volume_strength.iloc[i] = 0.5
        else:
            volume_strength.iloc[i] = 0.25

    df["VolumeStrength"] = volume_strength

    df["PatternVolumeConfirm"] = (
        volume_strength >= 0.75
    )

    # ----------------------------------------------------------
    # INSTITUTIONAL CONFIRMATION ENGINE
    # ==========================================================

    (
        df["PatternState"],
        df["PatternScore"],
        df["PatternTrigger"],
        df["PatternFailure"],
        df["PatternDirection"]
    ) = confirm_candlestick_patterns(df)

    # ==========================================================
    # PATTERN STATE NORMALIZATION (SEVERITY TIERS)
    # ==========================================================

    normalized_state = []

    for i in range(len(df)):

        s = str(df["PatternState"].iloc[i])

        score = float(df["PatternScore"].iloc[i] or 0)

        vol_ok = bool(df["PatternVolumeConfirm"].iloc[i])

        if "Institutional" in s and score >= 70 and vol_ok:
            normalized_state.append("Institutional")

        elif "Confirmed" in s and score >= 50:
            normalized_state.append("Confirmed")

        elif score >= 25:
            normalized_state.append("Weak")

        else:
            normalized_state.append("None")

    df["PatternState"] = normalized_state

    # ==========================================================
    # SCORE NORMALIZATION (CROSS-TF CONSISTENCY)
    # ==========================================================

    raw_scores = pd.to_numeric(df["PatternScore"], errors="coerce").fillna(0)

    max_score = raw_scores.max() if raw_scores.max() != 0 else 1

    df["PatternScore"] = (raw_scores / max_score) * 100

    # ==========================================================
    # LATEST CANDLE
    # ==========================================================

    latest = df.iloc[-1]

    latest_pattern = latest.get(
        "CandlestickPattern",
        "No Pattern"
    )

    latest_patterns = latest.get(
        "CandlestickPatterns",
        {}
    )

    latest_state = latest.get(
        "PatternState",
        "None"
    )

    latest_score = float(
        latest.get(
            "PatternScore",
            0
        ) or 0
    )

    latest_direction = latest.get(
        "PatternDirection",
        "Neutral"
    )

    # ==========================================================
    # TRADE SETUP
    # ==========================================================

    setup = build_trade_setup(
        latest_pattern,
        latest_direction,
        df=df,
        i=len(df) - 1
    ) or {}

    # ==========================================================
    # SIGNAL INDEX
    # ==========================================================

    signal_indexes = df.index[
        df["CandlestickPattern"] != "No Pattern"
    ]

    signal_index = (
        signal_indexes[-1]
        if len(signal_indexes) > 0
        else None
    )

    stop_price = setup.get("stop_price_hint")
    direction = setup.get("bias")

    # ==========================================================
    # RESULT
    # ==========================================================

    result = {
        "label": label,
        "dataframe": df,

        "latest_pattern": latest_pattern,
        "CandlestickPatterns": latest_patterns,

        "pattern_state": latest_state,
        "pattern_score": latest_score,
        "pattern_direction": latest_direction,

        "trigger_level": latest.get("PatternTrigger"),
        "failure_level": latest.get("PatternFailure"),

        "latest_confirmed_pattern": latest_pattern,

        "volume_confirmed": bool(
            latest.get(
                "PatternVolumeConfirm",
                False
            )
        ),

        "volume_strength": float(
            latest.get("VolumeStrength", 0) or 0
        ),

        "trade_setup": setup,

        "interpretation": interpret_pattern(
            latest_pattern
        ),

        "actionable": actionable_pattern(
            latest_pattern
        ),

        "latest_snapshot": latest.to_dict(),

        "stop_state": evaluate_stop_state(
            df,
            signal_index=signal_index,
            stop_price=(
                stop_price
                if stop_price is not None
                else float("nan")
            ),
            direction=direction
        )
    }

    result["journal_prompt"] = (
        build_candlestick_journal_prompt(
            result
        )
    )

    return result
    
# ==========================================================
# MULTI-TIMEFRAME ENGINE (FIXED - WEIGHTED TF DOMINANCE + HIERARCHY + CONFLICT RESOLUTION)
# ==========================================================

def analyze_multitimeframe_candlesticks(df_15m, df_1h, df_daily, ticker):

    results = {
        "15M": analyze_single_timeframe(df_15m, ticker, "15M"),
        "1H": analyze_single_timeframe(df_1h, ticker, "1H"),
        "DAILY": analyze_single_timeframe(df_daily, ticker, "DAILY")
    }

    bullish = 0
    bearish = 0

    confirmed_bullish = 0
    confirmed_bearish = 0

    timeframe_summary = {}

    tf_weights = {
        "15M": 1.0,
        "1H": 2.0,
        "DAILY": 3.0
    }

    tf_role = {
        "15M": "EXECUTION",
        "1H": "CONTEXT",
        "DAILY": "STRUCTURE"
    }

    weighted_bullish = 0.0
    weighted_bearish = 0.0
    weighted_neutral = 0.0

    bullish_score = 0.0
    bearish_score = 0.0
    neutral_score = 0.0

    volume_valid_bull = 0
    volume_valid_bear = 0

    daily_regime_block = False

    daily_pattern = str(
        results["DAILY"].get("latest_pattern", "No Pattern") or "No Pattern"
    )

    daily_state = str(
        results["DAILY"].get("pattern_state", "None") or "None"
    )

    daily_volume = bool(
        results["DAILY"].get("volume_confirmed", False)
    )

    if (
        "Doji" in daily_pattern
        or "Deliberation" in daily_pattern
        or "Exhaustion" in daily_pattern
        or "Spinning" in daily_pattern
    ):
        daily_regime_block = True

    # ==========================================================
    # TF DOMINANCE ENGINE (STRUCTURAL WEIGHTING, NOT COUNTS)
    # ==========================================================

    tf_dominance_score = {
        "BULL": 0.0,
        "BEAR": 0.0,
        "NEUTRAL": 0.0
    }

    for tf, r in results.items():

        pattern = str(
            r.get(
                "latest_pattern",
                "No Pattern"
            ) or "No Pattern"
        )

        state = str(
            r.get(
                "pattern_state",
                "None"
            ) or "None"
        )

        direction = str(
            r.get(
                "pattern_direction",
                "Neutral"
            ) or "Neutral"
        )

        score = float(
            r.get(
                "pattern_score",
                0
            ) or 0
        )

        volume_ok = bool(
            r.get(
                "volume_confirmed",
                False
            )
        )

        is_confirmed = (
            "Confirmation" in state
            or "Institutional" in state
            or "CONFIRMED" in state
        )

        tf_weight = tf_weights.get(tf, 1.0)

        # ==================================================
        # RAW COUNTING (DEMOTED - KEPT FOR LEGACY METRICS ONLY)
        # ==================================================

        if pattern in BULLISH_PATTERNS:
            bullish += 1

        elif pattern in BEARISH_PATTERNS:
            bearish += 1

        # ==================================================
        # VOLUME VALIDATION (STRUCTURAL FILTER)
        # ==================================================

        if pattern in BULLISH_PATTERNS and volume_ok:
            volume_valid_bull += 1

        elif pattern in BEARISH_PATTERNS and volume_ok:
            volume_valid_bear += 1

        # ==================================================
        # WEIGHTED STRUCTURE SCORING (PRIMARY ENGINE)
        # ==================================================

        pattern_strength = score

        if not volume_ok:
            pattern_strength *= 0.40

        if not is_confirmed:
            pattern_strength *= 0.60

        if tf == "DAILY":
            pattern_strength *= 1.35

        if tf == "1H":
            pattern_strength *= 1.10

        if tf == "15M":
            pattern_strength *= 0.85

        # ==================================================
        # TF DOMINANCE CONTRIBUTION (HIERARCHICAL SCORING)
        # ==================================================

        dominance_multiplier = tf_weight * pattern_strength

        if pattern in BULLISH_PATTERNS:
            weighted_bullish += dominance_multiplier
            bullish_score += dominance_multiplier
            tf_dominance_score["BULL"] += dominance_multiplier

        elif pattern in BEARISH_PATTERNS:
            weighted_bearish += dominance_multiplier
            bearish_score += dominance_multiplier
            tf_dominance_score["BEAR"] += dominance_multiplier

        else:
            weighted_neutral += dominance_multiplier
            neutral_score += dominance_multiplier
            tf_dominance_score["NEUTRAL"] += dominance_multiplier

        # ==================================================
        # TIMEFRAME SUMMARY (FULL STRUCTURAL CONTEXT)
        # ==================================================

        timeframe_summary[tf] = {
            "pattern": pattern,
            "state": state,
            "direction": direction,
            "score": score,
            "volume_confirmed": volume_ok,
            "confirmed": is_confirmed,
            "role": tf_role.get(tf, "UNKNOWN"),
            "weight": tf_weight,
            "weighted_strength": pattern_strength,
            "dominance_contribution": dominance_multiplier
        }

    # ==================================================
    # CONFLICT DETECTION LAYER (STRUCTURE + DOMINANCE BASED)
    # ==================================================

    conflict_detected = False

    total_pressure = bullish_score + bearish_score

    if (
        bullish_score > 0
        and bearish_score > 0
    ):
        if abs(bullish_score - bearish_score) / max(total_pressure, 1e-9) < 0.35:
            conflict_detected = True

    if (
        tf_role.get("DAILY") == "STRUCTURE"
        and bearish_score > bullish_score
        and "Bullish" in daily_pattern
    ):
        conflict_detected = True

    # ==================================================
    # ALIGNMENT ENGINE (HIERARCHICAL DOMINANCE MODEL)
    # ==================================================

    daily_bias = tf_dominance_score["BULL"] - tf_dominance_score["BEAR"]

    if daily_regime_block:

        if bearish_score > bullish_score:
            alignment = "Bearish Bias (Daily Regime Override)"

        elif bullish_score > bearish_score:
            alignment = "Bullish Bias (Daily Regime Capped)"

        else:
            alignment = "Rotational / Mixed (Daily Regime Block)"

    else:
        alignment = "Rotational / Mixed (Unresolved Dominance)"
        
        # DAILY OVERRIDE LAYER (STRUCTURE FIRST)
        if tf_dominance_score["BULL"] == tf_dominance_score["BEAR"] and daily_bias == 0:
            pass

        elif tf_dominance_score["BULL"] > tf_dominance_score["BEAR"] and tf_weights["DAILY"] >= 3.0:
            alignment = "Institutional Bullish Alignment (Daily Dominant)"

        elif tf_dominance_score["BEAR"] > tf_dominance_score["BULL"] and tf_weights["DAILY"] >= 3.0:
            alignment = "Institutional Bearish Alignment (Daily Dominant)"

        # 1H CONFIRMATION LAYER
        elif weighted_bullish > weighted_bearish and tf_weights["1H"] >= 2.0:
            alignment = "Bullish Alignment (1H Confirmed Structure)"

        elif weighted_bearish > weighted_bullish and tf_weights["1H"] >= 2.0:
            alignment = "Bearish Alignment (1H Confirmed Structure)"

        # 15M EXECUTION LAYER
        elif weighted_bullish > weighted_bearish and volume_valid_bull >= 2:
            alignment = "Institutional Bullish Alignment (Execution Validated)"

        elif weighted_bearish > weighted_bullish and volume_valid_bear >= 2:
            alignment = "Institutional Bearish Alignment (Execution Validated)"

        # FALLBACK STRUCTURE (WEIGHTED DOMINANCE)
        elif weighted_bullish > weighted_bearish:
            alignment = "Bullish Bias (Weighted Dominance)"

        elif weighted_bearish > weighted_bullish:
            alignment = "Bearish Bias (Weighted Dominance)"

        elif bullish > bearish:
            alignment = "Bullish Pattern Alignment"

        elif bearish > bullish:
            alignment = "Bearish Pattern Alignment"

        else:
            alignment = "Rotational / Mixed"

    # ==================================================
    # CONFLICT OVERRIDE MARKER
    # ==================================================

    if conflict_detected:
        alignment = alignment + " (Conflict Detected)"

    # ==================================================
    # ALIGNMENT SCORE (TRUE WEIGHTED STRUCTURE INDEX)
    # ==================================================

    alignment_score = round(
        (bullish_score + bearish_score + neutral_score)
        / max(sum(tf_weights.values()), 1e-9),
        2
    )

    if "alignment" not in locals():
        alignment = "Rotational / Mixed (Fallback Safety)"
        
    return {
        **results,

        "alignment": alignment,
        "alignment_score": alignment_score,

        "bullish_patterns": bullish,
        "bearish_patterns": bearish,

        "confirmed_bullish": confirmed_bullish,
        "confirmed_bearish": confirmed_bearish,

        "weighted_bullish": weighted_bullish,
        "weighted_bearish": weighted_bearish,
        "weighted_neutral": weighted_neutral,

        "volume_valid_bull": volume_valid_bull,
        "volume_valid_bear": volume_valid_bear,

        "conflict_detected": conflict_detected,

        "timeframe_summary": timeframe_summary,

        "tf_dominance_score": tf_dominance_score
    }
    
def format_candle_stop(result):

    stop_state = result.get("stop_state", {})
    setup = result.get("trade_setup", {}) or {}

    stop_price = setup.get("stop_price_hint")

    if stop_price is None or pd.isna(stop_price):
        return """
────────────────────────────
CANDLESTICK STOP

No candlestick stop defined.
"""

    return f"""
────────────────────────────
CANDLESTICK STOP

STOP HINT:
{stop_price}

STOP STATUS:
{stop_state.get("stop_status")}

BREACHED:
{stop_state.get("breached")}

REASON:
{stop_state.get("reason")}
"""


# ==========================================================
# JOURNAL BUILDER
# ==========================================================

def build_candlestick_journal_prompt(result):

    snapshot = result.get("latest_snapshot", {}) or {}
    setup = result.get("trade_setup", {}) or {}

    return f"""
Candlestick Pattern:
{result.get('latest_pattern')}

Interpretation:
{result.get('interpretation')}

Actionable:
{result.get('actionable')}

TRADE SETUP:
Bias: {setup.get("bias")}
Entry: {setup.get("entry")}
Entry Hint Price: {setup.get("entry_price_hint")}
Stop: {setup.get("stop")}
Stop Hint Price: {setup.get("stop_price_hint")}
Target: {setup.get("target")}
Structure High: {setup.get("structure_high")}
Structure Low: {setup.get("structure_low")}
Context: {setup.get("context")}

Volume Confirmation:
{result.get('volume_confirmed')}

Latest Candle Snapshot:
Open: {snapshot.get("open")}
High: {snapshot.get("high")}
Low: {snapshot.get("low")}
Close: {snapshot.get("close")}
"""


# ==========================================================
# JOURNAL FORMATTER (EXPORT READY)
# ==========================================================

def format_candlestick_for_journal(result):

    m15 = result.get("15M", {}) or {}
    h1 = result.get("1H", {}) or {}
    d1 = result.get("DAILY", {}) or {}

    m15_patterns = m15.get("CandlestickPatterns", {}) or {}
    h1_patterns = h1.get("CandlestickPatterns", {}) or {}
    d1_patterns = d1.get("CandlestickPatterns", {}) or {}

    m15_setup = m15.get("trade_setup", {}) or {}
    h1_setup = h1.get("trade_setup", {}) or {}
    d1_setup = d1.get("trade_setup", {}) or {}

    m15_score = float(m15.get("pattern_score", 0) or 0)
    h1_score = float(h1.get("pattern_score", 0) or 0)
    d1_score = float(d1.get("pattern_score", 0) or 0)

    return f"""
====================================================
📊 CANDLESTICK MULTI-TIMEFRAME ENGINE
====================================================

📈 ALIGNMENT:
{result.get("alignment", "Unknown")}

----------------------------------------------------
15M:

Primary Pattern:
{m15.get("latest_pattern", "No Pattern")}

Patterns:
Single: {m15_patterns.get("single")}
Double: {m15_patterns.get("double")}
Triple: {m15_patterns.get("triple")}
Advanced: {m15_patterns.get("advanced")}

Pattern Direction:{get_pattern_direction(m15.get("latest_pattern"))}
Pattern State:{m15.get("pattern_state", "None")}
Reliability Score:{m15_score:.0f}/100

Interpretation:{m15.get("interpretation", "")}
Volume Confirmed:{m15.get("volume_confirmed", False)}
Actionable:{m15.get("actionable", "")}
Trigger Level:{m15.get("trigger_level")}
Failure Level:{m15.get("failure_level")}

--- TRADE SETUP (15M) ---

Bias:{m15_setup.get("bias")}
Entry:{m15_setup.get("entry")}
Entry Price:{m15_setup.get("entry_price_hint")}
Stop:{m15_setup.get("stop")}
Stop Price:{m15_setup.get("stop_price_hint")}
Target:{m15_setup.get("target")}

Context:{m15_setup.get("context")}
Reference High:{m15_setup.get("reference_high")}
Reference Low:{m15_setup.get("reference_low")}
Reference Close:{m15_setup.get("reference_close")}

----------------------------------------------------
1H:

Primary Pattern:
{h1.get("latest_pattern", "No Pattern")}

Patterns:
Single: {h1_patterns.get("single")}
Double: {h1_patterns.get("double")}
Triple: {h1_patterns.get("triple")}
Advanced: {h1_patterns.get("advanced")}

Pattern Direction:{get_pattern_direction(h1.get("latest_pattern"))}
Pattern State:{h1.get("pattern_state", "None")}
Reliability Score:{h1_score:.0f}/100

Interpretation:{h1.get("interpretation", "")}
Volume Confirmed:{h1.get("volume_confirmed", False)}
Actionable:{h1.get("actionable", "")}
Trigger Level:{h1.get("trigger_level")}
Failure Level:{h1.get("failure_level")}

--- TRADE SETUP (1H) ---

Bias:{h1_setup.get("bias")}
Entry:{h1_setup.get("entry")}
Entry Price:{h1_setup.get("entry_price_hint")}
Stop:{h1_setup.get("stop")}
Stop Price:{h1_setup.get("stop_price_hint")}
Target:{h1_setup.get("target")}

Context:{h1_setup.get("context")}
Reference High:{h1_setup.get("reference_high")}
Reference Low:{h1_setup.get("reference_low")}
Reference Close:{h1_setup.get("reference_close")}

----------------------------------------------------
DAILY:

Primary Pattern:
{d1.get("latest_pattern", "No Pattern")}

Patterns:
Single: {d1_patterns.get("single")}
Double: {d1_patterns.get("double")}
Triple: {d1_patterns.get("triple")}
Advanced: {d1_patterns.get("advanced")}

Pattern Direction:{get_pattern_direction(d1.get("latest_pattern"))}
Pattern State:{d1.get("pattern_state", "None")}
Reliability Score:{d1_score:.0f}/100

Interpretation:{d1.get("interpretation", "")}
Volume Confirmed:{d1.get("volume_confirmed", False)}
Actionable:{d1.get("actionable", "")}
Trigger Level:{d1.get("trigger_level")}
Failure Level:{d1.get("failure_level")}

--- TRADE SETUP (DAILY) ---

Bias:{d1_setup.get("bias")}
Entry:{d1_setup.get("entry")}
Entry Price:{d1_setup.get("entry_price_hint")}
Stop:{d1_setup.get("stop")}
Stop Price:{d1_setup.get("stop_price_hint")}
Target:{d1_setup.get("target")}

Context:{d1_setup.get("context")}
Reference High:{d1_setup.get("reference_high")}
Reference Low:{d1_setup.get("reference_low")}
Reference Close:{d1_setup.get("reference_close")}

====================================================
"""