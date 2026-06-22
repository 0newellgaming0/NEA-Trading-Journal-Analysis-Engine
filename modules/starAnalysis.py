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
# STAR CENTER CANDLE CLASSIFIER
# =========================================================
def classify_star_center_candle(candle):

    o = f(candle["Open"])
    h = f(candle["High"])
    l = f(candle["Low"])
    c = f(candle["Close"])

    rng = max(h - l, 1e-9)
    body = abs(c - o)

    body_pct = body / rng

    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    wick_balance = (
        min(upper_wick, lower_wick)
        / max(max(upper_wick, lower_wick), 1e-9)
    )

    if body_pct <= 0.10:
        return {
            "type": "Doji",
            "strength": "Strong"
        }

    if body_pct <= 0.30 and wick_balance >= 0.50:
        return {
            "type": "Spinning Top",
            "strength": "Strong"
        }

    if body_pct <= 0.35:
        return {
            "type": "Small Body",
            "strength": "Weak"
        }

    return {
        "type": "Directional Candle",
        "strength": "Invalid"
    }
    
# =========================================================
# ⭐ STAR DETECTION (FIXED TRUE MORNING/EVENING STAR LOGIC)
# =========================================================
def detect_star_pattern(df):

    if len(df) < 3:
        return {"detected": False, "type": None}

    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]

    o1, h1, l1, cl1 = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
    o2, h2, l2, cl2 = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    o3, h3, l3, cl3 = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])

    center = classify_star_center_candle(c2)

    if center["strength"] == "Invalid":
        return {"detected": False, "type": None}

    midpoint1 = (o1 + cl1) / 2

    candle1_body = cl1 - o1

    # =====================================================
    # MORNING STAR (TRUE STRUCTURE)
    # =====================================================
    bullish = (
        candle1_body < 0 and
        center["type"] in ("Doji", "Spinning Top", "Small Body") and
        cl3 > midpoint1 and
        cl3 > o1
    )

    # =====================================================
    # EVENING STAR (TRUE STRUCTURE)
    # =====================================================
    bearish = (
        candle1_body > 0 and
        center["type"] in ("Doji", "Spinning Top", "Small Body") and
        cl3 < midpoint1 and
        cl3 < o1
    )

    if bullish:
        return {
            "detected": True,
            "type": "MorningStar",
            "strength": "VALID",
            "center_type": center["type"],
            "high": h3,
            "low": l3,
            "close": cl3
        }

    if bearish:
        return {
            "detected": True,
            "type": "EveningStar",
            "strength": "VALID",
            "center_type": center["type"],
            "high": h3,
            "low": l3,
            "close": cl3
        }

    return {"detected": False, "type": None}


# =========================================================
# STAR FORMING (FIXED STRICTER FILTER)
# =========================================================
def detect_star_forming(df):

    if len(df) < 2:
        return None

    c1, c2 = df.iloc[-2], df.iloc[-1]

    o1, h1, l1, cl1 = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
    o2, h2, l2 = f(c2["Open"]), f(c2["High"]), f(c2["Low"])

    center = classify_star_center_candle(c2)

    if center["strength"] == "Invalid":
        return None

    bearish_first = cl1 < o1
    bullish_first = cl1 > o1

    # stricter forming validation
    if bearish_first and (o2 < cl1 and l2 <= h1):
        return {
            "forming": True,
            "expected": "MorningStar",
            "center_type": center["type"],
            "status": "AWAITING_CANDLE_3"
        }

    if bullish_first and (o2 > cl1 and h2 >= l1):
        return {
            "forming": True,
            "expected": "EveningStar",
            "center_type": center["type"],
            "status": "AWAITING_CANDLE_3"
        }

    return None


# =========================================================
# STAR STRENGTH (UNCHANGED LOGIC OK)
# =========================================================
def classify_star_strength(c1, c2, c3):

    o1, h1, l1, c1c = f(c1["Open"]), f(c1["High"]), f(c1["Low"]), f(c1["Close"])
    o2, h2, l2, c2c = f(c2["Open"]), f(c2["High"]), f(c2["Low"]), f(c2["Close"])
    o3, h3, l3, c3c = f(c3["Open"]), f(c3["High"]), f(c3["Low"]), f(c3["Close"])

    body2 = abs(c2c - o2)
    range2 = max(h2 - l2, 1e-9)

    body_ratio = body2 / range2

    left_drop = abs(c1c - o1)
    right_rise = abs(c3c - o3)

    symmetry = min(left_drop, right_rise) / (max(left_drop, right_rise) + 1e-9)

    if body_ratio <= 0.20 and symmetry > 0.7:
        return "STRONG"
    elif body_ratio <= 0.35:
        return "WEAK"
    else:
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
# ⭐ STAR MEMORY (PRESERVED EVENT STRUCTURE)
# =========================================================
def star_state_memory(df):
    states = []

    for i in range(len(df)):
        if i < 2:
            states.append(False)
            continue

        res = detect_star_pattern(df.iloc[i-2:i+1])
        states.append(res["detected"])

    out = df.copy()
    out["star_flag"] = states
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
def build_active_trade_state(y_pin):

    if not y_pin or not y_pin.get("detected"):
        return None

    pin_type = y_pin["type"]
    high = y_pin["high"]
    low = y_pin["low"]

    rng = max(high - low, 1e-9)

    if pin_type == "MorningStar":

        return {
            "direction": "LONG",
            "entry": high,
            "stop": low - (rng * 0.10),
            "invalidation": low,
            "target1": high + rng,
            "target2": high + (2 * rng)
        }

    elif pin_type == "EveningStar":

        return {
            "direction": "SHORT",
            "entry": low,
            "stop": high + (rng * 0.10),
            "invalidation": high,
            "target1": low - rng,
            "target2": low - (2 * rng)
        }

    return None


# =========================================================
# ⭐ STAR EVENT PERSISTENCE (FIXED CORE ADDITION)
# =========================================================
def build_star_event_state(df, max_confirm_days=5):

    events = []
    active = None

    for i in range(len(df)):

        window = df.iloc[max(0, i-2):i+1]
        detected = detect_star_pattern(window)

        if active is None and detected["detected"]:
            active = {
                "start_index": i,
                "type": detected["type"],
                "high": detected["high"],
                "low": detected["low"],
                "status": "PENDING",
                "days_active": 0
            }
            continue

        if active is None:
            continue

        if i <= active["start_index"]:
            continue

        close = f(df.iloc[i]["Close"])
        active["days_active"] = i - active["start_index"]

        if active["type"] == "MorningStar":
            if close > active["high"]:
                active["status"] = "CONFIRMED"
            elif close < active["low"]:
                active["status"] = "FAILED"

        else:
            if close < active["low"]:
                active["status"] = "CONFIRMED"
            elif close > active["high"]:
                active["status"] = "FAILED"

        if active["status"] == "PENDING" and active["days_active"] >= max_confirm_days:
            active["status"] = "EXPIRED"

        if active["status"] in ("CONFIRMED", "FAILED", "EXPIRED"):
            events.append(active.copy())
            active = None

    return events, active


# =========================================================
# ⭐ TRADE PLAN (UNCHANGED STRUCTURE)
# =========================================================
def build_star_trade_plan(star, trend, sweep, structure, volume):

    if not star or not star.get("detected"):
        return {
            "setup": "NO STAR",
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "interpretation": "No valid star pattern."
        }

    rng = star["high"] - star["low"]

    # =====================================================
    # INSTITUTIONAL CONTEXT SCORING (ADDED FIX)
    # =====================================================
    quality_score = 0

    if sweep and sweep.get("sweep"):
        quality_score += 1

    if structure and (structure.get("near_support") or structure.get("near_resistance")):
        quality_score += 1

    if volume and volume.get("confirmed"):
        quality_score += 1

    trend_dir = trend.get("trend")

    # =====================================================
    # MORNING STAR
    # =====================================================
    if star["type"] == "MorningStar":
        entry = star["high"]
        stop = star["low"]

        base_setup = "MORNING STAR REVERSAL"

        if trend_dir == "Bearish":
            setup = base_setup
            interpretation = "Bullish reversal after exhaustion."
        else:
            setup = base_setup + " (COUNTER-TREND)"
            interpretation = "Bullish reversal forming against trend."

        # ENHANCED CONTEXT LABEL
        if quality_score == 3:
            interpretation = "HIGH QUALITY institutional reversal (sweep + structure + volume alignment). " + interpretation
        elif quality_score == 2:
            interpretation = "MODERATE quality setup with partial institutional confirmation. " + interpretation

        return {
            "setup": setup,
            "entry": entry,
            "stop": stop,
            "target1": entry + rng,
            "target2": entry + (2 * rng),
            "interpretation": interpretation
        }

    # =====================================================
    # EVENING STAR
    # =====================================================
    if star["type"] == "EveningStar":
        entry = star["low"]
        stop = star["high"]

        base_setup = "EVENING STAR REVERSAL"

        if trend_dir == "Bullish":
            setup = base_setup
            interpretation = "Bearish reversal after exhaustion."
        else:
            setup = base_setup + " (COUNTER-TREND)"
            interpretation = "Bearish reversal forming against trend."

        # ENHANCED CONTEXT LABEL
        if quality_score == 3:
            interpretation = "HIGH QUALITY institutional reversal (sweep + structure + volume alignment). " + interpretation
        elif quality_score == 2:
            interpretation = "MODERATE quality setup with partial institutional confirmation. " + interpretation

        return {
            "setup": setup,
            "entry": entry,
            "stop": stop,
            "target1": entry - rng,
            "target2": entry - (2 * rng),
            "interpretation": interpretation
        }

    return {
        "setup": "NO STAR",
        "entry": None,
        "stop": None,
        "target1": None,
        "target2": None,
        "interpretation": "No valid star pattern."
    }


# =========================================================
# TREND
# =========================================================
def evaluate_trend(df):
    if len(df) < 50:
        return {"trend": "Unknown", "score": 0}

    close = pd.to_numeric(df["Close"], errors="coerce").dropna()

    ema8 = f(close.ewm(span=8).mean().iloc[-1])
    ema21 = f(close.ewm(span=21).mean().iloc[-1])
    sma50 = f(close.rolling(50).mean().iloc[-1])

    # -----------------------------
    # FIX: less rigid classification
    # -----------------------------
    if ema8 > ema21:
        trend_state = "Bullish"
    elif ema8 < ema21:
        trend_state = "Bearish"
    else:
        trend_state = "Neutral"

    # score remains unchanged (keeps compatibility)
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

def build_star_status(df):

    if len(df) < 3:
        return {"state": "NONE"}

    detected = detect_star_pattern(df.iloc[-3:])

    if detected.get("detected"):

        high = detected["high"]
        low = detected["low"]
        close = f(df.iloc[-1]["Close"])

        if detected["type"] == "MorningStar":
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
            "strength": detected["strength"],
            "center_type": detected["center_type"]
        }

    forming = detect_star_forming(df.iloc[-2:])

    if forming:
        return {
            "state": "FORMING",
            "expected": forming["expected"],
            "center_type": forming["center_type"]
        }

    return {"state": "NONE"}
    
# =========================================================
# ⭐ STAR ANALYSIS ENGINE (FIXED + EVENT TRACKING + 3 BAR OUTPUT)
# =========================================================
def analyze_star_pattern(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 3:
        return {"journal_prompt": "Insufficient data"}

    last3 = df.iloc[-3:].copy()

    today_star = detect_star_pattern(last3)
    star_status = build_star_status(df)
    forming_pattern = detect_star_forming(df.iloc[-2:])

    trend = evaluate_trend(df)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    volume = volume_confirmation(df)

    regime = "STAR_ACTIVE" if today_star.get("detected") else "NO_EDGE"

    trade_plan = build_star_trade_plan(
        today_star,
        trend,
        sweep,
        structure,
        volume
    )

    return {
        "journal_prompt": format_star_journal_prompt({
            "today_star": today_star,
            "star_status": star_status,
            "forming_pattern": forming_pattern,
            "trend": trend["trend"],
            "liquidity_sweep": sweep["sweep"],
            "structure": structure["label"],
            "volume": volume["confirmed"],
            "regime": regime,
            "trade_plan": trade_plan,
            "candle_1": last3.iloc[0].to_dict(),
            "candle_2": last3.iloc[1].to_dict(),
            "candle_3": last3.iloc[2].to_dict(),
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
# ⭐ FORMATTER (FIXED: NOW SHOWS LAST 3 CANDLES)
# =========================================================
def format_star_journal_prompt(result):

    t = result.get("today_star", {})
    s = result.get("star_status", {})
    tp = result.get("trade_plan", {})

    c1 = format_candle(result.get("candle_1", {}), "CANDLE 1")
    c2 = format_candle(result.get("candle_2", {}), "CANDLE 2")
    c3 = format_candle(result.get("candle_3", {}), "CANDLE 3")

    status_block = ""

    if s.get("state") == "FORMING":

        status_block = f"""
- Status: FORMING
- Expected Pattern: {s.get('expected')}
- Center Candle: {s.get('center_type')}
- Confirmation: Awaiting Candle 3
"""

    elif s.get("state") in ("PENDING", "CONFIRMED", "FAILED", "EXPIRED"):

        status_block = f"""
- Status: {s.get('state')}
- Type: {s.get('type')}
- Strength: {s.get('strength')}
- Center Candle: {s.get('center_type')}
"""

    else:

        status_block = """
- Status: NONE
"""

    return f"""
# ==================================================
📌 INSTITUTIONAL STAR PATTERN ANALYSIS (CONFIRMATION MODEL)
# ==================================================

STAR:
- Detected: {t.get('detected')}
- Type: {t.get('type')}
- Strength: {t.get('strength')}
{status_block}

--------------------------------------------------
📊 LAST 3 CANDLES (RAW)

{c1}
{c2}
{c3}

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