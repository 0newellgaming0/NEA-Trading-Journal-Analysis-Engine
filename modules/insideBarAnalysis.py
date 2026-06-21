import numpy as np
import pandas as pd

# =========================================================
# SAFE SCALAR EXTRACTOR
# =========================================================
def f(x):
    try:
        if isinstance(x, pd.Series):
            x = x.iloc[-1]
        if pd.isna(x):
            return 0.0
        return float(x)
    except:
        return 0.0


# =========================================================
# OHLC NORMALIZER
# =========================================================
def normalize_ohlcv_columns(df, ticker=None):
    df = df.copy()

    if ticker is None:
        for col in df.columns:
            if col.startswith("close_"):
                ticker = col.split("_")[-1]
                break

    if ticker is None:
        raise ValueError("Cannot detect ticker")

    t = ticker.lower()

    def pick(col):
        return df[col] if col in df.columns else pd.Series(np.nan, index=df.index)

    df["Open"] = pick(f"open_{t}")
    df["High"] = pick(f"high_{t}")
    df["Low"] = pick(f"low_{t}")
    df["Close"] = pick(f"close_{t}")
    df["Volume"] = pick(f"volume_{t}")

    return df


def enforce_schema(df):
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["Open", "High", "Low", "Close"])


# =========================================================
# 🧠 INSIDE BAR DETECTION
# =========================================================
def detect_inside_bar(df):

    if df is None or len(df) < 2:
        return {"detected": False}

    mother = df.iloc[-2]
    inside = df.iloc[-1]

    m_high = f(mother.get("High"))
    m_low = f(mother.get("Low"))

    i_high = f(inside.get("High"))
    i_low = f(inside.get("Low"))

    if m_high == 0 or m_low == 0:
        return {"detected": False}

    if not (i_high <= m_high and i_low >= m_low):
        return {"detected": False}

    m_open = f(mother.get("Open"))
    m_close = f(mother.get("Close"))
    i_open = f(inside.get("Open"))
    i_close = f(inside.get("Close"))

    mother_body = abs(m_close - m_open)
    inside_body = abs(i_close - i_open)

    ratio = inside_body / mother_body if mother_body > 0 else 0

    return {
        "detected": True,
        "mother_high": m_high,
        "mother_low": m_low,
        "inside_high": i_high,
        "inside_low": i_low,
        "compression_ratio": round(ratio, 3),
        "type": "Inside Bar"
    }

# =========================================================
# 🧠 BREAKOUT CLASSIFICATION
# =========================================================
def classify_inside_breakout(df, inside):

    if not inside or not inside.get("detected"):
        return "NONE"

    last = df.iloc[-1]

    close = f(last.get("Close"))
    high = f(last.get("High"))
    low = f(last.get("Low"))

    m_high = inside["mother_high"]
    m_low = inside["mother_low"]

    # =========================
    # CONFIRMED STATES FIRST
    # =========================
    if close > m_high:
        return "BULLISH_BREAKOUT_CONFIRMED"

    if close < m_low:
        return "BEARISH_BREAKOUT_CONFIRMED"

    # =========================
    # LIQUIDITY EVENTS
    # =========================
    if high > m_high and close <= m_high:
        return "BULLISH_FALSE_BREAK"

    if low < m_low and close >= m_low:
        return "BEARISH_FALSE_BREAK"

    # =========================
    # LIVE ACTIVE STATE (IMPORTANT FIX)
    # =========================
    return "PENDING"


# =========================================================
# 🧠 EVENT STATE ENGINE
# =========================================================
def build_inside_bar_event_state(df, max_hold=5):

    events = []
    active = None

    for i in range(len(df)):

        window = df.iloc[max(0, i-1):i+1]
        inside = detect_inside_bar(window)

        # START EVENT
        if active is None and inside.get("detected"):

            active = {
                "start": i,
                "mother_high": inside["mother_high"],
                "mother_low": inside["mother_low"],
                "status": "PENDING",
                "type": "Inside Bar"
            }

        if active is None:
            continue

        candle = df.iloc[i]
        close = f(candle.get("Close"))
        high = f(candle.get("High"))
        low = f(candle.get("Low"))

        # =========================
        # STATE MACHINE (FIXED ORDER)
        # =========================

        if close > active["mother_high"]:
            active["status"] = "CONFIRMED_BULLISH"

        elif close < active["mother_low"]:
            active["status"] = "CONFIRMED_BEARISH"

        elif high > active["mother_high"] and close <= active["mother_high"]:
            active["status"] = "LIQUIDITY_REJECTION_BULL"

        elif low < active["mother_low"] and close >= active["mother_low"]:
            active["status"] = "LIQUIDITY_REJECTION_BEAR"

        # HOLD WINDOW (DO NOT FORCE CLOSE EARLY)
        if i - active["start"] >= max_hold and active["status"] == "PENDING":
            active["status"] = "EXPIRED"

        # ONLY FINALIZE WHEN RESOLVED OR EXPIRED
        if active["status"] != "PENDING":
            events.append(active.copy())
            active = None

    return events, active


# =========================================================
# 🧠 TRADE PLAN GENERATOR (FIXED - NEVER RETURNS NONE)
# =========================================================
def build_inside_bar_trade_plan(inside, breakout_state):

    if not inside or not inside.get("detected"):
        return {
            "setup": "NO SIGNAL",
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "failure": "No inside bar detected",
            "interpretation": "No valid consolidation structure."
        }

    high = inside["mother_high"]
    low = inside["mother_low"]
    rng = max(high - low, 1e-9)

    # =====================================================
    # PENDING STATE (FIXED: NO DUAL ENTRY CONFUSION)
    # =====================================================
    if breakout_state == "PENDING":
        return {
            "setup": "INSIDE BAR BREAKOUT (UNCONFIRMED)",

            # =================================================
            # ALWAYS SHOW BOTH SIDES (THIS IS KEY FIX)
            # =================================================
            "long_trigger": f"Break & close above {high}",
            "short_trigger": f"Break & close below {low}",

            # PRE-MAPPED EXECUTION LEVELS
            "entry_long": high,
            "entry_short": low,

            "stop_long": low,
            "stop_short": high,

            # STRUCTURED TARGETS (NOT NONE)
            "target_long_1": high + rng,
            "target_long_2": high + (2 * rng),

            "target_short_1": low - rng,
            "target_short_2": low - (2 * rng),

            # FAILURE LOGIC
            "failure_long": "Rejection back inside range after breakout",
            "failure_short": "Rejection back inside range after breakdown",

            # STATE CLARITY (IMPORTANT)
            "status": "PENDING_CONFIRMATION",

            "interpretation": (
                "Inside bar detected = compression phase. "
                "Market is coiling between liquidity levels. "
                "Both breakout directions are valid until confirmation."
            )
        }

    # =====================================================
    # BULLISH CONFIRMED
    # =====================================================
    if breakout_state == "BULLISH_BREAKOUT_CONFIRMED":
        return {
            "setup": "INSIDE BAR BREAKOUT LONG (CONFIRMED)",
            "entry": high,
            "stop": low,
            "target1": high + rng,
            "target2": high + (2 * rng),
            "failure": "Close back inside range",
            "interpretation": "Bullish expansion confirmed after compression."
        }

    # =====================================================
    # BEARISH CONFIRMED
    # =====================================================
    if breakout_state == "BEARISH_BREAKOUT_CONFIRMED":
        return {
            "setup": "INSIDE BAR BREAKOUT SHORT (CONFIRMED)",
            "entry": low,
            "stop": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": "Close back inside range",
            "interpretation": "Bearish expansion confirmed after compression."
        }

    # =====================================================
    # FALSE BREAK UP
    # =====================================================
    if breakout_state == "BULLISH_FALSE_BREAK":
        return {
            "setup": "FALSE BREAK SHORT (LIQUIDITY SWEEP)",
            "entry": high,
            "stop": high + rng * 0.1,
            "target1": low,
            "target2": low - rng,
            "failure": "Acceptance above high",
            "interpretation": "Buy-side liquidity sweep → rejection."
        }

    # =====================================================
    # FALSE BREAK DOWN
    # =====================================================
    if breakout_state == "BEARISH_FALSE_BREAK":
        return {
            "setup": "FALSE BREAK LONG (LIQUIDITY SWEEP)",
            "entry": low,
            "stop": low - rng * 0.1,
            "target1": high,
            "target2": high + rng,
            "failure": "Acceptance below low",
            "interpretation": "Sell-side liquidity sweep → reversal."
        }

    return {
        "setup": "INSIDE BAR ACTIVE SETUP",
        "entry": None,
        "stop": None,
        "target1": None,
        "target2": None,
        "failure": None,
        "interpretation": "Awaiting breakout confirmation."
    }

# =========================================================
# 🧠 MAIN ENGINE
# =========================================================
def analyze_inside_bar(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    inside = detect_inside_bar(df.iloc[-2:])
    breakout_state = classify_inside_breakout(df, inside)

    events, active = build_inside_bar_event_state(df)

    trade_plan = build_inside_bar_trade_plan(inside, breakout_state)

    return {
        "journal_prompt": format_inside_bar_journal_prompt({
            "inside": inside,
            "breakout_state": breakout_state,
            "trade_plan": trade_plan,
            "events": events,
            "active_event": active,
            "today_candle": df.iloc[-1].to_dict(),
            "mother_candle": df.iloc[-2].to_dict()
        })
    }

# =========================================================
# 📊 JOURNAL FORMATTER (FIXED SAFETY)
# =========================================================
def format_inside_bar_journal_prompt(result):

    inside = result.get("inside") or {}
    tp = result.get("trade_plan") or {}

    base = f"""
# ==================================================
📌 INSTITUTIONAL INSIDE BAR ANALYSIS
# ==================================================

INSIDE BAR:
- Detected: {inside.get('detected')}
- Compression: {inside.get('compression_ratio')}

MOTHER BAR:
- High: {inside.get('mother_high')}
- Low: {inside.get('mother_low')}

--------------------------------------------------
⚠️ BREAKOUT STATE:
{result.get('breakout_state')}

--------------------------------------------------
🎯 TRADE PLAN
"""

    # ================================
    # PENDING STATE (IMPORTANT FIX)
    # ================================
    if tp.get("status") == "PENDING_CONFIRMATION":

        return base + f"""

- Setup:  {tp.get('setup')}

- LONG TRIGGER:  {tp.get('long_trigger')}
- LONG ENTRY:  {tp.get('entry_long')}
- LONG STOP:  {tp.get('stop_long')}
- LONG TARGETS:  {tp.get('target_long_1')} → {tp.get('target_long_2')}

- SHORT TRIGGER:  {tp.get('short_trigger')}
- SHORT ENTRY:  {tp.get('entry_short')}
- SHORT STOP:  {tp.get('stop_short')}
- SHORT TARGETS:  {tp.get('target_short_1')} → {tp.get('target_short_2')}

--------------------------------------------------
🧠 INTERPRETATION

{tp.get('interpretation')}

--------------------------------------------------
🧭 STRUCTURE MODEL:
Inside Bar = Consolidation → Expansion OR Liquidity Sweep → Reversal
"""

    # ================================
    # CONFIRMED STATES
    # ================================
    return base + f"""

- Setup:  {tp.get('setup')}

- Entry:  {tp.get('entry')}
- Stop:  {tp.get('stop')}
- Target 1:  {tp.get('target1')}
- Target 2:  {tp.get('target2')}
- Failure:  {tp.get('failure')}

--------------------------------------------------
🧠 INTERPRETATION

{tp.get('interpretation')}

--------------------------------------------------
🧭 STRUCTURE MODEL:
Inside Bar = Consolidation → Expansion OR Liquidity Sweep → Reversal
"""