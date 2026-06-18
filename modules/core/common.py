# common.py
import math


# =========================
# SAFE FLOAT
# =========================
def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(str(value).replace(",", "").replace("@", ""))
    except:
        return default


# =========================
# POSITION SIZING
# =========================
def calculate_position_size(risk_dollar, entry_price, stop_price):
    risk_per_share = entry_price - stop_price
    if risk_per_share <= 0:
        return 0, 0

    shares = risk_dollar / risk_per_share
    total = shares * entry_price
    return shares, total


# =========================
# RISK/REWARD
# =========================
def risk_reward(entry, stop, target):
    risk = entry - stop
    reward = target - entry

    if risk <= 0:
        return 0

    return reward / risk


# =========================
# LINEAR SLOPE (basic trend proxy)
# =========================
def slope(series):
    if len(series) < 2:
        return 0

    x1, y1 = 0, series[0]
    x2, y2 = len(series) - 1, series[-1]

    try:
        return (y2 - y1) / (x2 - x1)
    except:
        return 0


# =========================
# NORMALIZE PERCENT
# =========================
def normalize_pct(value):
    try:
        return max(0.0, min(100.0, float(value)))
    except:
        return 0.0