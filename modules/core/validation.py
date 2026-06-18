# validation.py
from constants import (
    MAX_POSITION_SIZE,
    MIN_POSITION_SIZE,
    MAX_NOTES_LENGTH
)
from common import safe_float


# =========================
# VALIDATE JOURNAL ROW
# =========================
def validate_journal_row(row: dict):
    errors = []

    if not row.get("ticker"):
        errors.append("Missing ticker")

    if safe_float(row.get("risk_dollar")) <= 0:
        errors.append("Invalid risk dollar")

    if safe_float(row.get("stop")) <= 0:
        errors.append("Invalid stop")

    if len(str(row.get("trade_notes", ""))) > MAX_NOTES_LENGTH:
        errors.append("Trade notes too long")

    return len(errors) == 0, errors


# =========================
# VALIDATE POSITION SIZE
# =========================
def validate_position_size(shares):
    try:
        shares = float(shares)
        if shares < MIN_POSITION_SIZE:
            return False, "Too small position"
        if shares > MAX_POSITION_SIZE:
            return False, "Too large position"
        return True, ""
    except:
        return False, "Invalid position size"


# =========================
# VALIDATE STOP LOGIC
# =========================
def validate_stop(entry, stop):
    try:
        return float(stop) < float(entry)
    except:
        return False