from typing import List, Dict, Any
import numpy as np

# =========================================================
# SUPPORTED TIMEFRAMES
# =========================================================

TIMEFRAME_ORDER = [
    "Monthly",
    "Weekly",
    "Daily",
    "60M"
]

TIMEFRAME_RANK = {
    tf: i for i, tf in enumerate(TIMEFRAME_ORDER)
}

# =========================================================
# FRACTAL TYPES (DIRECTIONAL)
# =========================================================

FRACTAL_HIGH = "FRACTAL_HIGH"
FRACTAL_LOW = "FRACTAL_LOW"

# =========================================================
# FRACTAL DEGREE (STRUCTURAL SCALE)
# =========================================================

MINOR_FRACTAL = "MINOR"
INTERMEDIATE_FRACTAL = "INTERMEDIATE"
MAJOR_FRACTAL = "MAJOR"
PRIMARY_FRACTAL = "PRIMARY"
SUPER_FRACTAL = "SUPER"

# =========================================================
# FRACTAL FUNCTION (WYCKOFF CONTEXT ROLE)
# =========================================================

TREND_FRACTAL = "TREND_FRACTAL"
REVERSAL_FRACTAL = "REVERSAL_FRACTAL"

LIQUIDITY_FRACTAL = "LIQUIDITY_FRACTAL"
BREAK_FRACTAL = "BREAK_FRACTAL"

RETEST_FRACTAL = "RETEST_FRACTAL"
TEST_FRACTAL = "TEST_FRACTAL"

# =========================================================
# FRACTAL MARKET ROLE
# =========================================================

ACCUMULATION_FRACTAL = "ACCUMULATION_FRACTAL"
DISTRIBUTION_FRACTAL = "DISTRIBUTION_FRACTAL"

SPRING_FRACTAL = "SPRING_FRACTAL"
UTAD_FRACTAL = "UTAD_FRACTAL"

MARKUP_FRACTAL = "MARKUP_FRACTAL"
MARKDOWN_FRACTAL = "MARKDOWN_FRACTAL"

# =========================================================
# FRACTAL TIMEFRAME WEIGHT
# =========================================================

MICRO_FRACTAL = "MICRO"
LOCAL_FRACTAL = "LOCAL"
SWING_FRACTAL = "SWING"
MACRO_FRACTAL = "MACRO"

# =========================================================
# FRACTAL CONFIDENCE TIERS
# =========================================================

WEAK_FRACTAL = "WEAK"
CONFIRMED_FRACTAL = "CONFIRMED"
STRONG_FRACTAL = "STRONG"
INSTITUTIONAL_FRACTAL = "INSTITUTIONAL"

# =========================================================
# ELLIOTT WAVE LABELS
# =========================================================

IMPULSE_WAVES = ["1", "2", "3", "4", "5"]
EXTENDED_IMPULSE_WAVES = ["1", "2", "3", "4", "5", "i", "ii", "iii", "iv", "v"]

CORRECTIVE_WAVES = ["A", "B", "C"]
EXTENDED_CORRECTIVE_WAVES = ["A", "B", "C", "W", "X", "Y", "Z"]

# =========================================================
# WAVE MODES
# =========================================================

IMPULSE_MODE = "IMPULSE"
CORRECTIVE_MODE = "CORRECTIVE"
EXPANDED_CORRECTIVE_MODE = "EXPANDED_CORRECTIVE"

ACCUMULATION_WAVE_MODE = "ACCUMULATION"
DISTRIBUTION_WAVE_MODE = "DISTRIBUTION"

COMPRESSION_MODE = "COMPRESSION"
EXPANSION_MODE = "EXPANSION"

# =========================================================
# FIBONACCI CORE RATIOS
# =========================================================

FIB_RETRACEMENTS = [
    0.236,
    0.382,
    0.5,
    0.618,
    0.705,
    0.786,
    0.886
]

FIB_EXTENSIONS = [
    1.0,
    1.272,
    1.414,
    1.618,
    2.0,
    2.618,
    3.618,
    4.236
]

# =========================================================
# FIBONACCI CONFLUENCE ZONES
# =========================================================

FIB_CONFLUENCE_ZONES = {
    "deep_retrace": (0.705, 0.886),
    "standard_retrace": (0.382, 0.618),
    "shallow_retrace": (0.236, 0.382),

    "breakout_zone": (1.0, 1.272),
    "trend_extension": (1.414, 1.618),
    "trend_exhaustion": (2.618, 4.236)
}

# =========================================================
# WAVE RELATIONSHIPS
# =========================================================

WAVE_RELATION_W2 = "W2_RETRACEMENT"
WAVE_RELATION_W3 = "W3_EXTENSION"
WAVE_RELATION_W4 = "W4_CORRECTION"
WAVE_RELATION_W5 = "W5_EXHAUSTION"

WAVE_RELATION_A = "A_LEG"
WAVE_RELATION_B = "B_RETRACEMENT"
WAVE_RELATION_C = "C_IMPULSE_DOWN"

# =========================================================
# WYCKOFF EVENTS (ATOMIC LAYER)
# =========================================================

SPRING = "SPRING"
UTAD = "UTAD"

BREAKOUT = "BREAKOUT"
BREAKDOWN = "BREAKDOWN"

FALSE_BREAKOUT = "FALSE_BREAKOUT"
FALSE_BREAKDOWN = "FALSE_BREAKDOWN"

SOS = "SOS"
SOW = "SOW"

LPS = "LPS"
LPSY = "LPSY"

AR = "AUTOMATIC_RALLY"
AS = "AUTOMATIC_REACTION"

SC = "SELLING_CLIMAX"
BC = "BUYING_CLIMAX"

LIQUIDITY_SWEEP_HIGH = "LIQUIDITY_SWEEP_HIGH"
LIQUIDITY_SWEEP_LOW = "LIQUIDITY_SWEEP_LOW"

STOP_HUNT = "STOP_HUNT"

BACKUP = "BACKUP_ACTION"
TEST = "TEST"

CREEK_JUMP = "CREEK_JUMP"
ICE_BREAK = "ICE_BREAK"

# =========================================================
# PHASES (A–E)
# =========================================================

PHASE_A = "A"
PHASE_B = "B"
PHASE_C = "C"
PHASE_D = "D"
PHASE_E = "E"

# =========================================================
# SCHEMATICS
# =========================================================

ACCUMULATION = "ACCUMULATION"
DISTRIBUTION = "DISTRIBUTION"
REACCUMULATION = "REACCUMULATION"
REDISTRIBUTION = "REDISTRIBUTION"

TRANSITION = "TRANSITION"
MARKUP = "MARKUP"
MARKDOWN = "MARKDOWN"

# =========================================================
# VOLUME SYSTEM
# =========================================================

LOW_VOLUME = "LOW_VOLUME"
NORMAL_VOLUME = "NORMAL_VOLUME"
HIGH_VOLUME = "HIGH_VOLUME"
CLIMACTIC_VOLUME = "CLIMACTIC_VOLUME"

RVOL_LOW = "RVOL_LOW"
RVOL_NORMAL = "RVOL_NORMAL"
RVOL_HIGH = "RVOL_HIGH"
RVOL_EXTREME = "RVOL_EXTREME"

WEAK_PARTICIPATION = "WEAK_PARTICIPATION"
NEUTRAL_PARTICIPATION = "NEUTRAL_PARTICIPATION"
STRONG_PARTICIPATION = "STRONG_PARTICIPATION"
INSTITUTIONAL_PARTICIPATION = "INSTITUTIONAL_PARTICIPATION"

VOLUME_EXPANDING = "VOLUME_EXPANDING"
VOLUME_CONTRACTING = "VOLUME_CONTRACTING"
VOLUME_NEUTRAL = "VOLUME_NEUTRAL"

PRICE_UP_VOLUME_UP = "PRICE_UP_VOLUME_UP"
PRICE_UP_VOLUME_DOWN = "PRICE_UP_VOLUME_DOWN"
PRICE_DOWN_VOLUME_UP = "PRICE_DOWN_VOLUME_UP"
PRICE_DOWN_VOLUME_DOWN = "PRICE_DOWN_VOLUME_DOWN"

ABSORPTION_VOLUME = "ABSORPTION_VOLUME"
DISTRIBUTION_VOLUME = "DISTRIBUTION_VOLUME"
ACCUMULATION_VOLUME = "ACCUMULATION_VOLUME"

EFFORT_RESULT_CONFIRMATION = "EFFORT_RESULT_CONFIRMATION"
EFFORT_RESULT_DIVERGENCE = "EFFORT_RESULT_DIVERGENCE"

CONFIRMED_BREAKOUT_VOLUME = "CONFIRMED_BREAKOUT_VOLUME"
WEAK_BREAKOUT_VOLUME = "WEAK_BREAKOUT_VOLUME"

CONFIRMED_BREAKDOWN_VOLUME = "CONFIRMED_BREAKDOWN_VOLUME"
WEAK_BREAKDOWN_VOLUME = "WEAK_BREAKDOWN_VOLUME"

SPRING_VOLUME_CONFIRMATION = "SPRING_VOLUME_CONFIRMATION"
UTAD_VOLUME_CONFIRMATION = "UTAD_VOLUME_CONFIRMATION"

NO_VOLUME_CONFIRMATION = "NO_VOLUME_CONFIRMATION"

INSTITUTIONAL_ACCUMULATION = "INSTITUTIONAL_ACCUMULATION"
INSTITUTIONAL_DISTRIBUTION = "INSTITUTIONAL_DISTRIBUTION"

ABSORPTION_DETECTED = "ABSORPTION_DETECTED"

SUPPLY_OVERCOMING_DEMAND = "SUPPLY_OVERCOMING_DEMAND"
DEMAND_OVERCOMING_SUPPLY = "DEMAND_OVERCOMING_SUPPLY"

WEAK_VOLUME_SIGNAL = "WEAK_VOLUME_SIGNAL"
MODERATE_VOLUME_SIGNAL = "MODERATE_VOLUME_SIGNAL"
STRONG_VOLUME_SIGNAL = "STRONG_VOLUME_SIGNAL"
INSTITUTIONAL_VOLUME_SIGNAL = "INSTITUTIONAL_VOLUME_SIGNAL"

HTF_VOLUME_ALIGNED = "HTF_VOLUME_ALIGNED"
HTF_VOLUME_CONFLICT = "HTF_VOLUME_CONFLICT"

MTF_VOLUME_CONFIRMATION = "MTF_VOLUME_CONFIRMATION"
MTF_VOLUME_DIVERGENCE = "MTF_VOLUME_DIVERGENCE"

# =========================================================
# SAFE HELPERS
# =========================================================

def safe_float(value, default=0.0):
    try:
        return float(value)
    except:
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def safe_mean(arr):
    try:
        if arr is None:
            return 0.0
        arr = np.asarray(arr, dtype=float)
        return float(np.nanmean(arr)) if len(arr) else 0.0
    except:
        return 0.0


def safe_std(arr):
    try:
        arr = np.asarray(arr, dtype=float)
        return float(np.nanstd(arr)) if len(arr) else 0.0
    except:
        return 0.0


def safe_slope(arr):
    try:
        arr = np.asarray(arr, dtype=float)
        if len(arr) < 2:
            return 0.0
        return float(np.polyfit(np.arange(len(arr)), arr, 1)[0])
    except:
        return 0.0


def clamp_confidence(value):
    try:
        return float(np.clip(value, 0.0, 1.0))
    except:
        return 0.0