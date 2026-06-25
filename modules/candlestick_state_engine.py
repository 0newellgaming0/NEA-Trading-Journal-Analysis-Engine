import os
import pandas as pd
from datetime import datetime
import logging

from modules.marubozu import analyze_marubozu
from modules.harami import analyze_harami
from modules.pinbar import analyze_pinbar
from modules.dccpl import analyze_piercing_dcc
from modules.lines import analyze_candle_cluster
from modules.tweezers import analyze_tweezer
from modules.hammer import analyze_hammer
from modules.doji import analyze_doji
from modules.threesCompany import analyze_three_candle_patterns
from modules.engulfing import analyze_engulfing
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

    def __init__(self, ticker, event_store):

        self.ticker = str(ticker).upper()
        self.event_store = event_store

        logger.info(f"[ENGINE] Initialized ticker={self.ticker}")

        self.registry = {
            "Pinbar": analyze_pinbar,
            "Hammer": analyze_hammer,
            "Doji": analyze_doji,
            "Harami": analyze_harami,
            "Marubozu": analyze_marubozu,
            "Lines": analyze_candle_cluster,
            "Engulfing": analyze_engulfing,
            "Tweezers": analyze_tweezer,
            "Dark Cloud/Piercing Lines": analyze_piercing_dcc,
            "Threes Company": analyze_three_candle_patterns,
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
                raw_result = analyzer(
                    df,
                    self.event_store
                )

                normalized = normalize_output(
                    self.ticker,
                    module_name,
                    raw_result
                )

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