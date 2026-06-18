import numpy as np
import pandas as pd

# =========================================================
# SAFE HELPERS
# =========================================================

def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def poly_slope(arr):
    try:
        arr = np.asarray(arr, dtype=float)
        if len(arr) < 2 or np.all(np.isnan(arr)):
            return 0.0
        return np.polyfit(range(len(arr)), arr, 1)[0]
    except:
        return 0.0


# =========================================================
# NORMALIZATION (FIXED TIMESTAMP PARSING)
# =========================================================

def normalize_ohlcv(df, ticker=None):
    df = df.copy()
    df = df.reset_index(drop=True)

    if "timestamp" not in df.columns:

        if "date" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["date"],
                errors="coerce",
                format="mixed",
                utc=True
            )

        elif "datetime" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["datetime"],
                errors="coerce",
                format="mixed",
                utc=True
            )

        elif isinstance(df.index, pd.DatetimeIndex):
            df["timestamp"] = pd.to_datetime(df.index, errors="coerce", utc=True)

    df = df.dropna(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    for c in ["High", "Low", "Close", "Volume"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = np.nan

    return df

def detect_liquidity_sweep(high, low, close, range_high, range_low, volume=None, avg_volume=None):

    if any(pd.isna(x) for x in [high, low, close, range_high, range_low]):
        return None

    range_size = range_high - range_low
    if range_size <= 0:
        return None

    displacement = range_size * 0.2  # adaptive structural threshold

    vol_confirm = (
        volume is not None and
        avg_volume is not None and
        volume > avg_volume * 1.2
    )

    # -------------------------
    # BEARISH SWEEP (UTAD ZONE)
    # -------------------------
    if high > range_high + displacement and close < range_high:

        return {
            "type": "BearishSweep",
            "confirmed": vol_confirm,
            "penetration_pct": round(((high - range_high) / range_high) * 100, 2),
            "context": "liquidity_above_range"
        }

    # -------------------------
    # BULLISH SWEEP (SPRING ZONE)
    # -------------------------
    if low < range_low - displacement and close > range_low:

        return {
            "type": "BullishSweep",
            "confirmed": vol_confirm,
            "penetration_pct": round(((range_low - low) / range_low) * 100, 2),
            "context": "liquidity_below_range"
        }

    return None

def calculate_structural_position(close, range_high, range_low):
    try:
        if range_high is None or range_low is None:
            return None

        if range_high == range_low:
            return 0.5

        return (close - range_low) / (range_high - range_low)

    except:
        return None

def classify_sequence(state_dict, i=None):
    try:
        if not isinstance(state_dict, dict):
            return "UNKNOWN"

        acc = state_dict.get("accumulation_curve", [])
        abs_sat = state_dict.get("absorption_saturation", [])
        break_p = state_dict.get("breakout_pressure", [])

        if len(acc) == 0:
            return "UNKNOWN"

        idx = i if i is not None else -1

        if acc[idx] > 0.7:
            return "ACCUMULATION"
        if abs_sat[idx] > 0.7:
            return "ABSORPTION"
        if break_p[idx] > 0.6:
            return "MARKUP"

        return "TRANSITION"

    except:
        return "UNKNOWN"
        
# =========================================================
# FRACTAL CORE STATE MODEL
# =========================================================

def compute_lifecycle_state(df):

    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values
    vol = df["Volume"].values

    vol_ma = pd.Series(vol).rolling(20, min_periods=1).mean().values
    n = len(df)

    state = {
        "accumulation_curve": np.zeros(n),
        "absorption_saturation": np.zeros(n),
        "breakout_pressure": np.zeros(n),
        "efficiency_decay": np.zeros(n),
    }

    for i in range(1, n):

        rng = max(high[i] - low[i], 1e-6)
        vol_ratio = vol[i] / max(vol_ma[i], 1e-6)

        compression = 1 - (rng / max(close[i], 1e-6))

        state["accumulation_curve"][i] = np.clip(
            compression * (1 / (1 + abs(poly_slope(close[max(0,i-5):i+1])))),
            0, 1
        )

        price_response = abs(close[i] - close[i-1])

        state["absorption_saturation"][i] = np.clip(
            vol_ratio / (price_response + 1e-6),
            0, 1
        )

        state["breakout_pressure"][i] = np.clip(
            state["accumulation_curve"][i] * state["absorption_saturation"][i],
            0, 1
        )

        state["efficiency_decay"][i] = np.clip(
            price_response / (vol[i] + 1e-6),
            0, 1
        )

    return state


# =========================================================
# STRUCTURAL FEATURES
# =========================================================

def compute_strength_vector(state, i):
    return {
        "regime_pressure": float(state["breakout_pressure"][i] - state["absorption_saturation"][i]),
        "absorption_depth": float(state["absorption_saturation"][i]),
        "breakout_quality": float(state["breakout_pressure"][i]),
        "liquidity_displacement": float(state["efficiency_decay"][i]),
    }


def aggregate_strength(vec):
    return (
        vec["regime_pressure"] * 0.4 +
        vec["absorption_depth"] * 0.3 +
        vec["breakout_quality"] * 0.2 +
        (1 - vec["liquidity_displacement"]) * 0.1
    )


def is_valid_breakout(vec):
    return (
        vec["breakout_quality"] >= 0.6 and
        vec["absorption_depth"] >= 0.5 and
        vec["liquidity_displacement"] <= 0.7
    )


def extract_regime_pressure(state):
    try:
        if state is None:
            return 0.0

        bp = state.get("breakout_pressure", [])
        ab = state.get("absorption_saturation", [])

        if len(bp) == 0 or len(ab) == 0:
            return 0.0

        return float(bp[-1] - ab[-1])

    except:
        return 0.0
        
# =========================================================
# TIMEFRAME ENGINE
# =========================================================

def run_tf(df):

    state = compute_lifecycle_state(df)

    events = []
    prev_phase = None

    for i in range(len(df)):

        vec = compute_strength_vector(state, i)
        score = aggregate_strength(vec)

        if state["accumulation_curve"][i] > 0.7:
            phase = "ACCUMULATION"
        elif state["absorption_saturation"][i] > 0.7:
            phase = "ABSORPTION"
        elif is_valid_breakout(vec):
            phase = "MARKUP"
        else:
            phase = "TRANSITION"

        if phase != prev_phase:
            events.append({
                "type": phase,
                "index": i,
                "price": float(df["Close"].iloc[i]),
                "strength_vector": vec,
                "score": score,
                "timestamp": df["timestamp"].iloc[i]
            })
            prev_phase = phase

    return {
        "events": events[-10:],
        "state": state,
        "final_score": np.mean([e["score"] for e in events]) if events else 0
    }

def safe_final_score(tf):
    try:
        if not isinstance(tf, dict):
            return 0.0
        return float(tf.get("final_score", 0.0))
    except:
        return 0.0
        

# =========================================================
# CROSS TIMEFRAME SOLVER (FIXED)
# =========================================================

def resolve_ctf(weekly, daily, m60):

    w_state = weekly.get("state", {})
    d_state = daily.get("state", {})
    m_state = m60.get("state", {})

    weekly_bias = extract_regime_pressure(w_state)
    daily_bias = extract_regime_pressure(d_state)
    m60_bias = extract_regime_pressure(m_state)

    # attach computed regime pressure safely
    weekly["regime_pressure"] = weekly_bias
    daily["regime_pressure"] = np.clip(daily_bias, weekly_bias - 0.3, weekly_bias + 0.3)
    m60["regime_pressure"] = np.clip(m60_bias, daily["regime_pressure"] - 0.4, daily["regime_pressure"] + 0.4)

    return weekly, daily, m60

# =========================================================
# MAIN ENGINE v3.1
# =========================================================

def analyze_wyckoff_fractals(df, ticker=None):

    df = normalize_ohlcv(df)

    tf_map = {
        "60M": "60min",
        "Daily": "1D",
        "Weekly": "1W"
    }

    def resample(rule):
        tmp = df.set_index("timestamp").resample(rule).agg({
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna().reset_index()
        return tmp

    results = {}

    weekly = run_tf(resample("1W"))
    daily = run_tf(resample("1D"))
    m60 = run_tf(resample("60min"))

    # ---------------------------
    # CROSS TF CONSTRAINT SOLVER
    # ---------------------------
    weekly, daily, m60 = resolve_ctf(
        weekly["state"] if "state" in weekly else {},
        daily["state"] if "state" in daily else {},
        m60["state"] if "state" in m60 else {}
    )

    results["60M"] = m60
    results["Daily"] = daily
    results["Weekly"] = weekly

    combined = np.mean([
        safe_final_score(weekly),
        safe_final_score(daily),
        safe_final_score(m60)
    ])

    return {
        "timeframes": results,
        "institutional_score": combined
    }
    
# =========================================================
# JOURNAL FORMATTER (RESTORED + FIXED)
# =========================================================

def format_for_journal(result, ticker=None):

    try:
        if not result:
            return "NO FRACTAL DATA"

        tf = result.get("timeframes", {})
        score = result.get("institutional_score", 0)

        def fmt(k):
            d = tf.get(k, {})
            e = d.get("events", [])
            if not e:
                return f"{k}: No events"

            last = e[-1]
            return f"{k} | {last['type']} | Score {round(last['score'],2)} | {last['price']}"

        return f"""
WYCKOFF FRACTAL JOURNAL
Ticker: {ticker or "N/A"}

Score: {round(score,4)}

- {fmt("Weekly")}
- {fmt("Daily")}
- {fmt("60M")}
"""

    except Exception as e:
        return f"FORMAT ERROR: {e}"