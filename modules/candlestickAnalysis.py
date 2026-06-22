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
# ADVANCED PATTERNS (FIXED - STRICT LOGIC + NO OVERLAP BUGS)
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

        prev2_bull = prev2_c > prev2_o
        prev2_bear = prev2_c < prev2_o

        prev_bull = prev_c > prev_o
        prev_bear = prev_c < prev_o

        prev_body_high = max(prev_o, prev_c)
        prev_body_low = min(prev_o, prev_c)

        curr_body_high = max(o, c)
        curr_body_low = min(o, c)

        # ==================================================
        # STRICT DOJI / SINGLE CANDLE STRUCTURES
        # ==================================================

        if br <= 0.05:

            if h == l == o == c:
                pattern.iloc[i] = "Four Price Doji"

            elif (h - l) > 3 * body:
                pattern.iloc[i] = "Rickshaw Man"

            elif (h - c) > (c - l):
                pattern.iloc[i] = "Gravestone Doji"

            else:
                pattern.iloc[i] = "Dragonfly Doji"

        elif br <= 0.1:
            pattern.iloc[i] = "Doji"

        elif br <= 0.2 and (h - l) > 3 * body:
            pattern.iloc[i] = "High Wave Candle"

        elif br <= 0.3:
            pattern.iloc[i] = "Spinning Top"

        # ==================================================
        # 3-CANDLE REVERSALS (STRICT ORDER + CLEAN LOGIC)
        # ==================================================

        if prev2_bear and br <= 0.1 and prev_bull and c > o:
            pattern.iloc[i] = "Morning Doji Star"

        if prev2_bull and br <= 0.1 and prev_bear and c < o:
            pattern.iloc[i] = "Evening Doji Star"

        if prev2_bear and prev_bull and c > o:
            pattern.iloc[i] = "Morning Star"

        if prev2_bull and prev_bear and c < o:
            pattern.iloc[i] = "Evening Star"

        # ==================================================
        # 2-CANDLE ENGULFING (STRICT BODY RULES)
        # ==================================================

        if prev_bear and curr_body_high >= prev_body_high and curr_body_low <= prev_body_low and c > o:
            pattern.iloc[i] = "Bullish Engulfing"

        if prev_bull and curr_body_high >= prev_body_high and curr_body_low <= prev_body_low and c < o:
            pattern.iloc[i] = "Bearish Engulfing"

        # ==================================================
        # HARAMI (STRICT CONTAINMENT - FIXED)
        # ==================================================

        if prev_bear and curr_body_high <= prev_body_high and curr_body_low >= prev_body_low and c > o:
            pattern.iloc[i] = "Bullish Harami"

        if prev_bull and curr_body_high <= prev_body_high and curr_body_low >= prev_body_low and c < o:
            pattern.iloc[i] = "Bearish Harami"

        if prev_bear and (h - l) <= body * 0.5:
            pattern.iloc[i] = "Bullish Harami Cross"

        if prev_bull and (h - l) <= body * 0.5:
            pattern.iloc[i] = "Bearish Harami Cross"

        # ==================================================
        # TWEEZERS (STRICT HIGH/LOW MATCH)
        # ==================================================

        if abs(h - prev_h) <= body * 0.1:
            pattern.iloc[i] = "Tweezer Top"

        if abs(l - prev_l) <= body * 0.1:
            pattern.iloc[i] = "Tweezer Bottom"

        # ==================================================
        # 3-CANDLE CONTINUATION PATTERNS
        # ==================================================

        if prev2_bull and prev_bull and c > o:
            pattern.iloc[i] = "Three White Soldiers"

        if prev2_bear and prev_bear and c < o:
            pattern.iloc[i] = "Three Black Crows"

        # ==================================================
        # GAP / WINDOW (STRICT GAP RULE)
        # ==================================================

        if l > prev_h:
            pattern.iloc[i] = "Rising Window"

        if h < prev_l:
            pattern.iloc[i] = "Falling Window"

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
        "Ladder Bottom": "Multi-candle bullish recovery."
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
        "Falling Window": "Bearish gap. Continuation short bias."
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
            "context": "No pattern detected"
        }

    key = str(pattern).strip()

    # fallback safety
    if df is not None and i < len(df):
        row = df.iloc[i]
        high = f(row["high"])
        low = f(row["low"])
        close = f(row["close"])
    else:
        high = low = close = None

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

        "Gravestone Doji": {
            "bias": "SHORT",
            "entry": "Break below candle low",
            "stop": "Above rejection high",
            "target": "Range low / liquidity sweep",
            "context": "Rejection of highs"
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
        }
    }

    setup = setups.get(key)

    if not setup:
        return {
            "bias": "NEUTRAL",
            "entry": "No structured setup",
            "stop": "N/A",
            "target": "N/A",
            "context": "No institutional edge defined"
        }

    # optional dynamic levels
    setup = setup.copy()

    if high is not None and low is not None:
        setup["reference_high"] = high
        setup["reference_low"] = low
        setup["reference_close"] = close

    # ======================================================
    # JOURNAL PRICE PACK (NEW)
    # ======================================================

    setup["entry_price_hint"] = close
    setup["stop_price_hint"] = low if setup["bias"] == "LONG" else high
    setup["structure_high"] = high
    setup["structure_low"] = low
    
    return setup
    
# ==========================================================
# VOLUME CONFIRMATION (UNCHANGED)
# ==========================================================

def volume_confirmation(volume, patterns):

    try:
        vol_mean = volume.iloc[-20:].mean()
        confirmation = pd.Series(False, index=patterns.index)

        for i in range(len(patterns)):
            p = patterns.iloc[i]

            if pd.isna(p):
                confirmation.iloc[i] = False
                continue

            if "Bullish" in str(p):
                confirmation.iloc[i] = volume.iloc[i] > vol_mean
            elif "Bearish" in str(p):
                confirmation.iloc[i] = volume.iloc[i] > vol_mean * 0.9
            else:
                confirmation.iloc[i] = volume.iloc[i] > vol_mean * 0.8

        return confirmation

    except Exception as e:
        logger.warning(f"Volume confirmation failed: {e}")
        return pd.Series(False, index=patterns.index)

# ==========================================================
# INSTITUTIONAL PATTERN CONFIRMATION ENGINE
# ==========================================================
# ==========================================================
# PATTERN DIRECTION MAP
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
    "Rising Window"
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
    "Hanging Man"
}

# ==========================================================
# INSTITUTIONAL PATTERN CONFIRMATION ENGINE
# ==========================================================

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

    for i in range(len(df) - 2):

        pattern = str(df.iloc[i]["CandlestickPattern"])

        if pattern == "No Pattern":
            continue

        score = 25

        pattern_high = f(df.iloc[i]["high"])
        pattern_low = f(df.iloc[i]["low"])

        next_close = f(df.iloc[i + 1]["close"])
        next_volume = f(df.iloc[i + 1]["volume"])

        follow_close = f(df.iloc[i + 2]["close"])

        vol_avg = f(avg_volume.iloc[i])

        trend_up = (
            f(df.iloc[i]["close"])
            > f(df.iloc[i]["SMA20"])
        )

        trend_down = (
            f(df.iloc[i]["close"])
            < f(df.iloc[i]["SMA20"])
        )

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

                if next_volume > vol_avg:
                    score += 25

                if trend_up:
                    score += 15

                if follow_close > next_close:
                    score += 10

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

                if next_volume > vol_avg:
                    score += 25

                if trend_down:
                    score += 15

                if follow_close < next_close:
                    score += 10

                confirmed = True

            elif next_close > pattern_high:
                failed = True

        # ==================================================
        # STATE ASSIGNMENT
        # ==================================================

        if failed:

            states.iloc[i] = "Failed"
            scores.iloc[i] = 0

        elif confirmed:

            if score >= 90:
                states.iloc[i] = "Institutional Grade"

            elif score >= 75:
                states.iloc[i] = "Strong Confirmation"

            elif score >= 50:
                states.iloc[i] = "Moderate Confirmation"

            else:
                states.iloc[i] = "Weak Confirmation"

            scores.iloc[i] = score

        else:

            states.iloc[i] = "Pending"
            scores.iloc[i] = score

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
# SINGLE TIMEFRAME ANALYSIS
# ==========================================================
def analyze_single_timeframe(df, ticker, label):

    df = normalize_candlestick_ohlcv(df, ticker)

    df["SMA20"] = df["close"].rolling(20, min_periods=5).mean()

    structure = candle_structure(df["open"], df["high"], df["low"], df["close"])

    df["Body"] = structure["Body"]
    df["Range"] = structure["Range"]
    df["BodyRatio"] = structure["BodyRatio"]
    df["UpperShadow"] = structure["UpperShadow"]
    df["LowerShadow"] = structure["LowerShadow"]

    # ==========================================================
    # FIXED PATTERN RESOLUTION ENGINE (NO OVERWRITE LOGIC)
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

    # PRIORITY SYSTEM (HIGHEST WIN)
    priority = {
        "advanced": 4,
        "triple": 3,
        "double": 2,
        "single": 1
    }

    def resolve_pattern(row):

        candidates = [
            ("advanced", row["advanced"]),
            ("triple", row["triple"]),
            ("double", row["double"]),
            ("single", row["single"])
        ]

        best_pattern = "No Pattern"
        best_rank = 0

        for source, pattern in candidates:

            if pd.isna(pattern):
                continue

            rank = priority[source]

            # overwrite only if higher priority
            if rank > best_rank:
                best_pattern = pattern
                best_rank = rank

        return best_pattern

    df["CandlestickPattern"] = patterns.apply(resolve_pattern, axis=1)

    df["PatternVolumeConfirm"] = volume_confirmation(
        df["volume"],
        df["CandlestickPattern"]
    )

    (
        df["PatternState"],
        df["PatternScore"],
        df["PatternTrigger"],
        df["PatternFailure"],
        df["PatternDirection"]
    ) = confirm_candlestick_patterns(df)

    latest = df.iloc[-1]

    confirmed_df = df[df["PatternState"].isin([
        "Institutional Grade",
        "Strong Confirmation",
        "Moderate Confirmation",
        "Weak Confirmation"
    ])]

    latest_confirmed = confirmed_df.iloc[-1] if not confirmed_df.empty else latest

    latest_pattern = latest.get("CandlestickPattern", "No Pattern")

    setup = build_trade_setup(
        latest_confirmed.get("CandlestickPattern"),
        latest_confirmed.get("PatternDirection"),
        df=df
    ) or {}

    signal_index = df.index[df["CandlestickPattern"] != "No Pattern"]
    signal_index = signal_index[-1] if len(signal_index) > 0 else None

    stop_price = setup.get("stop_price_hint")
    direction = setup.get("bias")

    result = {
        "label": label,
        "dataframe": df,
        "latest_pattern": latest_pattern,
        "pattern_state": latest_confirmed.get("PatternState", "None"),
        "pattern_score": float(latest_confirmed.get("PatternScore", 0)),
        "pattern_direction": latest_confirmed.get("PatternDirection", "Neutral"),
        "trigger_level": latest_confirmed.get("PatternTrigger"),
        "failure_level": latest_confirmed.get("PatternFailure"),
        "latest_confirmed_pattern": latest_confirmed.get("CandlestickPattern", "No Pattern"),
        "volume_confirmed": bool(latest.get("PatternVolumeConfirm", False)),
        "trade_setup": setup,
        "interpretation": interpret_pattern(latest_pattern),
        "actionable": actionable_pattern(latest_pattern),
        "latest_snapshot": latest.to_dict(),
        "stop_state": evaluate_stop_state(
            df,
            signal_index=signal_index,
            stop_price=stop_price if stop_price is not None else float("nan"),
            direction=direction
        )
    }

    result["journal_prompt"] = build_candlestick_journal_prompt(result)

    return result
    
# ==========================================================
# MULTI-TIMEFRAME ENGINE
# ==========================================================

def analyze_multitimeframe_candlesticks(df_15m, df_1h, df_daily, ticker):

    results = {
        "15M": analyze_single_timeframe(df_15m, ticker, "15M"),
        "1H": analyze_single_timeframe(df_1h, ticker, "1H"),
        "DAILY": analyze_single_timeframe(df_daily, ticker, "DAILY")
    }

    bullish = sum("Bullish" in str(r.get("latest_pattern")) for r in results.values())
    bearish = sum("Bearish" in str(r.get("latest_pattern")) for r in results.values())

    confirmed_bullish = 0
    confirmed_bearish = 0

    for tf, r in results.items():

        pattern = str(
            r.get(
                "latest_pattern",
                ""
            )
        )

        state = str(
            r.get(
                "pattern_state",
                ""
            )
        )

        if "Confirmation" not in state \
           and "Institutional" not in state:
            continue

        if pattern in BULLISH_PATTERNS:
            confirmed_bullish += 1

        elif pattern in BEARISH_PATTERNS:
            confirmed_bearish += 1
            
    alignment = (
        "Institutional Bullish Alignment"
        if confirmed_bullish >= 3 else

        "Institutional Bearish Alignment"
        if confirmed_bearish >= 3 else

        "Partial Bullish Confirmation"
        if confirmed_bullish > confirmed_bearish else

        "Partial Bearish Confirmation"
        if confirmed_bearish > confirmed_bullish else

        "Rotational / Mixed"
    )

    return {
        **results,
        "alignment": alignment
    }

def format_candle_stop(result):

    stop_state = result.get("stop_state", {})
    setup = result.get("trade_setup", {})

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

    snapshot = result.get("latest_snapshot", {})

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

    m15 = result.get("15M", {})
    h1 = result.get("1H", {})
    d1 = result.get("DAILY", {})

    m15_setup = m15.get("trade_setup", {})
    h1_setup = h1.get("trade_setup", {})
    d1_setup = d1.get("trade_setup", {})

    return f"""
====================================================
📊 CANDLESTICK MULTI-TIMEFRAME ENGINE
====================================================

📈 ALIGNMENT:
{result.get("alignment")}

----------------------------------------------------
15M:
Pattern: {m15.get("latest_pattern")}
Pattern State: {m15.get("pattern_state")}
Reliability Score: {m15.get("pattern_score"):.0f}/100
Interpretation: {m15.get("interpretation")}
Volume Confirmed: {m15.get("volume_confirmed")}
Actionable: {m15.get("actionable")}

--- TRADE SETUP (15M) ---
Bias: {m15_setup.get("bias")}
Entry Price: {m15_setup.get("entry_price_hint")}
Stop Price: {m15_setup.get("stop_price_hint")}
Target: {m15_setup.get("target")}

----------------------------------------------------
1H:
Pattern: {h1.get("latest_pattern")}
Pattern State: {h1.get("pattern_state")}
Reliability Score: {h1.get("pattern_score"):.0f}/100
Interpretation: {h1.get("interpretation")}
Volume Confirmed: {h1.get("volume_confirmed")}
Actionable: {h1.get("actionable")}

--- TRADE SETUP (1H) ---
Bias: {h1_setup.get("bias")}
Entry Price: {h1_setup.get("entry_price_hint")}
Stop Price: {h1_setup.get("stop_price_hint")}
Target: {h1_setup.get("target")}

----------------------------------------------------
DAILY:
Pattern: {d1.get("latest_pattern")}
Pattern State: {d1.get("pattern_state")}
Reliability Score: {d1.get("pattern_score"):.0f}/100
Interpretation: {d1.get("interpretation")}
Volume Confirmed: {d1.get("volume_confirmed")}
Actionable: {d1.get("actionable")}

--- TRADE SETUP (DAILY) ---
Bias: {d1_setup.get("bias")}
Entry: {d1_setup.get("entry")}
Entry Price: {d1_setup.get("entry_price_hint")}
Stop: {d1_setup.get("stop")}
Stop Price: {d1_setup.get("stop_price_hint")}
Target: {d1_setup.get("target")}
Context: {d1_setup.get("context")}

====================================================
"""