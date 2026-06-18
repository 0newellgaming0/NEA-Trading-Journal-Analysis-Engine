# executed_trades_notes.py

import os
import csv


def load_executed_trade_notes(EXECUTED_TRADES_NOTES_FILE):
    """
    Loads saved executed trade notes into a dictionary keyed by trade_id.
    """

    notes_map = {}

    if not os.path.exists(EXECUTED_TRADES_NOTES_FILE):
        return notes_map

    with open(EXECUTED_TRADES_NOTES_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            trade_id = row.get("trade_id", "")
            if trade_id:
                notes_map[trade_id] = row

    return notes_map


def refresh_executed_trade_context(row_data, template_ticker_var, update_template_panel):
    """
    Updates UI context when selecting an executed trade.
    """

    ticker = (
        row_data.get("Ticker")
        or row_data.get("Symbol")
        or ""
    ).strip()

    if not ticker:
        return

    try:
        template_ticker_var.set(ticker)
        update_template_panel()

    except Exception as e:
        print("Executed trade context refresh error:", e)