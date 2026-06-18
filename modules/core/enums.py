# enums.py
from enum import Enum, auto


class Timeframe(Enum):
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_60 = "60m"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MarketRegime(Enum):
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    EXPANSION = "expansion"
    CONTRACTION = "contraction"


class SignalType(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    HOLD = "hold"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"