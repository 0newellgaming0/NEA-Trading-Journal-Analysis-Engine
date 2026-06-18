"""
XP RULE ENGINE
Maps user actions → base XP values
"""

XP_RULES = {
    "CLICK_BUTTON": 1,
    "OPEN_FEATURE": 3,
    "OPEN_JOURNAL_ENTRY": 5,
    "CREATE_JOURNAL_ENTRY": 10,
    "ANALYZE_DATA": 10,
    "USE_CHART_TOOL": 8,
    "CREATE_TRADE": 25,
    "CLOSE_TRADE": 40,
    "ANALYZE_TRADE": 15,
    "DAILY_LOGIN": 50,
}


def calculate_xp(event) -> int:
    base = XP_RULES.get(event.event_type, 0)

    # contextual multipliers
    if event.metadata.get("high_value_action"):
        base *= 1.5

    if event.metadata.get("first_time_use"):
        base *= 2

    if event.metadata.get("streak_bonus"):
        base *= event.metadata.get("streak_bonus_multiplier", 1.0)

    return int(base)