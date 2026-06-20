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
# OHLC NORMALIZER (CASE C + AUTO TICKER)
# =========================================================
def normalize_ohlcv_columns(df, ticker=None):
    df = df.copy()

    if ticker is None:
        for col in df.columns:
            if col.startswith("close_"):
                ticker = col.split("_")[-1]
                break

    if ticker is None:
        raise ValueError("Cannot detect ticker from dataframe columns")

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
# VOLUME MODULE (UNCHANGED)
# =========================================================
def rvol(volume, period=20):
    volume = pd.to_numeric(volume, errors="coerce")
    avg = volume.rolling(period, min_periods=1).mean()
    return volume / avg


def detect_volume_spike(volume, threshold=1.5, period=20):
    volume = pd.to_numeric(volume, errors="coerce")
    avg = volume.rolling(period, min_periods=1).mean()
    return volume > (avg * threshold)


def institutional_accumulation_state(close, high, low, volume, period=20):
    close = pd.to_numeric(close, errors="coerce")
    volume = pd.to_numeric(volume, errors="coerce")

    price_range = (high - low).rolling(period).mean()
    vol_avg = volume.rolling(period).mean()
    compression = price_range / close.rolling(period).mean()

    state = pd.Series(index=close.index, dtype="object")

    for i in range(len(close)):
        if i < period:
            state.iloc[i] = "Unknown"
            continue

        if volume.iloc[i] > vol_avg.iloc[i] and compression.iloc[i] < 0.02:
            state.iloc[i] = "Accumulation"
        elif volume.iloc[i] > vol_avg.iloc[i] and compression.iloc[i] > 0.05:
            state.iloc[i] = "Distribution"
        else:
            state.iloc[i] = "Neutral"

    return state


# =========================================================
# 🕯 MARUBOZU DETECTION
# =========================================================
def detect_marubozu(data):

    if isinstance(data, pd.DataFrame):

        if len(data) < 1:
            return {
                "detected": False,
                "type": None,
                "strength": "None",
                "range": 0
            }

        curr = data.iloc[-1]

    else:
        raise ValueError("detect_marubozu() requires dataframe input")

    o = f(curr["Open"])
    h = f(curr["High"])
    l = f(curr["Low"])
    c = f(curr["Close"])

    if h == l:
        return {
            "detected": False,
            "type": None,
            "strength": "None",
            "range": 0
        }

    body = abs(c - o)
    rng = h - l

    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    body_ratio = body / rng
    wick_threshold = 0.10

    # reject weak candles
    if body_ratio < 0.75:
        return {
            "detected": False,
            "type": None,
            "strength": "Weak",
            "range": rng
        }

    bullish = c > o and upper_wick <= wick_threshold * rng and lower_wick <= wick_threshold * rng
    bearish = c < o and upper_wick <= wick_threshold * rng and lower_wick <= wick_threshold * rng

    if not bullish and not bearish:
        return {
            "detected": False,
            "type": None,
            "strength": "Rejection Candle",
            "range": rng
        }

    if body_ratio >= 0.90:
        strength = "Institutional"
    elif body_ratio >= 0.80:
        strength = "Strong"
    else:
        strength = "Standard"

    return {
        "detected": True,
        "type": "Bullish" if bullish else "Bearish",
        "strength": strength,
        "range": rng,
        "body_ratio": round(body_ratio, 3),
        "high": h,
        "low": l,
        "open": o,
        "close": c
    }


# =========================================================
# 🧠 MARUBOZU STATE MEMORY (UNCHANGED STRUCTURE)
# =========================================================
def marubozu_state_memory(df):

    states = []

    for i in range(len(df)):

        if i == 0:
            states.append(False)
            continue

        res = detect_marubozu(df.iloc[i-1:i+1])
        states.append(res["detected"])

    out = df.copy()
    out["marubozu_flag"] = states

    return out


# =========================================================
# 🧠 YESTERDAY MARUBOZU
# =========================================================
def detect_yesterday_marubozu(df):
    if len(df) < 2:
        return None

    return detect_marubozu(df.iloc[-2:])


# =========================================================
# 🧠 CONFIRMATION ENGINE (UNCHANGED LOGIC STYLE)
# =========================================================
def confirm_marubozu_today(today_candle, y_pin):

    if not y_pin or not y_pin.get("detected"):
        return "NONE"

    close = f(today_candle["Close"])
    open_ = f(today_candle["Open"])
    high = f(today_candle["High"])
    low = f(today_candle["Low"])

    y_high = y_pin.get("high")
    y_low = y_pin.get("low")

    if y_high is None or y_low is None:
        return "NONE"

    # =====================================================
    # BULLISH MARUBOZU
    # =====================================================
    if y_pin["type"] == "Bullish":

        if close > y_high:
            return "CONFIRMED"

        if close < y_low:
            return "FAILED"

        if high > y_high and close <= y_high:
            return "LIQUIDITY_REJECTION"

        return "PENDING"

    # =====================================================
    # BEARISH MARUBOZU
    # =====================================================
    if y_pin["type"] == "Bearish":

        if close < y_low:
            return "CONFIRMED"

        if close > y_high:
            return "FAILED"

        if low < y_low and close >= y_low:
            return "LIQUIDITY_REJECTION"

        return "PENDING"

    return "NONE"

# =========================================================
# TREND (UNCHANGED)
# =========================================================
def evaluate_trend(df):

    if len(df) < 50:
        return {"trend": "Unknown", "score": 0}

    close = pd.to_numeric(df["Close"], errors="coerce").dropna()

    ema8 = f(close.ewm(span=8).mean().iloc[-1])
    ema21 = f(close.ewm(span=21).mean().iloc[-1])
    sma50 = f(close.rolling(50).mean().iloc[-1])

    if ema8 > ema21 and ema21 > sma50:
        return {"trend": "Bullish", "score": 15}

    if ema8 < ema21 and ema21 < sma50:
        return {"trend": "Bearish", "score": 15}

    return {"trend": "Neutral", "score": 5}


# =========================================================
# LIQUIDITY SWEEP (UNCHANGED)
# =========================================================
def detect_liquidity_sweep(df, lookback=20):

    if len(df) < lookback + 2:
        return {"sweep": False, "type": None, "score": 0}

    current = df.iloc[-1]
    prev = df.iloc[-(lookback + 1):-1]

    swing_low = prev["Low"].min()
    swing_high = prev["High"].max()

    if current["Low"] < swing_low and current["Close"] > swing_low:
        return {"sweep": True, "type": "Spring", "score": 25}

    if current["High"] > swing_high and current["Close"] < swing_high:
        return {"sweep": True, "type": "Upthrust", "score": 25}

    return {"sweep": False, "type": None, "score": 0}


# =========================================================
# STRUCTURE (UNCHANGED)
# =========================================================
def evaluate_structure(df):

    if len(df) < 50:
        return {"score": 0, "label": "Unknown"}

    current = df.iloc[-1]

    support = df["Low"].rolling(50).min().iloc[-1]
    resistance = df["High"].rolling(50).max().iloc[-1]

    near_support = abs(current["Close"] - support) / current["Close"] < 0.03
    near_resistance = abs(current["Close"] - resistance) / current["Close"] < 0.03

    if near_support:
        label = "Near Support"
    elif near_resistance:
        label = "Near Resistance"
    else:
        label = "Neutral"

    return {
        "score": 15 if (near_support or near_resistance) else 0,
        "label": label
    }


# =========================================================
# VOLUME CONFIRMATION (UNCHANGED)
# =========================================================
def volume_confirmation(df):

    volume = df["Volume"]
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    rv = rvol(volume)
    spike = detect_volume_spike(volume)
    inst = institutional_accumulation_state(close, high, low, volume)

    confirmed = rv.iloc[-1] > 1.5 and spike.iloc[-1]

    return {
        "confirmed": confirmed,
        "rvol": round(rv.iloc[-1], 2),
        "institutional_state": str(inst.iloc[-1])
    }


# =========================================================
# 🧠 MAIN MARUBOZU ENGINE
# =========================================================
def analyze_marubozu(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    maru_today = detect_marubozu(df.iloc[-1:])
    maru_yesterday = detect_marubozu(df.iloc[-2:-1])

    confirmation_state = confirm_marubozu_today(today, maru_yesterday)

    trend = evaluate_trend(df)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    volume = volume_confirmation(df)

    # =====================================================
    # FIXED REGIME LOGIC (STATE-AWARE)
    # =====================================================
    if maru_today["detected"]:
        regime = "ACTIVE_MARUBOZU"
    elif maru_yesterday["detected"]:
        regime = "PRIOR_MARUBOZU_CONTEXT"
    else:
        regime = "NO_EDGE"

    trade_plan = build_marubozu_trade_plan(
        maru_today,
        maru_yesterday,
        confirmation_state,
        trend["trend"],
        sweep["sweep"],
        structure["label"],
        volume["confirmed"]
    )

    return {
        "journal_prompt": format_marubozu_journal_prompt({
            "today_marubozu": maru_today,
            "yesterday_marubozu": maru_yesterday,
            "confirmation_state": confirmation_state,
            "trend": trend["trend"],
            "liquidity_sweep": sweep["sweep"],
            "structure": structure["label"],
            "volume": volume["confirmed"],
            "regime": regime,
            "trade_plan": trade_plan,
            "today_candle": today.to_dict(),
            "yesterday_candle": yesterday.to_dict()
        })
    }


# =========================================================
# TRADE PLAN (MINIMAL ENGULFING STYLE ADAPTATION)
# =========================================================
def build_marubozu_trade_plan(
    maru_today,
    maru_yesterday,
    confirmation_state,
    trend,
    sweep,
    structure,
    volume
):

    # =====================================================
    # NO SIGNAL → RETURN NOTHING STRUCTURED
    # =====================================================
    if not maru_today.get("detected") and not maru_yesterday.get("detected"):
        return {
            "active": False
        }

    # =====================================================
    # ACTIVE MARUBOZU ONLY
    # =====================================================
    if maru_today.get("detected"):

        direction = maru_today.get("type")
        high = maru_today.get("high")
        low = maru_today.get("low")
        close = maru_today.get("close")

        # =========================
        # ENTRY + RISK MODEL
        # =========================
        if direction == "Bullish":
            entry = close
            stop = low
            target_1 = close + (close - low)
            target_2 = close + 2 * (close - low)
            failure = "Break below low invalidates long"
        else:
            entry = close
            stop = high
            target_1 = close - (high - close)
            target_2 = close - 2 * (high - close)
            failure = "Break above high invalidates short"

        # =========================
        # SETUP LABEL ONLY (NO NOISE)
        # =========================
        if confirmation_state == "CONFIRMED":
            setup = "CONFIRMED MARUBOZU CONTINUATION"
        elif confirmation_state == "FAILED":
            setup = "FAILED MARUBOZU REVERSAL"
        elif confirmation_state == "LIQUIDITY_REJECTION":
            setup = "MARUBOZU LIQUIDITY REJECTION"
        else:
            setup = "ACTIVE MARUBOZU SETUP"

        return {
            "active": True,
            "setup": setup,
            "entry": round(entry, 5),
            "stop": round(stop, 5),
            "target_1": round(target_1, 5),
            "target_2": round(target_2, 5),
            "failure": failure
        }

    # =====================================================
    # PRIOR CONTEXT ONLY (NO TRADE PLAN)
    # =====================================================
    if maru_yesterday.get("detected"):
        return {
            "active": False
        }

    return {
        "active": False
    }

# =========================================================
# FORMATTER
# =========================================================
def format_marubozu_journal_prompt(result: dict):

    m = result.get("today_marubozu", {})
    y = result.get("yesterday_marubozu", {})
    tp = result.get("trade_plan", {})

    trade_block = ""

    # =====================================================
    # ONLY SHOW TRADE PLAN IF ACTIVE
    # =====================================================
    if tp.get("active"):

        trade_block = f"""
--------------------------------------------------
🎯 TRADE PLAN

- Setup:  {tp.get('setup')}
- Entry:  {tp.get('entry')}
- Stop:  {tp.get('stop')}
- Target 1:  {tp.get('target_1')}
- Target 2:  {tp.get('target_2')}
- Failure Condition:  {tp.get('failure')}
"""

    return f"""
# ==================================================
📌 INSTITUTIONAL MARUBOZU PATTERN ANALYSIS (CONFIRMATION MODEL)
# ==================================================

TODAY:
- Detected: {m.get('detected')}
- Type: {m.get('type')}
- Strength: {m.get('strength')}
- Range: {m.get('range')}

YESTERDAY:
- Detected: {y.get('detected')}
- Type: {y.get('type')}
- Confirmation State: {result.get('confirmation_state')}

--------------------------------------------------
📊 CONTEXT:
- Trend: {result.get('trend')}
- Sweep: {result.get('liquidity_sweep')}
- Structure: {result.get('structure')}
- Volume: {result.get('volume')}

--------------------------------------------------
⚠️ REGIME:
- {result.get('regime')}

{trade_block}
"""