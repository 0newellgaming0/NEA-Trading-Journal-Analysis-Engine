import os
import pandas as pd
from datetime import datetime

from modules.pinbarAnalysis import analyze_pinbar
from modules.engulfingAnalysis import analyze_engulfing
from modules.insideBarAnalysis import analyze_inside_bar
from modules.hammerAnalysis import analyze_hammer
from modules.marubozuAnalysis import analyze_marubozu
from modules.starAnalysis import analyze_star_pattern
from modules.haramiAnalysis import analyze_harami_pattern
from modules.threeInsideAnalysis import analyze_three_inside_pattern
from modules.dccplAnalysis import analyze_reversal_patterns


# =========================================================
# ROOT PATH
# =========================================================
def get_project_root():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )


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

    if raw is None:
        return base_empty(ticker, module_name)

    if isinstance(raw, dict):
        return {
            "ticker": ticker,
            "module": module_name,
            "journal_prompt": str(
                raw.get(
                    "journal_prompt",
                    raw.get("prompt", "No journal prompt generated.")
                )
            ),
            "timestamp": datetime.utcnow().isoformat()
        }

    if isinstance(raw, str):
        return {
            "ticker": ticker,
            "module": module_name,
            "journal_prompt": raw,
            "timestamp": datetime.utcnow().isoformat()
        }

    return {
        "ticker": ticker,
        "module": module_name,
        "journal_prompt": str(raw),
        "timestamp": datetime.utcnow().isoformat()
    }


# =========================================================
# MAIN ENGINE
# =========================================================
class CandlestickInstitutionalStateEngine:

    def __init__(self, ticker):
        self.ticker = str(ticker).upper()

        self.registry = {
            "Pinbar": analyze_pinbar,
            "Engulfing": analyze_engulfing,
            "Inside_bar": analyze_inside_bar,
            "Hammer": analyze_hammer,
            "Marubozu": analyze_marubozu,
            "Star": analyze_star_pattern,
            "Harami": analyze_harami_pattern,
            "Three_inside": analyze_three_inside_pattern,
            "DCCPL": analyze_reversal_patterns
        }

    # =====================================================
    # RUN ALL MODULES
    # =====================================================
    def run(self, df):

        rows = []

        for module_name, analyzer in self.registry.items():

            try:
                raw_result = analyzer(df)

                row = normalize_output(
                    self.ticker,
                    module_name,
                    raw_result
                )

                rows.append(row)

            except Exception as e:
                rows.append({
                    "ticker": self.ticker,
                    "module": module_name,
                    "journal_prompt": f"ERROR: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return pd.DataFrame(rows, columns=[
            "ticker",
            "module",
            "journal_prompt",
            "timestamp"
        ])

    # =====================================================
    # EXPORT CSV → /data/candlestickAnalysis/<TICKER>/<YYYY-MM>/
    # =====================================================
    def export(self, df, filename=None):

        out = self.run(df)

        # -------------------------------------------------
        # DATE PARTITION (MONTHLY BUCKET)
        # -------------------------------------------------
        date_partition = datetime.utcnow().strftime("%Y-%m")

        # -------------------------------------------------
        # BASE ROOT PATH
        # -------------------------------------------------
        base_dir = os.path.join(
            get_project_root(),
            "data",
            "candlestickAnalysis",
            self.ticker,
            date_partition
        )

        os.makedirs(base_dir, exist_ok=True)

        # -------------------------------------------------
        # AUTO FILENAME
        # -------------------------------------------------
        if filename is None:
            filename = (
                f"{self.ticker}_candlestick_analysis_"
                f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            )

        filepath = os.path.join(base_dir, filename)

        # -------------------------------------------------
        # WRITE CSV
        # -------------------------------------------------
        out.to_csv(filepath, index=False)

        return out, filepath

    # =====================================================
    # TEXT REPORT
    # =====================================================
    def build_report(self, df):

        results = self.run(df)

        sections = []

        for _, row in results.iterrows():

            sections.append(f"""
==================================================
TICKER: {row['ticker']}
MODULE: {row['module'].upper()}
==================================================

{row['journal_prompt']}

""")

        return "\n".join(sections)