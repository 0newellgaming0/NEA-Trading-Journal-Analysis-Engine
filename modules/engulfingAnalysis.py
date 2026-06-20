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
# ENGULFING DETECTION
# =========================================================
def detect_engulfing(data):

    if isinstance(data, pd.DataFrame):

        if len(data) < 2:
            return {
                "detected": False,
                "type": None,
                "strength": "None",
                "engulf_ratio": 0
            }

        prev = data.iloc[-2]
        curr = data.iloc[-1]

    else:
        raise ValueError("detect_engulfing() requires the last two candles")

    prev_open = f(prev["Open"])
    prev_close = f(prev["Close"])

    curr_open = f(curr["Open"])
    curr_close = f(curr["Close"])

    high = f(curr["High"])
    low = f(curr["Low"])

    prev_body = abs(prev_close - prev_open)
    curr_body = abs(curr_close - curr_open)

    base = {
        "high": high,
        "low": low,
        "open": curr_open,
        "close": curr_close,
        "detected": False,
        "type": None,
        "strength": "Weak",
        "engulf_ratio": 0
    }

    if prev_body <= 0 or curr_body <= 0:
        return base

    engulf_ratio = curr_body / prev_body

    # 🔧 FIX: filter micro/invalid engulfing
    if engulf_ratio < 1.2:
        return base

    if engulf_ratio >= 2.0:
        strength = "Institutional"
    elif engulf_ratio >= 1.5:
        strength = "Strong"
    else:
        strength = "Standard"

    bullish = (
        prev_close < prev_open and
        curr_close > curr_open and
        curr_open <= prev_close and
        curr_close >= prev_open
    )

    bearish = (
        prev_close > prev_open and
        curr_close < curr_open and
        curr_open >= prev_close and
        curr_close <= prev_open
    )

    if bullish:
        base.update({
            "detected": True,
            "type": "Bullish",
            "strength": strength,
            "engulf_ratio": round(engulf_ratio, 2)
        })

    elif bearish:
        base.update({
            "detected": True,
            "type": "Bearish",
            "strength": strength,
            "engulf_ratio": round(engulf_ratio, 2)
        })

    return base

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
# 🧠 NEW: ENGULFING STATE MEMORY (CORE ADDITION)
# =========================================================
def engulfing_state_memory(df):

    states = []

    for i in range(len(df)):

        if i == 0:
            states.append(False)
            continue

        res = detect_engulfing(df.iloc[i-1:i+1])
        states.append(res["detected"])

    out = df.copy()
    out["engulfing_flag"] = states

    return out


# =========================================================
# 🧠 NEW: DETECT YESTERDAY ENGULFING
# =========================================================
def detect_yesterday_engulfing(df):
    if len(df) < 2:
        return None

    return detect_engulfing(df.iloc[-2])

# =========================================================
# 🧠 NEW: CONFIRM TODAY AGAINST YESTERDAY ENGULFING
# =========================================================
def confirm_engulfing_today(today_candle, y_pin):

    if not y_pin or not y_pin.get("detected"):
        return "NONE"

    close = f(today_candle["Close"])
    open_ = f(today_candle["Open"])

    high = f(today_candle["High"])
    low = f(today_candle["Low"])

    y_high = y_pin["high"]
    y_low = y_pin["low"]

    if y_high == y_low:
        return "NONE"

    # =====================================================
    # BULLISH ENGULFING
    # =====================================================
    if y_pin["type"] == "Bullish":

        # ---------------------------------
        # CONFIRMED
        # ---------------------------------
        if close > y_high:
            return "CONFIRMED"

        # ---------------------------------
        # FAILED
        # ---------------------------------
        if close < y_low:
            return "FAILED"

        # ---------------------------------
        # HIGH BROKEN
        # GREEN CLOSE
        # NO ACCEPTANCE
        # ---------------------------------
        if (
            high > y_high
            and close > open_
            and close <= y_high
        ):
            return "BULLISH_BREAK_ATTEMPT"

        # ---------------------------------
        # HIGH BROKEN
        # RED CLOSE
        # REJECTION
        # ---------------------------------
        if (
            high > y_high
            and close < open_
            and close <= y_high
        ):
            return "LIQUIDITY_REJECTION"

        return "PENDING"

    # =====================================================
    # BEARISH ENGULFING
    # =====================================================
    if y_pin["type"] == "Bearish":

        # ---------------------------------
        # CONFIRMED
        # ---------------------------------
        if close < y_low:
            return "CONFIRMED"

        # ---------------------------------
        # FAILED
        # ---------------------------------
        if close > y_high:
            return "FAILED"

        # ---------------------------------
        # LOW BROKEN
        # RED CLOSE
        # NO ACCEPTANCE
        # ---------------------------------
        if (
            low < y_low
            and close < open_
            and close >= y_low
        ):
            return "BEARISH_BREAK_ATTEMPT"

        # ---------------------------------
        # LOW BROKEN
        # GREEN CLOSE
        # REJECTION
        # ---------------------------------
        if (
            low < y_low
            and close > open_
            and close >= y_low
        ):
            return "LIQUIDITY_REJECTION"

        return "PENDING"

    return "NONE"

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


# =========================================================
# 🧠 ENGULFING STATE ENGINE (BOTH CANDLES ACTIVE)
# =========================================================
def analyze_engulfing(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    today_candle = df.iloc[-1]
    yesterday_candle = df.iloc[-2]

    today_engulfing = detect_engulfing(df.iloc[-2:])
    yesterday_engulfing = detect_engulfing(df.iloc[-3:-1])

    confirmation_state = confirm_engulfing_today(
        today_candle,
        yesterday_engulfing
    )

    trend = evaluate_trend(df)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    volume = volume_confirmation(df)
    fib = evaluate_fibonacci(df)

    expansion = volume.get("expansion", {})

    intent = (
        (10 if today_engulfing["detected"] else 0)
        + sweep["score"]
        + structure["score"]
    )

    confirm_score = (
        volume["score"]
        + trend["score"]
        + (5 if expansion.get("detected") else 0)
    )

    events, active_event = build_engulfing_event_state(df)

    if yesterday_engulfing.get("detected"):

        if confirmation_state == "CONFIRMED":
            regime = "INSTITUTIONAL_REVERSAL_CONTINUATION"

        elif confirmation_state == "FAILED":
            regime = "LIQUIDITY_FAILURE_EVENT"

        elif confirmation_state == "LIQUIDITY_REJECTION":
            regime = "FAILED_BREAKOUT_REJECTION"

        elif confirmation_state == "BULLISH_BREAK_ATTEMPT":
            regime = "BULLISH_ACCEPTANCE_PROBE"

        elif confirmation_state == "BEARISH_BREAK_ATTEMPT":
            regime = "BEARISH_ACCEPTANCE_PROBE"

        else:
            regime = "PENDING_CONFIRMATION"

    elif today_engulfing.get("detected"):
        regime = "NEW_ENGULFING_FORMATION"

    elif active_event:
        regime = "PENDING_CONFIRMATION"

    else:
        regime = "NO_EDGE"

    trade_plan = build_engulfing_trade_plan(
        today_engulfing,
        yesterday_engulfing,
        confirmation_state,
        trend["trend"],
        sweep["sweep"],
        structure["label"],
        volume["confirmed"]
    )

    return {
        "journal_prompt": format_engulfing_journal_prompt({
            "today_engulfing": today_engulfing,
            "yesterday_engulfing": yesterday_engulfing,
            "confirmation_state": confirmation_state,
            "trend": trend["trend"],
            "liquidity_sweep": sweep["sweep"],
            "structure": structure["label"],
            "volume": volume["confirmed"],
            "institutional_state": volume["institutional_state"],
            "expansion": expansion,
            "fibonacci": fib["label"],
            "intent": intent,
            "confirm_score": confirm_score,
            "context": fib["score"],
            "regime": regime,
            "trade_plan": trade_plan,
            "today_candle": today_candle.to_dict(),
            "yesterday_candle": yesterday_candle.to_dict()
        })
    }

def build_engulfing_event_state(df, max_confirm_days=5):

    events = []
    active = None

    for i in range(len(df)):

        candle_window = df.iloc[max(0, i-1):i+1]
        detected = detect_engulfing(candle_window)

        # =====================================================
        # START NEW EVENT
        # =====================================================
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

        # =====================================================
        # NO ACTIVE EVENT
        # =====================================================
        if active is None:
            continue

        # =====================================================
        # DO NOT CONFIRM ON ORIGIN BAR
        # =====================================================
        if i <= active["start_index"]:
            continue

        close = f(candle_window.iloc[-1]["Close"])

        active["days_active"] = i - active["start_index"]

        # =====================================================
        # BULLISH EVENT
        # =====================================================
        if active["type"] == "Bullish":

            if close > active["high"]:
                active["status"] = "CONFIRMED"

            elif close < active["low"]:
                active["status"] = "FAILED"

        # =====================================================
        # BEARISH EVENT
        # =====================================================
        else:

            if close < active["low"]:
                active["status"] = "CONFIRMED"

            elif close > active["high"]:
                active["status"] = "FAILED"

        # =====================================================
        # TIME EXPIRATION
        # =====================================================
        if (
            active["status"] == "PENDING"
            and active["days_active"] >= max_confirm_days
        ):
            active["status"] = "EXPIRED"

        # =====================================================
        # CLOSE EVENT
        # =====================================================
        if active["status"] in ("CONFIRMED", "FAILED", "EXPIRED"):
            events.append(active.copy())
            active = None

    return events, active
    
    
def detect_active_trade(today_engulfing, yesterday_engulfing, confirmation_state):

    if yesterday_engulfing is None:
        return False

    if not isinstance(yesterday_engulfing, dict):
        return False

    if not yesterday_engulfing.get("detected", False):
        return False

    if yesterday_engulfing.get("type") is None:
        return False

    # 🔧 FIX: must be confirmed ONLY
    if confirmation_state != "CONFIRMED":
        return False

    return True
    
def build_active_trade_state(y_pin):

    if not y_pin or not y_pin.get("detected"):
        return None

    pin_type = y_pin["type"]
    high = y_pin["high"]
    low = y_pin["low"]

    rng = max(high - low, 1e-9)  # 🔧 FIX: prevents divide-by-zero instability

    if pin_type == "Bullish":

        return {
            "direction": "LONG",
            "entry": high,
            "stop": low - (rng * 0.10),
            "invalidation": low,
            "target1": high + rng,
            "target2": high + (2 * rng)
        }

    elif pin_type == "Bearish":

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
# INSTITUTIONAL ENGULFING INTERPRETATION ENGINE
# =========================================================
def build_engulfing_trade_plan(today_engulfing,
                            yesterday_engulfing,
                            confirmation_state,
                            trend,
                            sweep,
                            structure,
                            volume):

    # =====================================================
    # 🔥 FORCE ACTIVE EVENT STATE (CORE FIX)
    # =====================================================
    if yesterday_engulfing and yesterday_engulfing.get("detected"):

        if confirmation_state == "PENDING":

            return {
                "setup": "ACTIVE PENDING ENGULFING EVENT",
                "entry": yesterday_engulfing["high"] if yesterday_engulfing["type"] == "Bullish" else yesterday_engulfing["low"],
                "stop_close": yesterday_engulfing["low"] if yesterday_engulfing["type"] == "Bullish" else yesterday_engulfing["high"],
                "stop_wick": yesterday_engulfing["low"] if yesterday_engulfing["type"] == "Bullish" else yesterday_engulfing["high"],
                "target1": None,
                "target2": None,
                "failure": "Waiting for breakout or breakdown",
                "interpretation": "Engulfing event is ACTIVE and unresolved. System is tracking continuation or failure."
            }
        
    # =====================================================
    # 🔥 ACTIVE TRADE MODE (FIX)
    # =====================================================
    active_trade = detect_active_trade(
        today_engulfing,
        yesterday_engulfing,
        confirmation_state
    )

    # =====================================================
    # LIQUIDITY REJECTION STATE
    # =====================================================
    if (
        yesterday_engulfing
        and yesterday_engulfing.get("detected")
        and confirmation_state == "LIQUIDITY_REJECTION"
    ):

        pin_type = yesterday_engulfing["type"]

        high = yesterday_engulfing["high"]
        low = yesterday_engulfing["low"]

        rng = high - low

        if pin_type == "Bullish":

            return {
                "setup": "FAILED BULLISH BREAKOUT",
                "entry": high,
                "stop_close": low,
                "stop_wick": low,
                "target1": None,
                "target2": None,
                "failure": f"Close below {low}",
                "interpretation": (
                    "Price traded above the bullish engulfing high "
                    "but failed to maintain acceptance. "
                    "Institutional liquidity was likely harvested "
                    "above resistance. Monitor for compression, "
                    "retest, or reversal."
                )
            }

        else:

            return {
                "setup": "FAILED BEARISH BREAKDOWN",
                "entry": low,
                "stop_close": high,
                "stop_wick": high,
                "target1": None,
                "target2": None,
                "failure": f"Close above {high}",
                "interpretation": (
                    "Price traded below the bearish engulfing low "
                    "but failed to maintain acceptance. "
                    "Institutional liquidity was likely harvested "
                    "below support. Monitor for compression, "
                    "retest, or reversal."
                )
            }
            
    if active_trade:

        trade = build_active_trade_state(yesterday_engulfing)

        if trade:
            return {
                "setup": "ACTIVE CONFIRMED TRADE",
                "entry": trade["entry"],
                "stop_close": trade["stop"],
                "stop_wick": trade["invalidation"],
                "target1": trade["target1"],
                "target2": trade["target2"],
                "failure": f"Invalidation at {trade['invalidation']}",
                "interpretation": (
                    "Confirmed engulfing has transitioned into active trade state. "
                    "Price is now in execution phase, not formation phase."
                )
            }

    # =====================================================
    # BULLISH BREAK ATTEMPT
    # =====================================================
    if (
        yesterday_engulfing
        and yesterday_engulfing.get("detected")
        and confirmation_state == "BULLISH_BREAK_ATTEMPT"
    ):

        return {
            "setup": "BULLISH BREAK ATTEMPT",
            "entry": yesterday_engulfing["high"],
            "stop_close": yesterday_engulfing["low"],
            "stop_wick": yesterday_engulfing["low"],
            "target1": None,
            "target2": None,
            "failure": "Close below engulfing low",
            "interpretation": (
                "Price exceeded the bullish engulfing high and "
                "closed green, but failed to achieve acceptance "
                "above resistance. Buyers remain active but "
                "confirmation has not yet occurred."
            )
        }

    # =====================================================
    # BEARISH BREAK ATTEMPT
    # =====================================================
    if (
        yesterday_engulfing
        and yesterday_engulfing.get("detected")
        and confirmation_state == "BEARISH_BREAK_ATTEMPT"
    ):

        return {
            "setup": "BEARISH BREAK ATTEMPT",
            "entry": yesterday_engulfing["low"],
            "stop_close": yesterday_engulfing["high"],
            "stop_wick": yesterday_engulfing["high"],
            "target1": None,
            "target2": None,
            "failure": "Close above engulfing high",
            "interpretation": (
                "Price exceeded the bearish engulfing low and "
                "closed red, but failed to achieve acceptance "
                "below support. Sellers remain active but "
                "confirmation has not yet occurred."
            )
        }
    # =====================================================
    # 📊 FORMATION MODE (NO ACTIVE TRADE)
    # =====================================================
    if not today_engulfing.get("detected") and not yesterday_engulfing.get("detected"):

        return {
            "setup": "No Active Engulfing Bar",
            "entry": None,
            "stop_close": None,
            "stop_wick": None,
            "target1": None,
            "target2": None,
            "failure": None,
            "interpretation": (
                "No active formation or execution state present."
            )
        }

    # =====================================================
    # NORMAL ENGULFING MODE (TODAY FORMING)
    # =====================================================
    pin_type = today_engulfing["type"]

    high = today_engulfing["high"]
    low = today_engulfing["low"]
    close = today_engulfing["close"]

    rng = high - low

    if pin_type == "Bullish":

        return {
            "setup": "FORMING BULLISH ENGULFING",
            "entry": high,
            "stop_close": close - (rng * 0.10),
            "stop_wick": low,
            "target1": high + rng,
            "target2": high + (2 * rng),
            "failure": f"Failure below {low}",
            "interpretation": (
                "Bullish rejection forming. Await confirmation or breakdown."
            )
        }

    else:

        return {
            "setup": "FORMING BEARISH ENGULFING",
            "entry": low,
            "stop_close": close + (rng * 0.10),
            "stop_wick": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": f"Failure above {high}",
            "interpretation": (
                "Bearish rejection forming. Await confirmation or breakout."
            )
        }
    
# =========================================================
# FORMATTER
# =========================================================
def format_engulfing_journal_prompt(result: dict):

    t = result.get("today_engulfing", {})
    y = result.get("yesterday_engulfing", {})
    state = result.get("confirmation_state", "NONE")
    tp = result.get("trade_plan", {})
    today_candle = result.get("today_candle", {})
    yesterday_candle = result.get("yesterday_candle", {})

    return f"""
# ==================================================
📌 INSTITUTIONAL ENGULFING PATTERN ANALYSIS (CONFIRMATION MODEL)
# ==================================================

TODAY:
- Engulfing Detected: {t.get('detected')}
- Type: {t.get('type')}

📈 RAW CANDLE DATA:
- Open: {today_candle.get('Open')}
- High: {today_candle.get('High')}
- Low: {today_candle.get('Low')}
- Close: {today_candle.get('Close')}
- Volume: {today_candle.get('Volume')}

YESTERDAY:
- Engulfing Exists: {y.get('detected')}
- Type: {y.get('type')}
- Confirmation State: {state}

📈 RAW CANDLE DATA:
- Open: {yesterday_candle.get('Open')}
- High: {yesterday_candle.get('High')}
- Low: {yesterday_candle.get('Low')}
- Close: {yesterday_candle.get('Close')}
- Volume: {yesterday_candle.get('Volume')}

--------------------------------------------------
📊 CONTEXT:
- Trend: {result.get('trend')}
- Sweep: {result.get('liquidity_sweep')}
- Structure: {result.get('structure')}
- Volume: {result.get('volume')}
- Institutional State: {result.get('institutional_state')}
- Fibonacci: {result.get('fibonacci')}

--------------------------------------------------
⚠️ REGIME:
- {result.get('regime')}

--------------------------------------------------
🎯 TRADE PLAN

- Setup Quality:  {tp.get('setup')}
- Entry Trigger:  {tp.get('entry')}
- Aggressive Stop:  {tp.get('stop_close')}
- Conservative Stop:  {tp.get('stop_wick')}
- Target 1:  {tp.get('target1')}
- Target 2:  {tp.get('target2')}

- Failure Condition:
  {tp.get('failure')}

--------------------------------------------------
🧠 INTERPRETATION

{tp.get('interpretation')}

--------------------------------------------------
🧭 STATES:
CONFIRMED → continuation
FAILED → reversal
PENDING → waiting next candle
"""

