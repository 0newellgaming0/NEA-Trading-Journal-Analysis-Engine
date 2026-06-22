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
# TREND HELPER
# =========================================================
def get_trend(df, lookback=5):
    if df is None or len(df) < lookback + 1:
        return "UNKNOWN"

    closes = df["Close"].iloc[-lookback:]
    prior = df["Close"].iloc[-(lookback * 2):-lookback]

    if closes.mean() > prior.mean():
        return "UPTREND"
    elif closes.mean() < prior.mean():
        return "DOWNTREND"
    return "RANGE"


# =========================================================
# HAMMER DETECTION ENGINE
# =========================================================
def detect_hammer(
    df,
    strict_wick_ratio=2.0,
    strict_body_threshold=0.35,
    lazy_wick_ratio=1.25,
    lazy_body_threshold=0.55
):

    if df is None or len(df) < 1:
        return {"detected": False}

    candle = df.iloc[-1]

    o = f(candle.get("Open"))
    h = f(candle.get("High"))
    l = f(candle.get("Low"))
    c = f(candle.get("Close"))

    rng = max(h - l, 1e-9)
    body = abs(c - o)

    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)

    body_pct = body / rng
    wick_ratio_actual = lower_wick / max(body, 1e-9)

    # =====================================================
    # STRICT HAMMER RULES (UPDATED PER YOUR SPEC)
    # =====================================================

    strict_lower_wick = lower_wick >= 2 * body
    strict_upper_wick = upper_wick <= 0.25 * rng

    strict_hammer = (
        strict_lower_wick and
        strict_upper_wick
    )

    lazy_small_body = body_pct <= lazy_body_threshold
    lazy_lower_wick = wick_ratio_actual >= lazy_wick_ratio
    lazy_upper_wick = upper_wick <= body

    lazy_hammer = (
        lazy_small_body
        and lazy_lower_wick
        and lazy_upper_wick
    )

    hammer_class = None
    detected = False

    if strict_hammer:
        detected = True
        hammer_class = "INSTITUTIONAL_HAMMER"
    elif lazy_hammer:
        detected = True
        hammer_class = "LAZY_HAMMER"

    return {
        "detected": detected,
        "classification": hammer_class,
        "type": "Hammer",

        "open": o,
        "high": h,
        "low": l,
        "close": c,

        "body": round(body, 4),
        "range": round(rng, 4),

        "lower_wick": round(lower_wick, 4),
        "upper_wick": round(upper_wick, 4),

        "body_pct": round(body_pct, 4),
        "wick_ratio": round(wick_ratio_actual, 3),

        "strict_hammer": strict_hammer,
        "lazy_hammer": lazy_hammer,

        "location": "Potential Liquidity Sweep Zone",

        "entry": h,
        "stop": l,
        "target1": round(h + rng, 4),
        "target2": round(h + (2 * rng), 4),
        "range_size": rng
    }


# =========================================================
# SHOOTING STAR DETECTION ENGINE
# =========================================================
def detect_shooting_star(
    df,
    strict_wick_ratio=2.5,
    strict_body_threshold=0.35,
    lazy_wick_ratio=1.25,
    lazy_body_threshold=0.55
):

    if df is None or len(df) < 1:
        return {"detected": False}

    candle = df.iloc[-1]

    o = f(candle.get("Open"))
    h = f(candle.get("High"))
    l = f(candle.get("Low"))
    c = f(candle.get("Close"))

    rng = max(h - l, 1e-9)
    body = abs(c - o)

    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    body_pct = body / rng
    wick_ratio_actual = upper_wick / max(body, 1e-9)

    strict = (
        body_pct <= strict_body_threshold
        and wick_ratio_actual >= strict_wick_ratio
        and lower_wick <= body * 0.6
    )

    lazy = (
        body_pct <= lazy_body_threshold
        and wick_ratio_actual >= lazy_wick_ratio
        and lower_wick <= body
    )

    detected = strict or lazy

    return {
        "detected": detected,
        "classification": (
            "INSTITUTIONAL_SHOOTING_STAR" if strict else
            "LAZY_SHOOTING_STAR" if lazy else None
        ),
        "type": "ShootingStar",

        "open": o,
        "high": h,
        "low": l,
        "close": c,

        "body": round(body, 4),
        "range": round(rng, 4),
        "upper_wick": round(upper_wick, 4),
        "lower_wick": round(lower_wick, 4),
        "body_pct": round(body_pct, 4),
        "wick_ratio": round(wick_ratio_actual, 3),

        "location": "Potential Distribution Sweep Zone",

        # TRADE STRUCTURE LOCK
        "entry": l,
        "stop": h,
        "target1": round(l - rng, 4),
        "target2": round(l - (2 * rng), 4),
        "range_size": rng
    }


# =========================================================
# INVERTED HAMMER DETECTION
# =========================================================
def detect_inverted_hammer(
    df,
    strict_wick_ratio=2.5,
    strict_body_threshold=0.35,
    lazy_wick_ratio=1.25,
    lazy_body_threshold=0.55
):

    if df is None or len(df) < 1:
        return {"detected": False}

    candle = df.iloc[-1]

    o = f(candle.get("Open"))
    h = f(candle.get("High"))
    l = f(candle.get("Low"))
    c = f(candle.get("Close"))

    rng = max(h - l, 1e-9)
    body = abs(c - o)

    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l

    body_pct = body / rng
    wick_ratio_actual = upper_wick / max(body, 1e-9)

    strict_small_body = body_pct <= strict_body_threshold
    strict_upper_wick = wick_ratio_actual >= strict_wick_ratio
    strict_lower_wick = lower_wick <= body * 0.60

    lazy_small_body = body_pct <= lazy_body_threshold
    lazy_upper_wick = wick_ratio_actual >= lazy_wick_ratio
    lazy_lower_wick = lower_wick <= body

    strict = (
        strict_small_body
        and strict_upper_wick
        and strict_lower_wick
    )

    lazy = (
        lazy_small_body
        and lazy_upper_wick
        and lazy_lower_wick
    )

    detected = strict or lazy

    return {
        "detected": detected,
        "classification": (
            "INSTITUTIONAL_INVERTED_HAMMER" if strict else
            "LAZY_INVERTED_HAMMER" if lazy else None
        ),
        "type": "InvertedHammer",

        "open": o,
        "high": h,
        "low": l,
        "close": c,

        "body": round(body, 4),
        "range": round(rng, 4),
        "upper_wick": round(upper_wick, 4),
        "lower_wick": round(lower_wick, 4),
        "body_pct": round(body_pct, 4),
        "wick_ratio": round(wick_ratio_actual, 3),

        "entry": h,
        "stop": l,
        "target1": round(h + rng, 4),
        "target2": round(h + (2 * rng), 4),
        "range_size": rng
    }


# =========================================================
# HANGING MAN DETECTION
# =========================================================
def detect_hanging_man(
    df,
    strict_wick_ratio=2.5,
    strict_body_threshold=0.35,
    lazy_wick_ratio=1.25,
    lazy_body_threshold=0.55
):

    if df is None or len(df) < 1:
        return {"detected": False}

    candle = df.iloc[-1]

    o = f(candle.get("Open"))
    h = f(candle.get("High"))
    l = f(candle.get("Low"))
    c = f(candle.get("Close"))

    rng = max(h - l, 1e-9)
    body = abs(c - o)

    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)

    body_pct = body / rng
    wick_ratio = lower_wick / max(body, 1e-9)

    strict = (
        body_pct <= strict_body_threshold
        and wick_ratio >= strict_wick_ratio
        and upper_wick <= body * 0.60
    )

    lazy = (
        body_pct <= lazy_body_threshold
        and wick_ratio >= lazy_wick_ratio
        and upper_wick <= body
    )

    detected = strict or lazy

    return {
        "detected": detected,
        "classification": (
            "INSTITUTIONAL_HANGING_MAN" if strict else
            "LAZY_HANGING_MAN" if lazy else None
        ),
        "type": "HangingMan",

        "open": o,
        "high": h,
        "low": l,
        "close": c,

        "body": round(body, 4),
        "range": round(rng, 4),
        "lower_wick": round(lower_wick, 4),
        "upper_wick": round(upper_wick, 4),
        "body_pct": round(body_pct, 4),
        "wick_ratio": round(wick_ratio, 3),

        "location": "Potential Distribution (Uptrend Exhaustion)",

        # TRADE STRUCTURE LOCK
        "entry": l,
        "stop": h,
        "target1": round(l - rng, 4),
        "target2": round(l - (2 * rng), 4),
        "range_size": rng
    }


# =========================================================
# BREAKOUT CLASSIFICATION
# =========================================================
def classify_hammer_breakout(df, hammer):

    if not hammer or not hammer.get("detected"):
        return "NONE"

    last = df.iloc[-1]

    close = f(last.get("Close"))
    high = f(last.get("High"))
    low = f(last.get("Low"))

    h_high = hammer.get("high")
    h_low = hammer.get("low")

    if h_high is None or h_low is None:
        return "NONE"

    if close > h_high:
        return "BULLISH_REVERSAL_CONFIRMED"

    if close < h_low:
        return "BEARISH_CONTINUATION_CONFIRMED"

    if high > h_high and close <= h_high:
        return "BULLISH_FALSE_BREAK_REJECTION"

    if low < h_low and close >= h_low:
        return "BEARISH_FALSE_BREAK_REJECTION"

    return "PENDING"


# =========================================================
# EVENT STATE ENGINE
# =========================================================
def build_hammer_event_state(df, max_hold=5):

    events = []
    active = None

    for i in range(len(df)):

        window = df.iloc[max(0, i - 1):i + 1]
        hammer = detect_hammer(window)

        if active is None and hammer.get("detected"):
            active = {
                "start": i,
                "high": hammer["high"],
                "low": hammer["low"],
                "status": "PENDING",
                "type": "Hammer"
            }

        if active is None:
            continue

        candle = df.iloc[i]

        close = f(candle.get("Close"))
        high = f(candle.get("High"))
        low = f(candle.get("Low"))

        if close > active["high"]:
            active["status"] = "CONFIRMED_BULLISH"
        elif close < active["low"]:
            active["status"] = "CONFIRMED_BEARISH"
        elif high > active["high"] and close <= active["high"]:
            active["status"] = "LIQUIDITY_REJECTION_BULL"
        elif low < active["low"] and close >= active["low"]:
            active["status"] = "LIQUIDITY_REJECTION_BEAR"

        if i - active["start"] >= max_hold and active["status"] == "PENDING":
            active["status"] = "EXPIRED"

        if active["status"] != "PENDING":
            events.append(active.copy())
            active = None

    return events, active


# =========================================================
# CONFIRMATION ENGINE
# =========================================================
def confirm_hammer_today(today_candle, yesterday_hammer):

    if not yesterday_hammer:
        return "NONE"

    if not yesterday_hammer.get("detected"):
        return "NONE"

    close = f(today_candle.get("Close"))
    open_ = f(today_candle.get("Open"))
    high = f(today_candle.get("High"))
    low = f(today_candle.get("Low"))

    h_high = yesterday_hammer.get("high")
    h_low = yesterday_hammer.get("low")

    if h_high is None or h_low is None:
        return "NONE"

    if close > h_high:
        return "CONFIRMED"

    if close < h_low:
        return "FAILED"

    if high > h_high and close > open_ and close <= h_high:
        return "BULLISH_BREAK_ATTEMPT"

    if high > h_high and close < open_ and close <= h_high:
        return "LIQUIDITY_REJECTION"

    return "PENDING"


# =========================================================
# TRADE PLAN GENERATOR (FIXED CARRYOVER)
# =========================================================
def build_hammer_trade_plan(hammer, breakout_state, confirmation_state="NONE"):

    if not hammer or not hammer.get("detected"):
        return {
            "setup": "NO SIGNAL",
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "failure": None,
            "interpretation": "No hammer detected."
        }

    h = hammer["high"]
    l = hammer["low"]
    rng = max(h - l, 1e-9)
    classification = hammer.get("classification", "HAMMER")

    if confirmation_state == "CONFIRMED" or breakout_state == "BULLISH_REVERSAL_CONFIRMED":
        return {
            "setup": f"{classification} CONFIRMED LONG",
            "entry": hammer.get("entry", h),
            "stop": hammer.get("stop", l),
            "target1": hammer.get("target1", round(h + rng, 4)),
            "target2": hammer.get("target2", round(h + (2 * rng), 4)),
            "failure": "Close below hammer low",
            "interpretation": "Hammer confirmed. Buyers achieved acceptance above the hammer high."
        }

    if confirmation_state == "FAILED" or breakout_state == "BEARISH_CONTINUATION_CONFIRMED":
        return {
            "setup": f"{classification} FAILURE SHORT",
            "entry": hammer.get("stop", l),
            "stop": hammer.get("entry", h),
            "target1": hammer.get("target1", round(l - rng, 4)),
            "target2": hammer.get("target2", round(l - (2 * rng), 4)),
            "failure": "Reclaim above hammer high",
            "interpretation": "Hammer failed. Sellers achieved acceptance below the hammer low."
        }

    if confirmation_state == "LIQUIDITY_REJECTION" or breakout_state == "BULLISH_FALSE_BREAK_REJECTION":
        return {
            "setup": "HAMMER REJECTION SHORT",
            "entry": hammer.get("entry", h),
            "stop": round(h + (rng * 0.10), 4),
            "target1": hammer.get("stop", l),
            "target2": round(l - rng, 4),
            "failure": "Acceptance above hammer high",
            "interpretation": "The hammer high was swept but rejected."
        }

    if confirmation_state == "BULLISH_BREAK_ATTEMPT":
        return {
            "setup": "HAMMER BREAK ATTEMPT",
            "entry": hammer.get("entry", h),
            "stop": hammer.get("stop", l),
            "target1": hammer.get("target1", round(h + rng, 4)),
            "target2": hammer.get("target2", round(h + (2 * rng), 4)),
            "failure": "Close below hammer low",
            "interpretation": "Buyers attempted a breakout but have not yet achieved acceptance."
        }

    return {
        "setup": f"{classification} LONG SETUP",
        "entry": hammer.get("entry", h),
        "stop": hammer.get("stop", l),
        "target1": hammer.get("target1", round(h + rng, 4)),
        "target2": hammer.get("target2", round(h + (2 * rng), 4)),
        "failure": f"Close below {round(l,4)}",
        "interpretation": "A valid hammer has formed. Await confirmation."
    }


# =========================================================
# MAIN ENGINE
# =========================================================
def analyze_hammer(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 1:
        return {"journal_prompt": "Insufficient data"}

    hammer_today = detect_hammer(df.iloc[-1:])
    shooting_star_today = detect_shooting_star(df.iloc[-1:])
    inverted_hammer_today = detect_inverted_hammer(df.iloc[-1:])
    hanging_man_today = detect_hanging_man(df.iloc[-1:])

    last = df.iloc[-1]

    pattern_today = {
        "detected": False,
        "type": None,
        "classification": None,
        "open": f(last["Open"]),
        "high": f(last["High"]),
        "low": f(last["Low"]),
        "close": f(last["Close"])
    }

    if shooting_star_today.get("detected"):
        pattern_today = shooting_star_today
    elif inverted_hammer_today.get("detected"):
        pattern_today = inverted_hammer_today
    elif hammer_today.get("detected"):
        pattern_today = hammer_today
    elif hanging_man_today.get("detected"):
        pattern_today = hanging_man_today

    pattern_yesterday = {
        "detected": False,
        "type": None,
        "classification": None
    }

    if len(df) >= 2:

        prev = df.iloc[-2]

        pattern_yesterday.update({
            "open": f(prev["Open"]),
            "high": f(prev["High"]),
            "low": f(prev["Low"]),
            "close": f(prev["Close"])
        })

        y_hammer = detect_hammer(df.iloc[-2:-1])
        y_star = detect_shooting_star(df.iloc[-2:-1])
        y_inv = detect_inverted_hammer(df.iloc[-2:-1])
        y_hang = detect_hanging_man(df.iloc[-2:-1])

        if y_star.get("detected"):
            pattern_yesterday = y_star
        elif y_inv.get("detected"):
            pattern_yesterday = y_inv
        elif y_hammer.get("detected"):
            pattern_yesterday = y_hammer
        elif y_hang.get("detected"):
            pattern_yesterday = y_hang

    confirmation_state = "NONE"

    if pattern_yesterday.get("detected"):

        close = f(df.iloc[-1]["Close"])
        y_high = pattern_yesterday["high"]
        y_low = pattern_yesterday["low"]

        if pattern_yesterday["type"] == "Hammer":
            if close > y_high:
                confirmation_state = "CONFIRMED"
            elif close < y_low:
                confirmation_state = "FAILED"
            else:
                confirmation_state = "PENDING"
        else:
            if close < y_low:
                confirmation_state = "CONFIRMED"
            elif close > y_high:
                confirmation_state = "FAILED"
            else:
                confirmation_state = "PENDING"

    regime = "NO_EDGE"

    if pattern_today.get("detected"):
        if pattern_today["type"] == "Hammer":
            regime = "ACTIVE_HAMMER_EVENT"
        elif pattern_today["type"] == "ShootingStar":
            regime = "ACTIVE_SHOOTING_STAR_EVENT"
        elif pattern_today["type"] == "InvertedHammer":
            regime = "ACTIVE_INVERTED_HAMMER_EVENT"
        elif pattern_today["type"] == "HangingMan":
            regime = "ACTIVE_HANGING_MAN_EVENT"
    elif confirmation_state == "CONFIRMED":
        regime = "CONFIRMED"
    elif confirmation_state == "FAILED":
        regime = "FAILED"
    elif confirmation_state == "PENDING":
        regime = "PENDING_CONFIRMATION"

    trade_plan = build_hammer_trade_plan(
        pattern_today,
        classify_hammer_breakout(df, pattern_today) if pattern_today.get("detected") else "NONE",
        confirmation_state
    )

    return {
        "journal_prompt": format_hammer_journal_prompt({
            "pattern_today": pattern_today,
            "pattern_yesterday": pattern_yesterday,
            "confirmation_state": confirmation_state,
            "regime": regime,
            "trade_plan": trade_plan
        })
    }


# =========================================================
# JOURNAL FORMATTER
# =========================================================
def format_hammer_journal_prompt(result):

    today = result.get("pattern_today") or {}
    yesterday = result.get("pattern_yesterday") or {}
    tp = result.get("trade_plan") or {}

    return f"""
# ==================================================
📌 HAMMER/SHOOTING STAR DETECTOR
# ==================================================

TODAY:
- Pattern Detected: {today.get('detected')}
- Type: {today.get('type')}
- Classification: {today.get('classification')}

📈 RAW CANDLE DATA:
- Open: {today.get('open')}
- High: {today.get('high')}
- Low: {today.get('low')}
- Close: {today.get('close')}

YESTERDAY:
- Pattern Exists: {yesterday.get('detected')}
- Type: {yesterday.get('type')}
- Confirmation State: {result.get('confirmation_state')}

--------------------------------------------------
⚠️ REGIME:
- {result.get('regime')}

--------------------------------------------------
🎯 TRADE PLAN

- Setup Quality: {tp.get('setup')}
- Entry Trigger: {tp.get('entry')}

- Aggressive Stop: {tp.get('stop')}
- Conservative Stop: {tp.get('stop')}

- Target 1: {tp.get('target1')}
- Target 2: {tp.get('target2')}

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

==================================================
"""
