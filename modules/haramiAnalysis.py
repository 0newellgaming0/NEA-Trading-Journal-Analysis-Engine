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
# OHLC NORMALIZER (UNCHANGED)
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
# HARAMI DETECTION
# =========================================================
def detect_harami_pattern(df):

    if df is None or len(df) < 2:
        return {"detected": False, "type": None}

    c1 = df.iloc[-2]
    c2 = df.iloc[-1]

    o1, h1, l1, cl1 = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
    o2, h2, l2, cl2 = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])

    if any(np.isnan([o1, h1, l1, cl1, o2, h2, l2, cl2])):
        return {"detected": False, "type": None}

    body1_high, body1_low = max(o1, cl1), min(o1, cl1)
    body2_high, body2_low = max(o2, cl2), min(o2, cl2)

    body1_size = abs(cl1 - o1)
    body2_size = abs(cl2 - o2)

    # containment check
    if not (body2_high <= body1_high and body2_low >= body1_low):
        return {"detected": False, "type": None}

    strength = classify_harami_strength(c1, c2)
    if strength == "INVALID":
        return {"detected": False, "type": None}

    is_bull = cl1 < o1 and body2_size < body1_size * 0.6
    is_bear = cl1 > o1 and body2_size < body1_size * 0.6

    if is_bull:
        return {
            "detected": True,
            "type": "BullishHarami",
            "strength": strength,
            "high": h2,
            "low": l2,
            "close": cl2
        }

    if is_bear:
        return {
            "detected": True,
            "type": "BearishHarami",
            "strength": strength,
            "high": h2,
            "low": l2,
            "close": cl2
        }

    return {"detected": False, "type": None}

# =========================================================
# HARAMI FORMATION TRACKER
# =========================================================
def detect_harami_forming(df):

    if len(df) < 2:
        return None

    c1 = df.iloc[-2]
    c2 = df.iloc[-1]

    o1 = f(c1["Open"])
    c1c = f(c1["Close"])

    body1_high = max(o1, c1c)
    body1_low = min(o1, c1c)

    o2 = f(c2["Open"])
    c2c = f(c2["Close"])

    body2_high = max(o2, c2c)
    body2_low = min(o2, c2c)

    if (
        body2_high <= body1_high and
        body2_low >= body1_low
    ):

        if c1c < o1:
            return {
                "forming": True,
                "expected": "BullishHarami",
                "status": "AWAITING_CLOSE"
            }

        if c1c > o1:
            return {
                "forming": True,
                "expected": "BearishHarami",
                "status": "AWAITING_CLOSE"
            }

    return None
    
# =========================================================
# HARAMI STRENGTH
# =========================================================
def classify_harami_strength(c1, c2):

    o1 = f(c1["Open"])
    c1c = f(c1["Close"])

    o2 = f(c2["Open"])
    c2c = f(c2["Close"])

    body1 = abs(c1c - o1)
    body2 = abs(c2c - o2)

    ratio = body2 / max(body1, 1e-9)

    if ratio <= 0.30:
        return "STRONG"

    if ratio <= 0.60:
        return "WEAK"

    return "INVALID"
        
def detect_expansion_candle(df):
    prev = df.iloc[-2]
    curr = df.iloc[-1]

    body = abs(curr["Close"] - curr["Open"])
    prev_body = abs(prev["Close"] - prev["Open"])

    volume_spike = curr["Volume"] > prev["Volume"] * 2
    strong_move = body > prev_body * 1.5

    direction = "Bullish" if curr["Close"] > curr["Open"] else "Bearish"

    if volume_spike and strong_move:
        return {
            "detected": True,
            "type": direction,
            "strength": "Institutional Expansion"
        }

    return {"detected": False}

# =========================================================
# HARAMI MEMORY STATE
# =========================================================
def harami_state_memory(df):
    states = []

    for i in range(len(df)):
        if i < 1:
            states.append(False)
            continue

        window = df.iloc[i-1:i+1]  # correct 2-candle window
        res = detect_harami_pattern(window)

        states.append(res.get("detected", False))

    out = df.copy()
    out["harami_flag"] = states
    return out


# =========================================================
# ⭐ ACTIVE TRADE CHECK (UNCHANGED STRUCTURE)
# =========================================================
def detect_active_trade(today_star, yesterday_star, confirmation_state):

    if yesterday_star is None:
        return False

    if not isinstance(yesterday_star, dict):
        return False

    if not yesterday_star.get("detected", False):
        return False

    if yesterday_star.get("type") is None:
        return False

    if confirmation_state != "CONFIRMED":
        return False

    return True


# =========================================================
# ⭐ ACTIVE TRADE STATE (UNCHANGED STRUCTURE)
# =========================================================
def build_active_trade_state(harami):

    if not isinstance(harami, dict) or not harami.get("detected"):
        return None

    high = harami.get("high")
    low = harami.get("low")

    if high is None or low is None:
        return None

    rng = max(high - low, 1e-9)

    if harami["type"] == "BullishHarami":
        return {
            "direction": "LONG",
            "entry": high,
            "stop": low - (rng * 0.10),
            "target1": high + rng,
            "target2": high + (2 * rng)
        }

    if harami["type"] == "BearishHarami":
        return {
            "direction": "SHORT",
            "entry": low,
            "stop": high + (rng * 0.10),
            "target1": low - rng,
            "target2": low - (2 * rng)
        }

    return None


# =========================================================
# HARAMI TRADE PLAN
# =========================================================
def build_harami_trade_plan(
    harami,
    trend,
    sweep,
    structure,
    volume
):

    if not harami.get("detected"):

        return {
            "setup": "NO HARAMI",
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "interpretation": "No valid Harami pattern."
        }

    rng = harami["high"] - harami["low"]

    if harami["type"] == "BullishHarami":

        return {
            "setup": "BULLISH HARAMI REVERSAL",
            "entry": harami["high"],
            "stop": harami["low"],
            "target1": harami["high"] + rng,
            "target2": harami["high"] + (2 * rng),
            "interpretation": "Potential bullish reversal after selling exhaustion."
        }

    return {
        "setup": "BEARISH HARAMI REVERSAL",
        "entry": harami["low"],
        "stop": harami["high"],
        "target1": harami["low"] - rng,
        "target2": harami["low"] - (2 * rng),
        "interpretation": "Potential bearish reversal after buying exhaustion."
    }


# =========================================================
# TREND
# =========================================================
def evaluate_trend(df):
    if len(df) < 50:
        return {"trend": "Unknown", "score": 0}

    close = pd.to_numeric(df["Close"], errors="coerce").dropna()

    ema8_series = close.ewm(span=8).mean()
    ema21_series = close.ewm(span=21).mean()
    sma50_series = close.rolling(50).mean()

    ema8 = float(ema8_series.iloc[-1])
    ema21 = float(ema21_series.iloc[-1])
    sma50 = float(sma50_series.iloc[-1])

    if ema8 > ema21:
        trend_state = "Bullish"
    elif ema8 < ema21:
        trend_state = "Bearish"
    else:
        trend_state = "Neutral"

    if ema8 > ema21 and ema21 > sma50:
        return {"trend": "Bullish", "score": 15}
    if ema8 < ema21 and ema21 < sma50:
        return {"trend": "Bearish", "score": 15}

    return {"trend": trend_state, "score": 5}


# =========================================================
# LIQUIDITY SWEEP
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
# STRUCTURE
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
        "near_support": near_support,
        "near_resistance": near_resistance,
        "score": 15 if (near_support or near_resistance) else 0,
        "label": label,
        "zone": "Support" if near_support else "Resistance" if near_resistance else "Mid"
    }


# =========================================================
# VOLUME CONFIRMATION
# =========================================================
def volume_confirmation(df):
    volume = df["Volume"]
    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    rv = rvol(volume)
    spike = detect_volume_spike(volume)
    inst = institutional_accumulation_state(close, high, low, volume)

    expansion = detect_expansion_candle(df)

    confirmed = rv.iloc[-1] > 1.5 and spike.iloc[-1]

    score = 10 if confirmed else 0

    # 🔧 FIX: expansion adds institutional confirmation weight
    if expansion.get("detected"):
        score += 5

    return {
        "confirmed": confirmed,
        "rvol": round(rv.iloc[-1], 2),
        "institutional_state": str(inst.iloc[-1]),
        "expansion": expansion,
        "score": score
    }


# =========================================================
# FIBONACCI
# =========================================================
def evaluate_fibonacci(df):
    if len(df) < 50:
        return {"score": 0, "label": "No Data"}

    high = df["High"].tail(50).max()
    low = df["Low"].tail(50).min()
    close = df["Close"].iloc[-1]

    levels = [
        high - (high - low) * 0.382,
        high - (high - low) * 0.50,
        high - (high - low) * 0.618,
        high - (high - low) * 0.786
    ]

    for lvl in levels:
        if abs(close - lvl) / close < 0.01:
            return {"score": 5, "label": f"Aligned @ {round(lvl,2)}"}

    return {"score": 0, "label": "No Alignment"}

# =========================================================
# HARAMI STATUS
# =========================================================
def build_harami_status(df):

    if len(df) < 2:
        return {"state": "NONE"}

    detected = detect_harami_pattern(df.iloc[-2:])

    if detected.get("detected"):

        high = detected["high"]
        low = detected["low"]

        close = f(df.iloc[-1]["Close"])

        if detected["type"] == "BullishHarami":

            if close > high:
                state = "CONFIRMED"
            elif close < low:
                state = "FAILED"
            else:
                state = "PENDING"

        else:

            if close < low:
                state = "CONFIRMED"
            elif close > high:
                state = "FAILED"
            else:
                state = "PENDING"

        return {
            "state": state,
            "type": detected["type"],
            "strength": detected["strength"]
        }

    forming = detect_harami_forming(df.iloc[-2:])

    if forming:

        return {
            "state": "FORMING",
            "expected": forming["expected"]
        }

    return {
        "state": "NONE"
    }
    
# =========================================================
# HARAMI ANALYSIS ENGINE
# =========================================================
def analyze_harami_pattern(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    last2 = df.iloc[-2:].copy()

    harami = detect_harami_pattern(last2)
    status = build_harami_status(df)
    forming = detect_harami_forming(df.iloc[-2:])

    trend = evaluate_trend(df)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    volume = volume_confirmation(df)

    trade_plan = build_harami_trade_plan(
        harami,
        trend,
        sweep,
        structure,
        volume
    )

    return {
        "journal_prompt": format_harami_journal_prompt({
            "harami": harami,
            "status": status,
            "forming": forming,
            "trend": trend["trend"],
            "liquidity_sweep": sweep["sweep"],
            "structure": structure["label"],
            "volume": volume["confirmed"],
            "trade_plan": trade_plan,
            "candle_1": last2.iloc[0].to_dict(),
            "candle_2": last2.iloc[1].to_dict(),
        })
    }

def format_candle(candle, label="CANDLE"):
    return f"""
{label}:
- Date:   {candle.get('date')}
- Open:   {candle.get('Open')}
- High:   {candle.get('High')}
- Low:    {candle.get('Low')}
- Close:  {candle.get('Close')}
- Volume: {candle.get('Volume')}
"""

# =========================================================
# HARAMI FORMATTER
# =========================================================
def format_harami_journal_prompt(result):

    h = result.get("harami", {})
    s = result.get("status", {})
    tp = result.get("trade_plan", {})

    c1 = result.get("candle_1", {})
    c2 = result.get("candle_2", {})

    def fmt(c, label):
        return f"""
{label}:
- Open: {c.get('Open')}
- High: {c.get('High')}
- Low: {c.get('Low')}
- Close: {c.get('Close')}
- Volume: {c.get('Volume')}
"""

    status_block = f"""
- State: {s.get('state')}
- Type: {s.get('type')}
- Strength: {s.get('strength')}
"""

    return f"""
# ==================================================
📌 INSTITUTIONAL HARAMI PATTERN ANALYSIS
# ==================================================

HARAMI:
- Detected: {h.get('detected')}
- Type: {h.get('type')}
- Strength: {h.get('strength')}

{status_block}

--------------------------------------------------
📊 LAST 2 CANDLES

{fmt(c1, "CANDLE 1")}
{fmt(c2, "CANDLE 2")}

--------------------------------------------------
📊 CONTEXT
- Trend: {result.get('trend')}
- Sweep: {result.get('liquidity_sweep')}
- Structure: {result.get('structure')}
- Volume: {result.get('volume')}

--------------------------------------------------
🎯 TRADE PLAN
- Setup: {tp.get('setup')}
- Entry: {tp.get('entry')}
- Stop: {tp.get('stop')}
- Target1: {tp.get('target1')}
- Target2: {tp.get('target2')}

--------------------------------------------------
🧠 INTERPRETATION
{tp.get('interpretation')}
"""