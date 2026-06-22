import numpy as np
import pandas as pd

# =========================================================
# REVERSAL ENGINE CONSTANTS
# =========================================================

STRICT_MIDPOINT_BUFFER = 0.10  # 10% of previous candle body

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
    df = df.copy()
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["Open", "High", "Low", "Close"])

def midpoint(open_, close_):
    return (open_ + close_) / 2
    
# =========================================================
# 🌩 DARK CLOUD COVER
# =========================================================
def detect_dark_cloud_cover(df):
    if len(df) < 2:
        return {"detected": False, "type": None}

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    po, pc = f(prev["Open"]), f(prev["Close"])
    co, cc = f(curr["Open"]), f(curr["Close"])
    ph = f(prev["High"])
    pl = f(prev["Low"])

    prev_bull = pc > po
    curr_bear = cc < co

    mid = midpoint(po, pc)
    body = abs(pc - po)

    penetration_ok = (
        cc < mid and
        cc > po and
        cc < (mid - body * STRICT_MIDPOINT_BUFFER)
    )

    structure_ok = co > ph

    if prev_bull and curr_bear and structure_ok and penetration_ok:
        return {
            "detected": True,
            "type": "DarkCloudCover",
            "high": ph,
            "low": pl,
            "open": co,
            "close": cc,
        }

    return {"detected": False, "type": None}


# =========================================================
# ☀️ PIERCING LINE
# =========================================================
def detect_piercing_line(df):
    if len(df) < 2:
        return {"detected": False, "type": None}

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    po, pc = f(prev["Open"]), f(prev["Close"])
    co, cc = f(curr["Open"]), f(curr["Close"])
    ph = f(prev["High"])
    pl = f(prev["Low"])

    prev_bear = pc < po
    curr_bull = cc > co

    mid = midpoint(po, pc)
    body = abs(pc - po)

    penetration_ok = (
        cc > mid and
        cc < po and
        cc > (mid + body * STRICT_MIDPOINT_BUFFER)
    )

    structure_ok = co < pl

    if prev_bear and curr_bull and structure_ok and penetration_ok:
        return {
            "detected": True,
            "type": "PiercingLine",
            "high": ph,
            "low": pl,
            "open": co,
            "close": cc,
        }

    return {"detected": False, "type": None}

def resolve_state(prev_detected, curr_detected, close, high, low):

    if not prev_detected and not curr_detected:
        return "NONE"

    if prev_detected and not curr_detected:
        return "PENDING"

    if prev_detected and curr_detected:
        return "CONFIRMED"

    if close > high or close < low:
        return "INVALIDATED"

    return "WEAKENING"
    
# =========================================================
# MEMORY ENGINE
# =========================================================
def reversal_state_memory(df):
    states = []

    for i in range(len(df)):
        if i == 0:
            states.append(False)
            continue

        window = df.iloc[i-1:i+1]

        dcc = detect_dark_cloud_cover(window)
        pierce = detect_piercing_line(window)

        states.append(bool(dcc["detected"] or pierce["detected"]))

    out = df.copy()
    out["reversal_flag"] = states
    return out


# =========================================================
# EVENT ENGINE (FIXED PRIORITY LOGIC)
# =========================================================
def build_reversal_event_state(df, max_confirm_days=5):

    events = []
    active = None

    for i in range(len(df)):

        window = df.iloc[max(0, i-1):i+1]

        dcc = detect_dark_cloud_cover(window)
        pierce = detect_piercing_line(window)

        detected = None
        if dcc["detected"]:
            detected = dcc
        elif pierce["detected"]:
            detected = pierce

        if active is None and detected:
            active = {
                "start_index": i,
                "type": detected["type"],
                "high": detected["high"],
                "low": detected["low"],
                "status": "PENDING",
                "days_active": 0
            }
            continue

        if active is None or i <= active["start_index"]:
            continue

        close = f(df.iloc[i]["Close"])
        active["days_active"] = i - active["start_index"]

        if active["type"] == "DarkCloudCover":
            if close < active["low"]:
                active["status"] = "CONFIRMED"
            elif close > active["high"]:
                active["status"] = "FAILED"
        else:
            if close > active["high"]:
                active["status"] = "CONFIRMED"
            elif close < active["low"]:
                active["status"] = "FAILED"

        if active["status"] == "PENDING" and active["days_active"] >= max_confirm_days:
            active["status"] = "EXPIRED"

        if active["status"] in ("CONFIRMED", "FAILED", "EXPIRED"):
            events.append(active.copy())
            active = None

    return events, active


# =========================================================
# TRADE PLAN ENGINE
# =========================================================
def build_reversal_trade_plan(today, yesterday, state):

    if yesterday and yesterday.get("detected") and state == "PENDING":
        return {
            "setup": "ACTIVE REVERSAL EVENT",
            "entry": yesterday["high"] if yesterday["type"] == "DarkCloudCover" else yesterday["low"],
            "stop_close": yesterday["low"] if yesterday["type"] == "DarkCloudCover" else yesterday["high"],
            "target1": None,
            "target2": None,
            "failure": "Break invalidation range",
            "interpretation": "Reversal event active, awaiting confirmation."
        }

    if not (today.get("detected") or yesterday.get("detected")):
        return {
            "setup": "NO REVERSAL SIGNAL",
            "entry": None,
            "stop_close": None,
            "target1": None,
            "target2": None,
            "failure": None,
            "interpretation": "No institutional reversal structure detected."
        }

    pin = today if today.get("detected") else yesterday
    rng = pin["high"] - pin["low"]

    if pin["type"] == "DarkCloudCover":
        return {
            "setup": "FORMING DARK CLOUD COVER",
            "entry": pin["low"],
            "stop_close": pin["high"],
            "target1": pin["low"] - rng,
            "target2": pin["low"] - (2 * rng),
            "failure": f"Close above {pin['high']}",
            "interpretation": "Bearish reversal pressure forming."
        }

    return {
        "setup": "FORMING PIERCING LINE",
        "entry": pin["high"],
        "stop_close": pin["low"],
        "target1": pin["high"] + rng,
        "target2": pin["high"] + (2 * rng),
        "failure": f"Close below {pin['low']}",
        "interpretation": "Bullish reversal pressure forming."
    }


# =========================================================
# MAIN ENGINE
# =========================================================
def analyze_reversal_patterns(df):

    df = normalize_ohlcv_columns(df)
    df = enforce_schema(df)

    if len(df) < 2:
        return {"journal_prompt": "Insufficient data"}

    today_dcc = detect_dark_cloud_cover(df.iloc[-2:])
    today_pl = detect_piercing_line(df.iloc[-2:])

    today = today_dcc if today_dcc["detected"] else today_pl

    yesterday_dcc = detect_dark_cloud_cover(df.iloc[-3:-1])
    yesterday_pl = detect_piercing_line(df.iloc[-3:-1])

    yesterday = yesterday_dcc if yesterday_dcc["detected"] else yesterday_pl

    last_close = f(df.iloc[-1]["Close"])

    state = resolve_state(
        yesterday.get("detected"),
        today.get("detected"),
        last_close,
        today.get("high", 0),
        today.get("low", 0)
    )

    trade_plan = build_reversal_trade_plan(today, yesterday, state)

    return {
        "journal_prompt": format_reversal_journal({
            "today": today,
            "yesterday": yesterday,
            "state": state,
            "trade_plan": trade_plan,
            "today_candle": df.iloc[-1].to_dict(),
            "yesterday_candle": df.iloc[-2].to_dict()
        })
    }


# =========================================================
# JOURNAL FORMATTER
# =========================================================
def format_reversal_journal(result):

    t = result["today"]
    y = result["yesterday"]
    tp = result["trade_plan"]

    return f"""
# ==================================================
📌 INSTITUTIONAL REVERSAL ENGINE
(DARK CLOUD COVER + PIERCING LINE)
# ==================================================

TODAY:
- Detected: {t.get("detected")}
- Type: {t.get("type")}

YESTERDAY:
- Detected: {y.get("detected")}
- Type: {y.get("type")}

--------------------------------------------------
⚠️ STATE: {result.get("state")}

--------------------------------------------------
🎯 TRADE PLAN
- Setup: {tp.get("setup")}
- Entry: {tp.get("entry")}
- Stop: {tp.get("stop_close")}
- Target 1: {tp.get("target1")}
- Target 2: {tp.get("target2")}
- Failure: {tp.get("failure")}

--------------------------------------------------
🧠 INTERPRETATION
{tp.get("interpretation")}
"""