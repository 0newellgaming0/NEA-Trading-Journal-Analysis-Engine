# constants.py

# =========================
# RISK MODEL DEFAULTS
# =========================
DEFAULT_RISK_PER_TRADE = 0.01  # 1%

# =========================
# LIQUIDITY / VOLUME THRESHOLDS
# =========================
RVOL_MIN_ACCUMULATION = 1.5
RVOL_BREAKOUT = 3.0
RVOL_EXPLOSION = 5.0

FLOAT_LOW = 20_000_000
FLOAT_VERY_LOW = 10_000_000

SHARES_OUTSTANDING_LOW = 75_000_000

# =========================
# MOMENTUM THRESHOLDS
# =========================
RSI_OVERBOUGHT = 80
RSI_OVERSOLD = 20

EMA_TLINE_PERIOD = 8

# =========================
# WYCKOFF STRUCTURE CONSTANTS
# =========================
WYCKOFF_RETEST_TOLERANCE = 0.02
SPRING_VOLUME_MULTIPLIER = 1.8

# =========================
# POSITION SIZING SAFETY
# =========================
MIN_POSITION_SIZE = 1
MAX_POSITION_SIZE = 1_000_000

# =========================
# JOURNAL LIMITS
# =========================
MAX_NOTES_LENGTH = 50_000