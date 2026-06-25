# =========================================================
# RENDERER (PURE - NO CONTEXT DEPENDENCY)
# =========================================================

import logging

logger = logging.getLogger("renderer")


def format_event_journal_prompt(result: dict):

    logger.info("\n[RENDERER] ================= INPUT START =================")
    logger.info(f"[RENDERER] result keys = {list(result.keys())}")

    event = result.get("event", {}) or {}
    trade = result.get("trade", {}) or {}

    # Regime is now treated as OPTIONAL METADATA ONLY
    regime = result.get("regime") or "UNKNOWN"

    # --------------------------------------------------
    # EVENT FIELDS
    # --------------------------------------------------
    detected = event.get("detected")
    event_type = event.get("type")
    direction = event.get("direction")
    trade_type = event.get("trade_type")
    status = event.get("status")

    high = event.get("high")
    low = event.get("low")

    event_id = event.get("id")
    event_index = event.get("index")

    detected_date = event.get("date") or event.get("event_date") or "UNKNOWN"
    resolved_date = event.get("resolved_date")

    days_active = event.get("days_active", 0)

    failure_reason = event.get("status_reason") or trade.get("failure")

    # --------------------------------------------------
    # EVENT TRACE
    # --------------------------------------------------
    logger.info("\n[RENDERER][EVENT] -----------------------------")
    logger.info(f"id            = {event_id}")
    logger.info(f"index         = {event_index}")
    logger.info(f"detected_date = {detected_date}")
    logger.info(f"resolved_date = {resolved_date}")
    logger.info(f"days_active   = {days_active}")

    logger.info(f"detected      = {detected}")
    logger.info(f"type          = {event_type}")
    logger.info(f"direction     = {direction}")
    logger.info(f"trade_type    = {trade_type}")
    logger.info(f"status        = {status}")

    logger.info(f"high          = {high}")
    logger.info(f"low           = {low}")

    logger.info(f"raw_event_obj = {event}")

    # --------------------------------------------------
    # TRADE TRACE
    # --------------------------------------------------
    logger.info("\n[RENDERER][TRADE] ----------------------------")

    logger.info(f"entry          = {trade.get('entry')}")
    logger.info(f"stop           = {trade.get('stop')}")
    logger.info(f"invalidation   = {trade.get('invalidation')}")
    logger.info(f"target1        = {trade.get('target1')}")
    logger.info(f"target2        = {trade.get('target2')}")
    logger.info(f"failure        = {trade.get('failure')}")
    logger.info(f"interpretation = {trade.get('interpretation')}")

    logger.info(f"raw_trade_obj  = {trade}")

    # --------------------------------------------------
    # REGIME TRACE (PURE METADATA ONLY)
    # --------------------------------------------------
    logger.info("\n[RENDERER][REGIME]")
    logger.info(f"regime = {regime}")

    logger.info("\n[RENDERER] ================= INPUT END =================\n")

    # --------------------------------------------------
    # STATE BLOCK
    # --------------------------------------------------
    if status == "FAILED":
        state_text = f"FAILED\nReason: {failure_reason}"
    elif status == "CONFIRMED":
        state_text = "CONFIRMED\nEntry trigger has been validated."
    else:
        state_text = "PENDING\nAwaiting confirmation or failure."

    # --------------------------------------------------
    # TRADE BLOCK
    # --------------------------------------------------
    if status == "FAILED":
        trade_block = "PATTERN FAILED"
    else:
        trade_block = f"""
- Trade Type: {trade_type}
- Entry: {trade.get('entry')}
- Stop: {trade.get('stop')}
- Wick Stop: {trade.get('invalidation')}
- Target 1: {trade.get('target1')}
- Target 2: {trade.get('target2')}
- Failure Condition: {trade.get('failure')}
"""

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------
    return f"""
# ==================================================
📌 INSTITUTIONAL EVENT ANALYSIS
# ==================================================

EVENT:
- Detected: {detected}
- Detected Date: {detected_date}
- Direction: {direction}
- Type: {event_type}
- Status: {status}
- Resolved Date: {resolved_date}
- Bars Active: {days_active}
- High: {high}
- Low: {low}

--------------------------------------------------
🧭 STATE
{state_text}
- Resolved Date: {resolved_date}

--------------------------------------------------
🎯 TRADE PLAN
{trade_block}

--------------------------------------------------
🧠 PATTERN INTERPRETATION 
{trade.get('interpretation', '')}

--------------------------------------------------
📊 REGIME
{regime}
"""