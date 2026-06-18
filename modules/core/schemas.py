# schemas.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class JournalRow:
    timestamp: str
    ticker: str
    account: float
    risk_dollar: float
    stop: float

    buy_now_price: float
    buy_now_shares: float
    buy_now_total: float

    ladder_1_price: float
    ladder_2_price: float
    ladder_3_price: float
    ladder_4_price: float

    trade_notes: str = ""
    analysis_notes: str = ""
    management_notes: str = ""

    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutedTrade:
    trade_id: str
    ticker: str
    placed_time: str

    notes: str = ""
    analysis_notes: str = ""
    management_notes: str = ""


@dataclass
class MarketContext:
    daily: Any = None
    weekly: Any = None
    intraday_60m: Any = None
    intraday_15m: Any = None


@dataclass
class RiskState:
    breached: bool
    distance: float
    block: str