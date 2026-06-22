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
# HARAMI DETECTION (STRICT BODY + STRUCTURE RULES)
# =========================================================
def detect_harami_pattern(df):

    if df is None or len(df) < 2:
        return {"detected": False}

    mother = df.iloc[-2]
    inside = df.iloc[-1]

    o1, c1 = f(mother["Open"]), f(mother["Close"])
    o2, c2 = f(inside["Open"]), f(inside["Close"])

    h1, l1 = f(mother["High"]), f(mother["Low"])
    h2, l2 = f(inside["High"]), f(inside["Low"])

    mother_body_high = max(o1, c1)
    mother_body_low = min(o1, c1)

    inside_body_high = max(o2, c2)
    inside_body_low = min(o2, c2)

    if not (
        inside_body_high <= mother_body_high and
        inside_body_low >= mother_body_low
    ):
        return {"detected": False}

    if c1 < o1:
        h_type = "BullishHarami"
    elif c1 > o1:
        h_type = "BearishHarami"
    else:
        return {"detected": False}

    return {
        "detected": True,
        "type": h_type,
        "high": h1,
        "low": l1,
        "body_high": mother_body_high,
        "body_low": mother_body_low,
        "inside_high": h2,
        "inside_low": l2,
    }


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

    if ratio <= 0.35:
        return "STRONG"
    if ratio <= 0.75:
        return "WEAK"

    return "WEAK"


# =========================================================
# EXPANSION CANDLE
# =========================================================
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
# ACTIVE TRADE CHECK
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
# ACTIVE TRADE STATE
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
def build_harami_trade_plan(harami, trend, sweep, structure, volume):

    if not harami or not harami.get("detected"):
        return _no_harami()

    state = harami.get("state", "NONE")
    h_type = harami.get("type")

    high = harami["high"]
    low = harami["low"]

    rng = max(high - low, 1e-9)

    if state == "PENDING":

        if h_type == "BullishHarami":
            return {
                "setup": "BULLISH HARAMI PENDING",
                "status": "PENDING_CONFIRMATION",
                "trigger": f"Close above {high}",
                "entry": high,
                "stop": low,
                "target1": high + rng,
                "target2": high + (2 * rng),
                "failure": f"Close below {low}",
                "interpretation": "Bullish Harami detected. Awaiting upside confirmation."
            }

        return {
            "setup": "BEARISH HARAMI PENDING",
            "status": "PENDING_CONFIRMATION",
            "trigger": f"Close below {low}",
            "entry": low,
            "stop": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": f"Close above {high}",
            "interpretation": "Bearish Harami detected. Awaiting downside confirmation."
        }

    if state == "CONFIRMED":

        if h_type == "BullishHarami":
            return {
                "setup": "BULLISH HARAMI CONFIRMED",
                "entry": high,
                "stop": low,
                "target1": high + rng,
                "target2": high + (2 * rng),
                "failure": f"Close below {low}",
                "interpretation": "Bullish breakout confirmed from Harami compression."
            }

        return {
            "setup": "BEARISH HARAMI CONFIRMED",
            "entry": low,
            "stop": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": f"Close above {high}",
            "interpretation": "Bearish breakdown confirmed from Harami compression."
        }

    if state == "FAILED":

        return {
            "setup": f"{h_type.upper()} FAILED",
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "failure": "Pattern invalidated",
            "interpretation": f"{h_type} failed before confirmation."
        }

    return _no_harami()


def _no_harami(msg="No valid Harami pattern."):
    return {
        "setup": "NO HARAMI",
        "entry": None,
        "stop": None,
        "target1": None,
        "target2": None,
        "interpretation": msg
    }


# =========================================================
# TREND
# =========================================================
def evaluate_trend(df):
    if len(df) < 50:
        return {"trend": "Unknown", "score": 0}

    close = pd.to_numeric(df["Close"], errors="coerce").dropna()

    ema8 = close.ewm(span=8).mean().iloc[-1]
    ema21 = close.ewm(span=21).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]

    if ema8 > ema21 and ema21 > sma50:
        return {"trend": "Bullish", "score": 15}
    if ema8 < ema21 and ema21 < sma50:
        return {"trend": "Bearish", "score": 15}

    return {"trend": "Neutral", "score": 5}


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

    return {
        "near_support": near_support,
        "near_resistance": near_resistance,
        "score": 15 if (near_support or near_resistance) else 0,
        "label": "Near Support" if near_support else "Near Resistance" if near_resistance else "Neutral",
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


def safe(v, default=0.0):
    return default if v is None else v


# =========================================================
# HARAMI STATUS
# =========================================================
def build_harami_status(df):

    if df is None or len(df) < 2:
        return empty_state()

    mother = df.iloc[-2]
    inside = df.iloc[-1]

    o1, c1 = f(mother["Open"]), f(mother["Close"])
    o2, c2 = f(inside["Open"]), f(inside["Close"])

    mother_high = max(o1, c1)
    mother_low = min(o1, c1)

    inside_high = max(o2, c2)
    inside_low = min(o2, c2)

    eps = abs(mother_high - mother_low) * 0.01 + 1e-9

    contained = (
        inside_high <= mother_high + eps and
        inside_low >= mother_low - eps
    )

    if not contained:
        return empty_state()

    h_type = "BullishHarami" if c1 < o1 else "BearishHarami" if c1 > o1 else None
    if h_type is None:
        return empty_state()

    if h_type == "BullishHarami":
        state = "CONFIRMED" if c2 > mother_high else "FAILED" if c2 < mother_low else "PENDING"
    else:
        state = "CONFIRMED" if c2 < mother_low else "FAILED" if c2 > mother_high else "PENDING"

    return {
        "today": {
            "detected": True,
            "type": h_type,
            "strength": classify_harami_strength(mother, inside),
            "compression_ratio": round(abs(c2 - o2) / max(abs(c1 - o1), 1e-9), 3),
            "high": mother_high,
            "low": mother_low,
            "range": mother_high - mother_low
        },
        "yesterday": {
            "detected": True,
            "state": state,
            "type": h_type,
            "strength": classify_harami_strength(mother, inside),
            "high": mother_high,
            "low": mother_low,
            "range": mother_high - mother_low
        }
    }


def empty_state():
    return {
        "today": {
            "detected": False,
            "type": None,
            "strength": None,
            "range": None,
            "high": None,
            "low": None
        },
        "yesterday": {
            "state": "NONE",
            "type": None,
            "strength": None,
            "range": None,
            "high": None,
            "low": None
        }
    }


# =========================================================
# ENGINE
# =========================================================
def analyze_harami_pattern(df):

    required_cols = {"Open", "High", "Low", "Close", "Volume"}

    if not required_cols.issubset(df.columns):
        df = normalize_ohlcv_columns(df)

    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    status = build_harami_status(df)

    active_harami = status["yesterday"]

    trend = evaluate_trend(df)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    volume = volume_confirmation(df)

    trade_plan = build_harami_trade_plan(
        active_harami,
        trend,
        sweep,
        structure,
        volume
    )

    return {
        "journal_prompt": format_harami_journal_prompt({
            "harami": status["today"],
            "status": status,
            "trade_plan": trade_plan
        })
    }


# =========================================================
# FORMATTERS
# =========================================================
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


def format_harami_journal_prompt(result):

    harami = result.get("harami", {})
    tp = result.get("trade_plan", {})

    base = f"""
# ==================================================
📌 HARAMI PATTERN ANALYSIS
# ==================================================

PATTERN:
- Detected: {harami.get('detected')}
- Type: {harami.get('type')}
- Strength: {harami.get('strength')}

--------------------------------------------------
🎯 TRADE SETUP
"""

    if tp.get("status") == "PENDING_CONFIRMATION":

        return base + f"""
- Setup: {tp.get('setup')}
- Trigger: {tp.get('trigger')}
- Entry: {tp.get('entry')}
- Stop: {tp.get('stop')}
- Target 1: {tp.get('target1')}
- Target 2: {tp.get('target2')}
- Failure Condition:
  {tp.get('failure')}

--------------------------------------------------
STATUS:
PENDING

--------------------------------------------------
INTERPRETATION:

{tp.get('interpretation')}
"""

    return base + f"""
- Setup: {tp.get('setup')}
- Entry: {tp.get('entry')}
- Stop: {tp.get('stop')}
- Target 1: {tp.get('target1')}
- Target 2: {tp.get('target2')}
- Failure:
  {tp.get('failure')}

--------------------------------------------------
STATUS:
{tp.get('setup')}

--------------------------------------------------
INTERPRETATION:

{tp.get('interpretation')}
"""