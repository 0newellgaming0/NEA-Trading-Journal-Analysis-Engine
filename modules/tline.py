# =========================================================
# TLINE MODULE (STRATEGY PLUGIN - RESOLVER COMPATIBLE)
# ENHANCED - PINBAR STRUCTURE PARITY PRESERVED
# =========================================================

import logging
from modules.eventEngine import extract_event_date
from modules.signalEngine import evaluate_trend  # KEPT (no regression)

logger = logging.getLogger("tline")


# =========================================================
# SAFE HELPER
# =========================================================
def f(x):
    try:
        return float(x)
    except:
        return 0.0


# =========================================================
# INDICATORS
# =========================================================
def get_tline(df, i):
    return df["Close"].ewm(span=8).mean().iloc[i]


def get_sma(df, i, period):
    return df["Close"].rolling(period).mean().iloc[i]


# =========================================================
# SUPPORT / RESISTANCE (PRIMARY STRUCTURE)
# =========================================================
def get_primary_levels(df, i):
    try:
        lookback = df.iloc[max(0, i - 10): i]

        return {
            "support": f(lookback["Low"].min()),
            "resistance": f(lookback["High"].max()),
            "sma50": f(get_sma(df, i, 50))
        }
    except:
        return {"support": 0.0, "resistance": 0.0, "sma50": 0.0}


# =========================================================
# CRUNCH (COMPRESSION)
# =========================================================
def detect_tline_crunch(ema8, sma50, sma200, close, atr=0.0):

    spread = abs(ema8 - sma50) + abs(sma50 - sma200)

    tight = spread < (atr * 0.6) if atr > 0 else spread < 0.5
    price_near = abs(close - ema8) < (atr * 0.4 if atr > 0 else 0.3)

    if tight and price_near:
        return {"crunch": True, "type": "TLINE_CRUNCH"}

    return {"crunch": False}


# =========================================================
# EXUBERANCE (ANNOTATION ONLY)
# =========================================================
def detect_exuberance(close, ema8, atr=0.0):

    if atr <= 0:
        return {"exuberant": False}

    ratio = abs(close - ema8) / atr

    if ratio > 2.5:
        return {"exuberant": True, "level": "EXTREME"}

    if ratio > 1.8:
        return {"exuberant": True, "level": "HIGH"}

    return {"exuberant": False}


# =========================================================
# ROLLOVER (EXHAUSTION BEFORE REVERSAL)
# =========================================================
def detect_tline_rollover(df, i):

    try:
        ema_now = get_tline(df, i)
        ema_prev = get_tline(df, i - 1)

        sma50_now = get_sma(df, i, 50)
        sma50_prev = get_sma(df, i - 1, 50)

        slope_ema = ema_now - ema_prev
        slope_sma = sma50_now - sma50_prev

        if abs(slope_ema) < 0.01 and abs(slope_sma) < 0.01:
            return {"rollover": True, "type": "TLINE_ROLLOVER"}

    except:
        pass

    return {"rollover": False}


# =========================================================
# J-HOOK (BREAK → RETEST → CONTINUE)
# =========================================================
def detect_jhook(df, i):

    try:
        ema8 = get_tline(df, i)
        close = f(df["Close"].iloc[i])

        prev_high = df["High"].iloc[max(0, i - 5): i].max()
        prev_low = df["Low"].iloc[max(0, i - 5): i].min()

        breakout_up = close > prev_high
        breakout_down = close < prev_low

        pullback = abs(close - ema8) / max(close, 1e-9) < 0.015

        if breakout_up and pullback:
            return {"jhook": True, "direction": "Bullish"}

        if breakout_down and pullback:
            return {"jhook": True, "direction": "Bearish"}

    except:
        pass

    return {"jhook": False}


# =========================================================
# DETECTOR (EVENT DETECTION ONLY)
# =========================================================
def detect_tline(candle, df, i):

    logger.debug("[TLINE] detect_tline() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

        ema8 = f(get_tline(df, i))
        sma50 = f(get_sma(df, i, 50))
        sma200 = f(get_sma(df, i, 200))

    except Exception as e:
        logger.error(f"[TLINE] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if high <= low:
        return {"detected": False}

    bullish = close > ema8
    bearish = close < ema8

    # -----------------------------------------------------
    # PRIMARY EVENTS
    # -----------------------------------------------------
    cross_up = open_ <= ema8 and close > ema8
    cross_down = open_ >= ema8 and close < ema8

    spread = abs(ema8 - sma50) + abs(sma50 - sma200)
    crunch = spread < 0.5

    ema_prev = f(get_tline(df, i - 1))
    sma50_prev = f(get_sma(df, i - 1, 50))

    rollover = (
        abs(ema8 - ema_prev) < 0.01 and
        abs(sma50 - sma50_prev) < 0.01
    )

    prev_high = df["High"].iloc[max(0, i - 5):i].max()
    prev_low = df["Low"].iloc[max(0, i - 5):i].min()

    breakout_up = close > prev_high
    breakout_down = close < prev_low

    pullback = abs(close - ema8) / max(close, 1e-9) < 0.015

    jhook = (
        (breakout_up and pullback) or
        (breakout_down and pullback)
    )

    # -----------------------------------------------------
    # EVENT RESOLUTION
    # -----------------------------------------------------
    if cross_up:
        pattern_type = "TLINE_CROSS"
        direction = "Bullish"

    elif cross_down:
        pattern_type = "TLINE_CROSS"
        direction = "Bearish"

    elif jhook:
        pattern_type = "TLINE_JHOOK"
        direction = "Bullish" if breakout_up else "Bearish"

    elif rollover:
        pattern_type = "TLINE_ROLLOVER"
        direction = "Bullish" if bullish else "Bearish"

    elif crunch:
        pattern_type = "TLINE_CRUNCH"
        direction = "Bullish" if bullish else "Bearish"

    else:
        # -------------------------------------------------
        # Continuation is NOT an event.
        # Trend engine handles continuation.
        # -------------------------------------------------
        return {"detected": False}

    return {

        "detected": True,
        "type": pattern_type,
        "direction": direction,

        "high": high,
        "low": low,
        "open": open_,
        "close": close,

        "ema8": ema8,
        "sma50": sma50,
        "sma200": sma200
    }

# =========================================================
# TLINE INTERPRETATION ENGINE (CLEAN + ISOLATED)
# =========================================================
def interpret_tline(event):

    direction = event.get("direction")
    ptype = event.get("type", "")
    status = event.get("status")

    out = []

    # STRUCTURE LOGIC
    if ptype == "TLINE_CROSS":
        out.append("EMA8 cross indicates directional shift attempt.")

    elif ptype == "TLINE_JHOOK":
        out.append("J-Hook breakout-retest continuation structure detected.")

    elif ptype == "TLINE_ROLLOVER":
        out.append("Momentum flattening suggests exhaustion or transition phase.")

    elif ptype == "TLINE_CRUNCH":
        out.append("Compression detected between EMA8 and higher timeframe averages.")

    else:
        out.append("T-Line continuation structure with no major distortion.")

    # DIRECTIONAL CONTEXT
    if direction == "Bullish":
        out.append("Price is holding above EMA8 showing bullish control.")
    else:
        out.append("Price is holding below EMA8 showing bearish control.")

    # STATUS CONTEXT
    if status == "PENDING":
        out.append("Setup is in development stage awaiting confirmation.")
    elif status == "CONFIRMED":
        out.append("Structure confirmed via price acceptance.")
    elif status == "FAILED":
        out.append("Structure invalidated by EMA8 rejection.")

    return " | ".join(out)

    
# =========================================================
# EVENT RULES
# =========================================================
def tline_event_rules(event, close, ema8):

    status = event.get("status")

    if status == "PENDING":

        if event["direction"] == "Bullish":
            if close > ema8:
                return "CONFIRM"
            if close < ema8:
                return "FAIL"

        if event["direction"] == "Bearish":
            if close < ema8:
                return "CONFIRM"
            if close > ema8:
                return "FAIL"

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish" and close < ema8:
            return "FAIL"

        if event["direction"] == "Bearish" and close > ema8:
            return "FAIL"

    return None


# =========================================================
# TRADE BUILDER (SAFE + STABLE)
# =========================================================
def build_tline_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event["direction"]

    levels = event.get("levels", {})

    if direction == "Bullish":
        return {
            "trade_type": "TLINE_CONTINUATION",
            "direction": "LONG",
            "entry": high,
            "stop": low - 0.1 * rng,
            "invalidation": low,
            "support": levels.get("support", low),
            "resistance": levels.get("resistance", high),
            "target1": high + rng,
            "target2": high + 2 * rng,
            "failure": "Close below EMA8",
            "interpretation": interpret_tline(event),
        }

    if direction == "Bearish":
        return {
            "trade_type": "TLINE_CONTINUATION",
            "direction": "SHORT",
            "entry": low,
            "stop": high + 0.1 * rng,
            "invalidation": high,
            "support": levels.get("support", low),
            "resistance": levels.get("resistance", high),
            "target1": low - rng,
            "target2": low - 2 * rng,
            "failure": "Close above EMA8",
            "interpretation": interpret_tline(event),
        }

    return {}


# =========================================================
# MAIN ANALYZER
# =========================================================
def analyze_tline(df, event_store):

    logger.info("[TLINE] analyze_tline called")

    latest_pattern = None

    # =====================================================
    # STEP 1
    # Find LAST ACTUAL EVENT
    # (continuation bars ignored)
    # =====================================================
    for i in range(len(df) - 1, -1, -1):

        candle = df.iloc[i]

        detected = detect_tline(candle, df, i)

        if not detected.get("detected"):
            continue

        latest_pattern = {

            "id": 1,

            "detected": True,
            "type": detected["type"],
            "direction": detected["direction"],

            "high": detected["high"],
            "low": detected["low"],
            "close": detected["close"],

            "ema8": detected["ema8"],
            "sma50": detected["sma50"],
            "sma200": detected["sma200"],

            "index": i,
            "date": extract_event_date(df, i),

            "status": "PENDING",

            "levels": get_primary_levels(df, i)
        }

        logger.info(
            f"[TLINE] Last event found: "
            f"{latest_pattern['type']} "
            f"at index {i}"
        )

        break

    if latest_pattern is None:

        return {
            "event": {},
            "trade": {},
            "regime": "NONE"
        }

    # =====================================================
    # STEP 2
    # Validate ONLY candles AFTER event
    # =====================================================
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = f(candle["Close"])
        ema8 = f(get_tline(df, i))

        latest_pattern["days_active"] = (
            i - latest_pattern["index"]
        )

        latest_pattern["crunch"] = detect_tline_crunch(

            ema8,

            f(get_sma(df, i, 50)),
            f(get_sma(df, i, 200)),

            close
        )

        latest_pattern["exuberance"] = detect_exuberance(
            close,
            ema8
        )

        latest_pattern["rollover"] = detect_tline_rollover(
            df,
            i
        )

        latest_pattern["jhook"] = detect_jhook(
            df,
            i
        )

        action = tline_event_rules(
            latest_pattern,
            close,
            ema8
        )

        if (
            action == "CONFIRM"
            and latest_pattern["status"] == "PENDING"
        ):

            latest_pattern["status"] = "CONFIRMED"

            latest_pattern["resolved_date"] = extract_event_date(
                df,
                i
            )

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"

            latest_pattern["resolved_date"] = extract_event_date(
                df,
                i
            )

            break

    # =====================================================
    # STEP 3
    # Event still unresolved
    # =====================================================
    if latest_pattern["status"] == "PENDING":

        logger.info(
            "[TLINE] Event remains pending "
            "(no validating candles yet)"
        )

    # =====================================================
    # STEP 4
    # Interpretation
    # =====================================================
    latest_pattern["interpretation"] = interpret_tline(
        latest_pattern
    )

    # =====================================================
    # STEP 5
    # Trade
    # =====================================================
    trade = build_tline_trade_state(
        latest_pattern
    )

    # =====================================================
    # STEP 6
    # Regime
    # =====================================================
    sma50 = latest_pattern["sma50"]
    sma200 = latest_pattern["sma200"]

    if sma50 > sma200:
        regime = "BULL_TREND"

    elif sma50 < sma200:
        regime = "BEAR_TREND"

    else:
        regime = "TRANSITION"

    return {

        "event": latest_pattern,

        "trade": trade,

        "regime": regime
    }