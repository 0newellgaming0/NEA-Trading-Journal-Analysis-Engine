# =========================================================
# COUNTERATTACK / SEPARATING / SIDE-BY-SIDE WHITE LINES MODULE
# STRATEGY PLUGIN (RESOLVER COMPATIBLE)
# =========================================================

import logging
from modules.eventEngine import extract_event_date

logger = logging.getLogger("candle_clusters")


# =========================================================
# DETECTOR (PURE)
# =========================================================
def detect_candle_cluster(candle, prev_candle, f):

    logger.debug("[CANDLE CLUSTER] detect_candle_cluster() called")

    try:
        high = f(candle.get("High"))
        low = f(candle.get("Low"))
        open_ = f(candle.get("Open"))
        close = f(candle.get("Close"))

        ph = f(prev_candle.get("High"))
        pl = f(prev_candle.get("Low"))
        po = f(prev_candle.get("Open"))
        pc = f(prev_candle.get("Close"))

    except Exception as e:
        logger.error(f"[CANDLE CLUSTER] OHLC extraction failed: {e}")
        return {"detected": False, "error": str(e)}

    if any(v is None for v in [high, low, open_, close, ph, pl, po, pc]):
        return {"detected": False}

    if high <= low or ph <= pl:
        return {"detected": False}

    prev_body = abs(pc - po)
    curr_body = abs(close - open_)

    prev_bull = pc > po
    prev_bear = pc < po
    curr_bull = close > open_
    curr_bear = close < open_

    prev_mid = (ph + pl) / 2.0

    gap_up = low > ph
    gap_down = high < pl

    # =========================================================
    # COUNTERATTACK LINES (REVERSAL 2-CANDLE CLASH)
    # =========================================================
    bullish_counterattack = (
        prev_bear and
        curr_bull and
        close >= pc and
        open_ < low + (high - low) * 0.5
    )

    bearish_counterattack = (
        prev_bull and
        curr_bear and
        close <= pc and
        open_ > high - (high - low) * 0.5
    )

    # =========================================================
    # SEPARATING LINES (STRONG TREND CONTINUATION GAP)
    # =========================================================
    separating_bull = (
        prev_bull and
        curr_bull and
        gap_up and
        curr_body >= prev_body
    )

    separating_bear = (
        prev_bear and
        curr_bear and
        gap_down and
        curr_body >= prev_body
    )

    # =========================================================
    # SIDE-BY-SIDE WHITE LINES (BULLISH CONTINUATION CLUSTER)
    # Two consecutive bullish candles with similar bodies/high alignment
    # =========================================================
    side_by_side_white = (
        prev_bull and
        curr_bull and
        abs(curr_body - prev_body) / max(prev_body, 1e-9) < 0.25 and
        abs(high - ph) / max(ph, 1e-9) < 0.01
    )

    # =========================================================
    # OUTPUTS
    # =========================================================

    if bullish_counterattack:
        return {
            "detected": True,
            "type": "Counterattack Lines",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if bearish_counterattack:
        return {
            "detected": True,
            "type": "Counterattack Lines",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if separating_bull:
        return {
            "detected": True,
            "type": "Separating Lines",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if separating_bear:
        return {
            "detected": True,
            "type": "Separating Lines",
            "direction": "Bearish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    if side_by_side_white:
        return {
            "detected": True,
            "type": "Side-by-Side White Lines",
            "direction": "Bullish",
            "high": high,
            "low": low,
            "open": open_,
            "close": close
        }

    return {"detected": False}


# =========================================================
# TRADE BUILDER (PURE)
# =========================================================
def build_candle_cluster_trade_state(event):

    high = event["high"]
    low = event["low"]
    rng = max(high - low, 1e-9)

    direction = event.get("direction")
    pattern_type = event.get("type")

    # =========================================================
    # REVERSAL STRUCTURES (COUNTERATTACK)
    # =========================================================
    if pattern_type == "Counterattack Lines":

        if direction == "Bullish":
            return {
                "trade_type": "REVERSAL",
                "direction": "LONG",
                "entry": high,
                "stop": low - rng * 0.1,
                "invalidation": low,
                "target1": high + rng,
                "target2": high + 2 * rng,
                "failure": f"Close below {low}",
                "interpretation": "Bullish counterattack rejection of prior bearish pressure."
            }

        if direction == "Bearish":
            return {
                "trade_type": "REVERSAL",
                "direction": "SHORT",
                "entry": low,
                "stop": high + rng * 0.1,
                "invalidation": high,
                "target1": low - rng,
                "target2": low - 2 * rng,
                "failure": f"Close above {high}",
                "interpretation": "Bearish counterattack rejection of prior bullish pressure."
            }

    # =========================================================
    # CONTINUATION STRUCTURES (SEPARATING / SIDE-BY-SIDE)
    # =========================================================
    if pattern_type in ["Separating Lines", "Side-by-Side White Lines"]:

        if direction == "Bullish":
            return {
                "trade_type": "CONTINUATION",
                "direction": "LONG",
                "entry": high,
                "stop": low - rng * 0.1,
                "invalidation": low,
                "target1": high + rng * 1.2,
                "target2": high + rng * 2.5,
                "failure": f"Close below {low}",
                "interpretation": f"{pattern_type} bullish continuation expansion structure."
            }

        if direction == "Bearish":
            return {
                "trade_type": "CONTINUATION",
                "direction": "SHORT",
                "entry": low,
                "stop": high + rng * 0.1,
                "invalidation": high,
                "target1": low - rng * 1.2,
                "target2": low - rng * 2.5,
                "failure": f"Close above {high}",
                "interpretation": f"{pattern_type} bearish continuation expansion structure."
            }

    logger.warning(f"[CANDLE CLUSTER] Unknown event type or direction")
    return {}


# =========================================================
# EVENT RULES
# =========================================================
def candle_cluster_event_rules(event, candle, close, high, low):

    status = event.get("status")

    if status == "PENDING":

        if event["direction"] == "Bullish":
            if close > event["high"]:
                return "CONFIRM"
            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":
            if close < event["low"]:
                return "CONFIRM"
            if close > event["high"]:
                return "FAIL"

    elif status == "CONFIRMED":

        if event["direction"] == "Bullish":
            if close < event["low"]:
                return "FAIL"

        elif event["direction"] == "Bearish":
            if close > event["high"]:
                return "FAIL"

    return None


# =========================================================
# MAIN ANALYZER (PINBAR-MIRROR ARCHITECTURE)
# =========================================================
def analyze_candle_cluster(df, event_store, f=float):

    logger.info("[CANDLE CLUSTER] analyze_candle_cluster() called")

    latest_pattern = None

    # SEARCH BACKWARD (PINBAR STYLE)
    for i in range(len(df) - 1, 0, -1):

        candle = df.iloc[i]
        prev_candle = df.iloc[i - 1]

        detected = detect_candle_cluster(candle, prev_candle, f)

        if not detected.get("detected"):
            continue

        event_date = extract_event_date(df, i)
        direction = detected["direction"]

        latest_pattern = {
            "id": 1,
            "detected": True,
            "type": detected["type"],
            "direction": direction,
            "trade_type": "MIXED",
            "high": detected["high"],
            "low": detected["low"],
            "index": i,
            "date": event_date,
            "days_active": 0,
            "status": "PENDING",
            "status_reason": "Awaiting confirmation"
        }

        logger.info(
            f"[CANDLE CLUSTER] Found {detected['type']} date={event_date} index={i} direction={direction}"
        )

        break

    if latest_pattern is None:
        return {"event": {}, "trade": {}, "regime": "NONE"}

    # VALIDATION LOOP (PINBAR-LIKE)
    for i in range(latest_pattern["index"] + 1, len(df)):

        candle = df.iloc[i]

        close = float(candle["Close"])
        high = float(candle["High"])
        low = float(candle["Low"])

        action = candle_cluster_event_rules(
            latest_pattern,
            candle,
            close,
            high,
            low
        )

        latest_pattern["days_active"] = i - latest_pattern["index"]

        if action == "CONFIRM" and latest_pattern["status"] == "PENDING":

            latest_pattern["status"] = "CONFIRMED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Cluster structure validated"

        elif action == "FAIL":

            latest_pattern["status"] = "FAILED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)

            latest_pattern["status_reason"] = build_candle_cluster_trade_state(
                latest_pattern
            )["failure"]

            break

        elif action == "EXPIRE":

            latest_pattern["status"] = "EXPIRED"
            latest_pattern["resolved_date"] = extract_event_date(df, i)
            latest_pattern["status_reason"] = "Pattern expired"
            break

    trade = build_candle_cluster_trade_state(latest_pattern)

    return {
        "event": latest_pattern,
        "trade": trade,
        "regime": "UNKNOWN"
    }