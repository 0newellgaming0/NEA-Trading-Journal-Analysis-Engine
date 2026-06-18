from dataclasses import dataclass, field
from typing import List, Dict, Any
import pandas as pd

@dataclass
class ManipulationEvent:
    event_type: str
    index: int
    timestamp: Any
    price: float
    timeframe: str
    confidence: float = 0.0
    volume_confirmed: bool = False
    metadata: Dict = field(default_factory=dict)
    
# =========================================================
# FRACTAL POINT (STRUCTURAL ANCHOR)
# =========================================================

@dataclass
class FractalPoint:
    index: int
    timestamp: Any
    price: float
    fractal_type: str
    degree: str
    timeframe: str
    strength: float = 0.0
    metadata: Dict = field(default_factory=dict)


# =========================================================
# TRADING RANGE (STRUCTURAL ZONE)
# =========================================================

@dataclass
class TradingRange:
    start_index: int
    end_index: int
    range_high: float
    range_low: float
    timeframe: str
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


# =========================================================
# ELLIOTT WAVE STRUCTURE (FIB CORE ONLY)
# =========================================================

@dataclass
class ElliottWave:
    label: str
    start_index: int
    end_index: int
    start_price: float
    end_price: float
    timeframe: str
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


# =========================================================
# EVENTS (ALL WYCKOFF ATOMIC EVENTS)
# =========================================================

@dataclass
class MarketEvent:
    event_type: str
    index: int
    timestamp: Any
    price: float
    timeframe: str
    confidence: float = 0.0
    volume_confirmed: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class BreakoutEvent:
    event_type: str
    index: int
    timestamp: Any
    price: float
    breakout_level: float
    timeframe: str
    confidence: float = 0.0
    volume_confirmed: bool = False
    institutional_confirmed: bool = False
    metadata: Dict = field(default_factory=dict)


# =========================================================
# PHASE MODEL (WYCKOFF STRUCTURAL PHASES A–E)
# =========================================================

@dataclass
class WyckoffPhase:
    label: str   # A, B, C, D, E
    name: str    # expansion / breakout / test etc
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


# =========================================================
# SCHEMATIC MODEL (REGIME CONTAINER)
# =========================================================

@dataclass
class MarketSchematic:
    accumulation: bool = False
    distribution: bool = False
    reaccumulation: bool = False
    redistribution: bool = False
    transition: bool = False


# =========================================================
# TIMEFRAME CONTEXT (PIPELINE CANONICAL STATE OBJECT)
# =========================================================

@dataclass
class TimeframeContext:
    timeframe: str
    data: pd.DataFrame

    # -------------------------
    # CORE STRUCTURES
    # -------------------------
    fractals: List[FractalPoint] = field(default_factory=list)
    ranges: List[TradingRange] = field(default_factory=list)
    waves: List[ElliottWave] = field(default_factory=list)

    # -------------------------
    # EVENTS (TYPE-SAFE)
    # -------------------------
    events: List[MarketEvent] = field(default_factory=list)

    springs: List[ManipulationEvent] = field(default_factory=list)
    utads: List[ManipulationEvent] = field(default_factory=list)

    breakouts: List[BreakoutEvent] = field(default_factory=list)
    breakdowns: List[BreakoutEvent] = field(default_factory=list)

    false_breakouts: List[BreakoutEvent] = field(default_factory=list)
    false_breakdowns: List[BreakoutEvent] = field(default_factory=list)

    # -------------------------
    # WYCKOFF PHASES
    # -------------------------
    phases: List[WyckoffPhase] = field(default_factory=list)

    # -------------------------
    # SCHEMATICS (REGIMES)
    # -------------------------
    schematic: MarketSchematic = field(default_factory=MarketSchematic)

    # -------------------------
    # OUTPUT STATE
    # -------------------------
    score: float = 0.0
    bias: str = "NEUTRAL"