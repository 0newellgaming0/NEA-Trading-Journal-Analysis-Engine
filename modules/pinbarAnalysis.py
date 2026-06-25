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

    # -----------------------------------------------------
    # AUTO-DETECT TICKER FROM COLUMN NAMES
    # -----------------------------------------------------
    if ticker is None:
        for col in df.columns:
            if isinstance(col, str) and col.startswith("close_"):
                ticker = col.split("_")[-1]
                break

    if ticker is None:
        raise ValueError("Cannot detect ticker from dataframe columns")

    t = str(ticker).lower()

    # -----------------------------------------------------
    # SAFE COLUMN PICKER (NO SCALAR CONVERSION HERE)
    # -----------------------------------------------------
    def pick(col_name):
        if col_name in df.columns:
            return df[col_name]
        return pd.Series(np.nan, index=df.index)

    # -----------------------------------------------------
    # MAP OHLCV USING RAW COLUMN STRINGS (FIXED BUG)
    # -----------------------------------------------------
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
# PINBAR DETECTION (BULLISH + BEARISH)
# =========================================================
def detect_pinbar(data):

    if isinstance(data, pd.DataFrame):
        candle = data.iloc[-1]
    else:
        candle = data

    high = f(candle["High"])
    low = f(candle["Low"])
    open_ = f(candle["Open"])
    close = f(candle["Close"])

    rng = high - low

    base = {
        "high": high,
        "low": low,
        "open": open_,
        "close": close,
        "mid": (high + low) / 2
    }

    if rng <= 0:
        base.update({
            "detected": False,
            "type": None,
            "strength": "invalid range"
        })
        return base

    body = abs(close - open_)

    upper = high - max(open_, close)
    lower = min(open_, close) - low

    body_ratio = body / rng

    bull_ratio = lower / max(body, 1e-9)
    bear_ratio = upper / max(body, 1e-9)

    close_position = (close - low) / rng

    # =====================================================
    # BULLISH PINBAR
    # =====================================================
    bullish_pinbar = (
        bull_ratio >= 2.5 and
        close_position >= 0.70 and
        lower > upper and
        body_ratio <= 0.35
    )

    # =====================================================
    # BEARISH PINBAR
    # =====================================================
    bearish_pinbar = (
        bear_ratio >= 2.5 and
        close_position <= 0.30 and
        upper > lower and
        body_ratio <= 0.35
    )

    detected = bullish_pinbar or bearish_pinbar

    pin_type = None

    if bullish_pinbar:
        pin_type = "Bullish"

    elif bearish_pinbar:
        pin_type = "Bearish"

    # =====================================================
    # STRENGTH
    # =====================================================
    if bullish_pinbar:

        if bull_ratio >= 4:
            strength = "strong bullish pinbar"
        else:
            strength = "bullish pinbar"

    elif bearish_pinbar:

        if bear_ratio >= 4:
            strength = "strong bearish pinbar"
        else:
            strength = "bearish pinbar"

    else:

        strength = "no pinbar"

    base.update({
        "body": body,
        "upper_wick": upper,
        "lower_wick": lower,
        "range": rng,
        "body_ratio": body_ratio,

        "bull_ratio": round(bull_ratio, 2),
        "bear_ratio": round(bear_ratio, 2),

        "close_position": round(close_position, 3),

        "detected": detected,
        "type": pin_type,
        "strength": strength
    })

    return base

# =========================================================
# 🧠 NEW: PINBAR STATE MEMORY (CORE ADDITION)
# =========================================================
def pinbar_state_memory(df):

    states = []

    for _, row in df.iterrows():
        res = detect_pinbar(row)
        states.append(res["detected"])

    out = df.copy()
    out["pinbar_flag"] = states

    return out


# =========================================================
# 🧠 NEW: DETECT YESTERDAY PINBAR
# =========================================================
def detect_yesterday_pinbar(df):
    if len(df) < 2:
        return None

    return detect_pinbar(df.iloc[-2])

# =========================================================
# 🧠 NEW: CONFIRM TODAY AGAINST YESTERDAY PINBAR
# =========================================================
def confirm_pinbar_today(today_candle, y_pin):

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
    # BULLISH PINBAR
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
    # BEARISH PINBAR
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
        "label": label
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

    confirmed = rv.iloc[-1] > 1.5 and spike.iloc[-1]

    return {
        "confirmed": confirmed,
        "rvol": round(rv.iloc[-1], 2),
        "institutional_state": str(inst.iloc[-1]),
        "score": 10 if confirmed else 0
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
# 🧠 PINBAR STATE ENGINE (BOTH CANDLES ACTIVE)
# =========================================================
def analyze_pinbar(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    events, active_event = build_pinbar_event_state(df)

    active_trade = None
    if active_event and active_event.get("status") == "CONFIRMED":
        active_trade = build_active_trade_state(active_event)

    today_candle = df.iloc[-1]
    yesterday_candle = df.iloc[-2]

    today_pinbar = detect_pinbar(today_candle)

    yesterday_pinbar = active_event if active_event else detect_pinbar(df.iloc[-2])

    confirmation_state = (
        active_event["status"]
        if active_event else
        confirm_pinbar_today(today_candle, yesterday_pinbar)
    )

    trend = evaluate_trend(df)
    sweep = detect_liquidity_sweep(df)
    structure = evaluate_structure(df)
    volume = volume_confirmation(df)
    fib = evaluate_fibonacci(df)

    intent = (
        (10 if today_pinbar["detected"] else 0)
        + sweep["score"]
        + structure["score"]
    )

    confirm_score = (
        volume["score"]
        + trend["score"]
    )

    # =====================================================
    # 🟢 ACTIVE TRADE OVERRIDE (HIGHEST PRIORITY)
    # =====================================================

    if active_trade:

        regime = "ACTIVE_TRADE_MANAGEMENT"

        trade_plan = {
            "setup": "ACTIVE CONFIRMED TRADE",
            "entry": active_trade["entry"],
            "stop_close": active_trade["stop"],
            "stop_wick": active_trade["invalidation"],
            "target1": active_trade["target1"],
            "target2": active_trade["target2"],
            "failure": f"Invalidation at {active_trade['invalidation']}",
            "interpretation": "Trade is ACTIVE. Monitoring continuation or failure."
        }

        return {
            "journal_prompt": format_pinbar_journal_prompt({
                "today_pinbar": today_pinbar,
                "yesterday_pinbar": active_event,
                "confirmation_state": "CONFIRMED",
                "trend": trend["trend"],
                "liquidity_sweep": sweep["sweep"],
                "structure": structure["label"],
                "volume": volume["confirmed"],
                "institutional_state": volume["institutional_state"],
                "fibonacci": fib["label"],
                "intent": intent,
                "confirm_score": confirm_score,
                "context": fib["score"],
                "regime": regime,
                "trade_plan": trade_plan
            })
        }

    # =====================================================
    # CURRENT MARKET STATE FIRST (EVENT-DRIVEN REGIME)
    # =====================================================

    if active_event:

        status = active_event.get("status")

        if status == "CONFIRMED":
            regime = "INSTITUTIONAL_REVERSAL_CONTINUATION"

        elif status == "FAILED":
            regime = "LIQUIDITY_FAILURE_EVENT"

        elif status == "PENDING":
            regime = "PENDING_CONFIRMATION"

        elif status == "EXPIRED":
            regime = "NO_EDGE"

        else:
            regime = "NO_EDGE"

    elif yesterday_pinbar.get("detected"):

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

        elif confirmation_state == "PENDING":
            regime = "PENDING_CONFIRMATION"

        else:
            regime = "NO_EDGE"

    # =====================================================
    # TODAY FORMED A NEW PINBAR
    # =====================================================

    elif today_pinbar.get("detected"):
        regime = "NEW_PINBAR_FORMATION"

    # =====================================================
    # OLDER UNRESOLVED EVENT
    # =====================================================

    elif active_event:
        regime = "PENDING_CONFIRMATION"

    # =====================================================
    # NO CURRENT EVENT
    # =====================================================

    else:
        regime = "NO_EDGE"

    trade_plan = build_pinbar_trade_plan(
        today_pinbar,
        yesterday_pinbar,
        confirmation_state,
        trend["trend"],
        sweep["sweep"],
        structure["label"],
        volume["confirmed"]
    )

    return {
        "journal_prompt": format_pinbar_journal_prompt({
            "today_pinbar": today_pinbar,
            "yesterday_pinbar": yesterday_pinbar,
            "confirmation_state": confirmation_state,
            "trend": trend["trend"],
            "liquidity_sweep": sweep["sweep"],
            "structure": structure["label"],
            "volume": volume["confirmed"],
            "institutional_state": volume["institutional_state"],
            "fibonacci": fib["label"],
            "intent": intent,
            "confirm_score": confirm_score,
            "context": fib["score"],
            "regime": regime,
            "trade_plan": trade_plan
        })
    }

def build_pinbar_event_state(df, max_confirm_days=5):

    events = []
    active = None

    for i in range(len(df)):

        candle = df.iloc[i]
        detected = detect_pinbar(candle)

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

        close = f(candle["Close"])

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
        if active["status"] in (
            "CONFIRMED",
            "FAILED",
            "EXPIRED"
        ):
            events.append(active.copy())
            active = None

    return events, active
    
    
def detect_active_trade(today_pinbar, yesterday_pinbar, confirmation_state):

    if yesterday_pinbar is None:
        return False

    if not isinstance(yesterday_pinbar, dict):
        return False

    if not yesterday_pinbar.get("detected", False):
        return False

    if yesterday_pinbar.get("type") is None:
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
# INSTITUTIONAL PINBAR INTERPRETATION ENGINE
# =========================================================
def build_pinbar_trade_plan(today_pinbar,
                            yesterday_pinbar,
                            confirmation_state,
                            trend,
                            sweep,
                            structure,
                            volume):

    # =====================================================
    # 🚨 HARD BLOCK: FAILED STATE (NO TRADE ALLOWED)
    # =====================================================
    if confirmation_state == "FAILED":
        return {
            "setup": "FAILED PINBAR - NO TRADE",
            "entry": None,
            "stop_close": None,
            "stop_wick": None,
            "target1": None,
            "target2": None,
            "failure": "Pattern invalidated - trade canceled",
            "interpretation": (
                "Pinbar setup failed confirmation. "
                "No continuation or reversal trade is valid. "
                "Market has rejected the signal."
            )
        }

    # =====================================================
    # 🔥 FORCE ACTIVE EVENT STATE (CORE FIX)
    # =====================================================
    if yesterday_pinbar and yesterday_pinbar.get("detected"):

        if confirmation_state == "PENDING":

            return {
                "setup": "ACTIVE PENDING PINBAR EVENT",
                "entry": yesterday_pinbar["high"] if yesterday_pinbar["type"] == "Bullish" else yesterday_pinbar["low"],
                "stop_close": yesterday_pinbar["low"] if yesterday_pinbar["type"] == "Bullish" else yesterday_pinbar["high"],
                "stop_wick": yesterday_pinbar["low"] if yesterday_pinbar["type"] == "Bullish" else yesterday_pinbar["high"],
                "target1": None,
                "target2": None,
                "failure": "Waiting for breakout or breakdown",
                "interpretation": "Pinbar event is ACTIVE and unresolved. System is tracking continuation or failure."
            }

    # =====================================================
    # 🔥 ACTIVE TRADE MODE (FIX)
    # =====================================================
    active_trade = detect_active_trade(
        today_pinbar,
        yesterday_pinbar,
        confirmation_state
    )

    # =====================================================
    # SAFETY: NEVER ALLOW ACTIVE TRADE IN FAILED CONTEXT
    # =====================================================
    if confirmation_state != "CONFIRMED":
        active_trade = False

    # =====================================================
    # LIQUIDITY REJECTION STATE
    # =====================================================
    if (
        yesterday_pinbar
        and yesterday_pinbar.get("detected")
        and confirmation_state == "LIQUIDITY_REJECTION"
    ):

        pin_type = yesterday_pinbar["type"]
        high = yesterday_pinbar["high"]
        low = yesterday_pinbar["low"]

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
                    "Price traded above the bullish pinbar high "
                    "but failed to maintain acceptance. "
                    "Institutional liquidity was likely harvested "
                    "above resistance. Monitor for compression, retest, or reversal."
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
                    "Price traded below the bearish pinbar low "
                    "but failed to maintain acceptance. "
                    "Institutional liquidity was likely harvested "
                    "below support. Monitor for compression, retest, or reversal."
                )
            }

    # =====================================================
    # ACTIVE CONFIRMED TRADE
    # =====================================================
    if active_trade:

        trade = build_active_trade_state(yesterday_pinbar)

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
                    "Confirmed pinbar has transitioned into active trade state. "
                    "Price is now in execution phase, not formation phase."
                )
            }

    # =====================================================
    # BULLISH BREAK ATTEMPT
    # =====================================================
    if (
        yesterday_pinbar
        and yesterday_pinbar.get("detected")
        and confirmation_state == "BULLISH_BREAK_ATTEMPT"
    ):

        return {
            "setup": "BULLISH BREAK ATTEMPT",
            "entry": yesterday_pinbar["high"],
            "stop_close": yesterday_pinbar["low"],
            "stop_wick": yesterday_pinbar["low"],
            "target1": None,
            "target2": None,
            "failure": "Close below pinbar low",
            "interpretation": (
                "Price exceeded the bullish pinbar high and closed green, "
                "but failed to achieve acceptance above resistance."
            )
        }

    # =====================================================
    # BEARISH BREAK ATTEMPT
    # =====================================================
    if (
        yesterday_pinbar
        and yesterday_pinbar.get("detected")
        and confirmation_state == "BEARISH_BREAK_ATTEMPT"
    ):

        return {
            "setup": "BEARISH BREAK ATTEMPT",
            "entry": yesterday_pinbar["low"],
            "stop_close": yesterday_pinbar["high"],
            "stop_wick": yesterday_pinbar["high"],
            "target1": None,
            "target2": None,
            "failure": "Close above pinbar high",
            "interpretation": (
                "Price exceeded the bearish pinbar low and closed red, "
                "but failed to achieve acceptance below support."
            )
        }

    # =====================================================
    # FORMATION MODE (NO ACTIVE TRADE)
    # =====================================================
    if not today_pinbar.get("detected") and not yesterday_pinbar.get("detected"):

        return {
            "setup": "No Active Pin Bar",
            "entry": None,
            "stop_close": None,
            "stop_wick": None,
            "target1": None,
            "target2": None,
            "failure": None,
            "interpretation": "No active formation or execution state present."
        }

    # =====================================================
    # NORMAL FORMATION MODE
    # =====================================================
    pin_type = today_pinbar["type"]

    high = today_pinbar["high"]
    low = today_pinbar["low"]
    close = today_pinbar["close"]

    rng = high - low

    if pin_type == "Bullish":

        return {
            "setup": "FORMING BULLISH PINBAR",
            "entry": high,
            "stop_close": close - (rng * 0.10),
            "stop_wick": low,
            "target1": high + rng,
            "target2": high + (2 * rng),
            "failure": f"Failure below {low}",
            "interpretation": "Bullish rejection forming. Await confirmation or breakdown."
        }

    else:

        return {
            "setup": "FORMING BEARISH PINBAR",
            "entry": low,
            "stop_close": close + (rng * 0.10),
            "stop_wick": high,
            "target1": low - rng,
            "target2": low - (2 * rng),
            "failure": f"Failure above {high}",
            "interpretation": "Bearish rejection forming. Await confirmation or breakout."
        }
    
# =========================================================
# FORMATTER
# =========================================================
def format_pinbar_journal_prompt(result: dict):

    t = result.get("today_pinbar", {})
    y = result.get("yesterday_pinbar", {})
    state = result.get("confirmation_state", "NONE")
    tp = result.get("trade_plan", {})

    return f"""
# ==================================================
📌 INSTITUTIONAL PIN BAR ANALYSIS (CONFIRMATION MODEL)
# ==================================================

TODAY:
- Pinbar Detected: {t.get('detected')}
- Type: {t.get('type')}
- High: {t.get('high')}
- Low: {t.get('low')}

YESTERDAY:
- Pinbar Exists: {y.get('detected')}
- Type: {y.get('type')}
- Confirmation State: {state}

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

