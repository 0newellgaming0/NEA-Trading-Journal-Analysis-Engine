"""
LEVEL CURVE SYSTEM
Non-linear RPG progression
"""

def xp_required_for_level(level: int) -> int:
    return int(100 * (level ** 1.6))


def get_level_from_xp(total_xp: int) -> int:
    level = 1
    remaining_xp = total_xp

    while remaining_xp >= xp_required_for_level(level):
        remaining_xp -= xp_required_for_level(level)
        level += 1

    return level