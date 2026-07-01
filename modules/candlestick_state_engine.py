import os
import pandas as pd
from datetime import datetime
import logging
from modules.path_resolver import get_signals_db_path
from modules.signals_repository import SignalsRepository

from modules.marubozu import analyze_marubozu
from modules.harami import analyze_harami
from modules.pinbar import analyze_pinbar
from modules.dccpl import analyze_piercing_dcc
from modules.lines import analyze_candle_cluster
from modules.tweezers import analyze_tweezer
from modules.hammer import analyze_hammer
from modules.doji import analyze_doji
from modules.tline import analyze_tline
from modules.threesCompany import analyze_three_candle_patterns
from modules.star import analyze_star_patterns
from modules.threeMethods import analyze_three_methods 
from modules.dojiSandwich import analyze_doji_sandwich
from modules.thrustDelib import analyze_thrust_deliberation
from modules.tasuki import analyze_tasuki_gap
from modules.engulfing import analyze_engulfing 
from modules.insideBar import analyze_insidebar 
from modules.stochastics import analyze_stoch
from modules.alligator import analyze_alligator 
from modules.spring import analyze_wyckoff_c
from modules.test import analyze_wyckoff_t 
from modules.lps import analyze_wyckoff_expansion 
from modules.volume import analyze_extreme_volume 
from modules.rsi import analyze_rsi  
from modules.macd import analyze_macd  
from modules.vwap import analyze_vwap  
from modules.kickers import analyze_kickers
from modules.ema20 import analyze_ema20
from modules.ema50 import analyze_ema50
from modules.ema200 import analyze_ema200
from modules.flag import analyze_pullback
from modules.fibonacci import analyze_fibonacci
from modules.candle import analyze_candle_over_candle
from modules.kikkake import analyze_kikkake
from modules.matHold import analyze_mat_hold


from modules.ohlcv_normalizer import normalize_timestamp
from modules.renderer import format_event_journal_prompt

logger = logging.getLogger("candlestick_engine")


# =========================================================
# ROOT PATH
# =========================================================
def get_project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_analysis_data_path():
    return os.path.join(get_project_root(), "data")


# =========================================================
# EMPTY RESULT
# =========================================================
def base_empty(ticker, module_name):
    return {
        "ticker": ticker,
        "module": module_name,
        "journal_prompt": "No analysis generated.",
        "timestamp": datetime.utcnow().isoformat()
    }


# =========================================================
# NORMALIZER
# =========================================================
def normalize_output(ticker, module_name, raw):

    logger.info(f"[NORMALIZER] module={module_name} raw_type={type(raw)}")

    if raw is None:
        return base_empty(ticker, module_name)

    if not isinstance(raw, dict):
        raw = {"journal_prompt": str(raw)}

    event = raw.get("event", {}) or {}
    trade = raw.get("trade", {}) or {}

    normalized_event = {
        "id": event.get("id"),
        "index": event.get("index"),
        "date": event.get("date"),
        "resolved_date": event.get("resolved_date"),
        "days_active": event.get("days_active", 0),
        "status_reason": event.get("status_reason"),

        "detected": event.get("detected"),
        "type": event.get("type"),
        "status": event.get("status"),

        "direction": event.get("direction"),
        "trade_type": event.get("trade_type"),

        "high": event.get("high"),
        "low": event.get("low")
    }

    return {
        "ticker": ticker,
        "module": module_name,
        "event": normalized_event,
        "trade": trade,
        "regime": raw.get("regime", "UNKNOWN"),
        "journal_prompt": format_event_journal_prompt(raw),
        "timestamp": datetime.utcnow().isoformat()
    }


# =========================================================
# VALIDATION
# =========================================================
def validate_ohlcv(df):
    required = ["Open", "High", "Low", "Close", "Volume"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"❌ OHLCV contract violation. Missing: {missing}")


# =========================================================
# ENGINE
# =========================================================
class CandlestickInstitutionalStateEngine:

    def __init__(self, ticker, event_store, signals_repo=None):

        self.ticker = str(ticker).upper()
        self.event_store = event_store

        # 🔥 FORCE SIGNALS DB CREATION IF NOT PROVIDED
        if signals_repo is None:
            db_path = get_signals_db_path()
            signals_repo = SignalsRepository(db_path)

        self.signals_repo = signals_repo

        logger.info(f"[ENGINE] Initialized ticker={self.ticker}")

        self.registry = { 
            "EMA 200": analyze_ema200,
            "EMA 50": analyze_ema50,
            "EMA 20": analyze_ema20,
            "T Line": analyze_tline, 
            "Fibonacci": analyze_fibonacci,
            "Flags": analyze_pullback, 
            "Alligator": analyze_alligator, 
            "Volume": analyze_extreme_volume,
            "RSI 50": analyze_rsi, 
            "Stochastics": analyze_stoch, 
            "MACD": analyze_macd, 
            "VWAP": analyze_vwap, 
            "Mat Hold": analyze_mat_hold,
            "Kikakke": analyze_kikkake,
            "Candle Over Candle": analyze_candle_over_candle,
            "Doji": analyze_doji,
            "Doji Sandwiches": analyze_doji_sandwich,
            "Kickers": analyze_kickers,
            "Three Methods": analyze_three_methods,
            "Threes Company": analyze_three_candle_patterns,
            "Stars": analyze_star_patterns,
            "Tasuki Gaps": analyze_tasuki_gap,
            "Harami": analyze_harami,
            "Marubozu": analyze_marubozu,
            "Lines": analyze_candle_cluster,
            "Engulfing": analyze_engulfing,
            "Inside Bars": analyze_insidebar,
            "Tweezers": analyze_tweezer,
            "Dark Cloud/Piercing Lines": analyze_piercing_dcc,
            "Hammer": analyze_hammer,
            "Thrust/Deliberation": analyze_thrust_deliberation,
            "Spring Detector": analyze_wyckoff_c,
            "Test Detector": analyze_wyckoff_t, 
            "LPS Detector": analyze_wyckoff_expansion,
            "Pinbar": analyze_pinbar,

        }

        logger.info(f"[ENGINE] Registered modules={list(self.registry.keys())}")


    # =====================================================
    # RUN ALL MODULES (NO CONTEXT)
    # =====================================================
    def run(self, df):

        logger.info(f"[ENGINE] run() ticker={self.ticker}")

        df = normalize_timestamp(df)
        validate_ohlcv(df)

        rows = []

        for module_name, analyzer in self.registry.items():

            logger.info(f"[ENGINE] Running module={module_name}")

            try:
                raw_result = analyzer(df, self.event_store)

                normalized = normalize_output(
                    self.ticker,
                    module_name,
                    raw_result
                )

                # =====================================================
                # SIGNALS PERSISTENCE HOOK (NON-BREAKING)
                # =====================================================
                if self.signals_repo is not None:

                    event = normalized.get("event", {}) or {}
                    trade = normalized.get("trade", {}) or {}

                    try:
                        self.signals_repo.insert_signal(

                            ticker=self.ticker,
                            timeframe="AUTO",
                            module=module_name,

                            # EVENT FIELDS
                            detected=event.get("detected"),
                            detected_date=event.get("date"),
                            direction=event.get("direction"),
                            event_type=event.get("type"),
                            status=event.get("status"),
                            resolved_date=event.get("resolved_date"),
                            bars_active=event.get("days_active"),
                            high=event.get("high"),
                            low=event.get("low"),
                            trade_type=event.get("trade_type"),

                            # TRADE FIELDS
                            entry=trade.get("entry"),
                            stop=trade.get("stop"),
                            wick_stop=trade.get("invalidation"),
                            target1=trade.get("target1"),
                            target2=trade.get("target2"),
                            failure_condition=trade.get("failure"),

                            # STATE + REGIME
                            state=normalized.get("state", "UNKNOWN"),
                            regime=normalized.get("regime"),

                            timestamp=normalized.get("timestamp")
                        )

                    except Exception:
                        logger.exception(f"[SIGNALS DB] insert failed for {module_name}")

                normalized.setdefault("journal_prompt", "")
                normalized.setdefault("ticker", self.ticker)
                normalized.setdefault("module", module_name)

                rows.append(normalized)

            except Exception as e:

                logger.exception(f"[ENGINE] {module_name} FAILED")

                rows.append({
                    "ticker": self.ticker,
                    "module": module_name,
                    "event": {},
                    "trade": {},
                    "regime": "ERROR",
                    "journal_prompt": f"ERROR: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return pd.DataFrame(rows)


    # =====================================================
    # EXPORT
    # =====================================================
    def export(self, df, filename=None):

        modules = self.run(df)

        date_partition = datetime.utcnow().strftime("%Y-%m")

        base_dir = os.path.join(
            get_project_root(),
            "data",
            "candlestickAnalysis",
            self.ticker,
            date_partition
        )

        os.makedirs(base_dir, exist_ok=True)

        if filename is None:
            filename = f"{self.ticker}_candlestick_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = os.path.join(base_dir, filename)

        modules.to_csv(filepath, index=False)

        return modules, filepath


    # =====================================================
    # REPORT
    # =====================================================
    def build_report(self, df):

        modules = self.run(df)

        sections = []

        for _, row in modules.iterrows():

            sections.append(f"""
==================================================
TICKER: {row['ticker']}
MODULE: {row['module'].upper()}
==================================================

{row.get('journal_prompt', '')}
""")

        return "\n".join(sections)