"""
====================================================================
NEA28 ENHANCED EARNINGS ENGINE

Module:
    enhanced_earnings.py

Purpose:
    Institutional SEC earnings analysis.

Features:
    - SEC XBRL earnings extraction
    - Same-period YoY growth
    - Sequential QoQ growth
    - Annual fiscal growth
    - Earnings trend classification
    - Earnings consistency analysis
    - Multi-period history

Used By:
    SECAnalysis
    SECAnalysisExtensions
    CANSLIM Engine
    Growth Asymmetry Engine
====================================================================
"""

from __future__ import annotations

import logging
import pandas as pd

from modules.stock_data_db.sec_financials_db.sec_concept_resolver import (
    resolve_concepts
)

logger = logging.getLogger("Earnings")

EARNINGS_CONCEPT_KEYS = [
    "NET_INCOME",
    "PROFIT_LOSS",
    "NET_INCOME_COMMON",
    "CONTINUING_OPERATIONS",
]

PERIOD_ORDER = {
    "Q1": 1,
    "Q2": 2,
    "Q3": 3,
    "Q4": 4,
    "FY": 5
}

def _normalize_concept(value):
    if not isinstance(value, str):
        return ""
    return value.split(":")[-1]


resolved = resolve_concepts(
    EARNINGS_CONCEPT_KEYS
)

EARNINGS_CONCEPTS = [
    _normalize_concept(x)
    for x in resolved
    if x
]

def _extract_earnings(df: pd.DataFrame) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    earnings = df.copy()

    earnings.columns = [
        str(c).strip().lower()
        for c in earnings.columns
    ]

    if "concept" not in earnings.columns:
        return pd.DataFrame()

    earnings["normalized_concept"] = (
        earnings["concept"]
        .astype(str)
        .apply(_normalize_concept)
    )

    earnings = earnings[
        earnings["normalized_concept"].isin(
            EARNINGS_CONCEPTS
        )
    ].copy()

    if earnings.empty:
        return pd.DataFrame()

    if "_statement_type" in earnings.columns:

        income = earnings[
            earnings["_statement_type"]
            .fillna("")
            .str.lower()
            .str.contains("income")
        ]

        if not income.empty:
            earnings = income.copy()

    required = [
        "numeric_value",
        "period_start",
        "period_end",
        "fiscal_year",
        "fiscal_period"
    ]

    for column in required:

        if column not in earnings.columns:
            return pd.DataFrame()

    earnings["numeric_value"] = pd.to_numeric(
        earnings["numeric_value"],
        errors="coerce"
    )

    earnings["fiscal_year"] = pd.to_numeric(
        earnings["fiscal_year"],
        errors="coerce"
    )

    earnings["period_end"] = pd.to_datetime(
        earnings["period_end"],
        errors="coerce"
    )

    def resolve_fiscal_year(row):

        period = row["fiscal_period"]

        if period == "FY":
            return int(row["period_end"].year)

        if pd.isna(row["period_end"]):
            return None

        quarter_end = row["period_end"]

        if period in ("Q1", "Q2", "Q3", "Q4"):

            return int(
                quarter_end.year
            )

        return int(
            quarter_end.year
        )

    earnings["fiscal_year"] = earnings.apply(
        resolve_fiscal_year,
        axis=1
    )

    earnings["period_start"] = pd.to_datetime(
        earnings["period_start"],
        errors="coerce"
    )

    earnings["period_end"] = pd.to_datetime(
        earnings["period_end"],
        errors="coerce"
    )

    earnings = earnings.dropna(
        subset=[
            "numeric_value",
            "period_start",
            "period_end",
            "fiscal_year",
            "fiscal_period"
        ]
    )

    earnings["duration_days"] = (
        earnings["period_end"]
        -
        earnings["period_start"]
    ).dt.days

    quarterly_filter = (
        earnings["fiscal_period"].isin(
            [
                "Q1",
                "Q2",
                "Q3",
                "Q4"
            ]
        )
        &
        earnings["duration_days"].between(
            70,
            110
        )
    )

    annual_filter = (
        earnings["fiscal_period"].eq("FY")
        &
        earnings["duration_days"].between(
            330,
            380
        )
    )

    earnings = earnings[
        quarterly_filter | annual_filter
    ]

    if earnings.empty:
        return earnings

    concept_priority = {
        concept: index
        for index, concept in enumerate(EARNINGS_CONCEPTS)
    }

    earnings["concept_rank"] = (
        earnings["normalized_concept"]
        .map(concept_priority)
        .fillna(999)
    )

    preferred = (
        earnings
        .sort_values(
            [
                "concept_rank",
                "period_end"
            ],
            ascending=[
                True,
                False
            ]
        )
        .iloc[0]["normalized_concept"]
    )

    earnings = earnings[
        earnings["normalized_concept"]
        ==
        preferred
    ]

    earnings = earnings.sort_values(
        [
            "period_end",
            "fiscal_year",
            "duration_days"
        ],
        ascending=[
            False,
            False,
            True
        ]
    )

    earnings = earnings.drop_duplicates(
        subset=[
            "period_end",
            "fiscal_period",
            "fiscal_year"
        ],
        keep="first"
    )

    return earnings


class EnhancedEarnings:

    def analyze(
    self,
    df: pd.DataFrame,
    log_output=True,
):

        report = {
            "latest": None,
            "previous_yoy": None,
            "previous_period": None,
            "growth_pct": None,
            "sequential_growth_pct": None,
            "annual_growth_pct": None,
            "trend": "UNKNOWN",
            "consistency": "UNKNOWN",
            "history": []
        }

        try:
            
            if isinstance(df, list):
                df = pd.DataFrame(df)

            if not isinstance(df, pd.DataFrame):
                logger.error(
                    "Enhanced earnings expects DataFrame"
                )
                return report
            
            earnings = _extract_earnings(df)

            if earnings.empty:
                logger.warning("No earnings facts found")
                return report

            history = []

            for _, row in earnings.iterrows():
                history.append(
                    {
                        "year": int(row["fiscal_year"]),
                        "period": row["fiscal_period"],
                        "value": float(row["numeric_value"]),
                        "period_end": row["period_end"],
                        "period_start": row["period_start"]
                    }
                )

            latest = history[0]

            previous_yoy = next(
                (
                    item
                    for item in history[1:]
                    if (
                        item["period"] == latest["period"]
                        and
                        300 <= abs(
                            (
                                latest["period_end"]
                                -
                                item["period_end"]
                            ).days
                        ) <= 400
                    )
                ),
                None
            )
            previous_period = None

            quarterly = [
                item
                for item in history
                if item["period"] in (
                    "Q1",
                    "Q2",
                    "Q3",
                    "Q4"
                )
            ]

            for item in quarterly:

                if item["period_end"] >= latest["period_end"]:
                    continue

                previous_period = item
                break

            growth_pct = self._growth(
                latest,
                previous_yoy
            )

            sequential_growth_pct = self._growth(
                latest,
                previous_period
            )

            annual_growth_pct = self._annual_growth(
                history
            )

            report.update(
                {
                    "latest": latest,
                    "previous_yoy": previous_yoy,
                    "previous_period": previous_period,
                    "growth_pct": growth_pct,
                    "sequential_growth_pct": sequential_growth_pct,
                    "annual_growth_pct": annual_growth_pct,
                    "trend": self._trend(growth_pct),
                    "consistency": self._consistency(history),
                    "history": history
                }
            )
            if log_output:
                logger.info("=" * 70)
                logger.info("ENHANCED EARNINGS ANALYSIS")
                logger.info("=" * 70)

                logger.info("Latest Earnings")
                logger.info("  Year                : %s", latest.get("year"))
                logger.info("  Period              : %s", latest.get("period"))
                logger.info("  Value               : %s", latest.get("value"))

                logger.info("-" * 70)
                logger.info("Previous YoY")
                logger.info("  Year                : %s", previous_yoy.get("year") if previous_yoy else None)
                logger.info("  Period              : %s", previous_yoy.get("period") if previous_yoy else None)
                logger.info("  Value               : %s", previous_yoy.get("value") if previous_yoy else None)

                logger.info("-" * 70)
                logger.info("Previous Period")
                logger.info("  Year                : %s", latest.get("year"))
                logger.info("  Period              : %s", previous_period.get("period") if previous_period else None)
                logger.info("  Value               : %s", previous_period.get("value") if previous_period else None)

                logger.info("-" * 70)
                logger.info("Growth")
                logger.info("  YoY Growth          : %.2f%%", growth_pct if growth_pct is not None else 0)
                logger.info("  Sequential Growth   : %.2f%%", sequential_growth_pct if sequential_growth_pct is not None else 0)
                logger.info("  Annual Growth       : %.2f%%", annual_growth_pct if annual_growth_pct is not None else 0)

                logger.info("-" * 70)
                logger.info("Earnings Quality")
                logger.info("  Trend               : %s", report["trend"])
                logger.info("  Consistency         : %s", report["consistency"])
                logger.info("  History Periods     : %s", len(history))

                logger.info("=" * 70)

        except Exception:
            logger.exception(
                "Enhanced earnings analysis failed"
            )

        return report


    def _growth(self, current, previous):

        if not previous:
            return None

        if previous["value"] == 0:
            return None

        return (
            (
                current["value"]
                -
                previous["value"]
            )
            /
            abs(previous["value"])
        ) * 100


    def _annual_growth(self, history):

        years = {}

        for item in history:

            if item["period"] == "FY":
                years[item["year"]] = item

        if len(years) < 2:
            return None

        ordered = sorted(
            years.keys(),
            reverse=True
        )

        return self._growth(
            years[ordered[0]],
            years[ordered[1]]
        )


    def _trend(self, growth):

        if growth is None:
            return "UNKNOWN"

        if growth >= 15:
            return "STRONG UP"

        if growth >= 5:
            return "UP"

        if growth <= -15:
            return "STRONG DOWN"

        if growth <= -5:
            return "DOWN"

        return "STABLE"


    def _consistency(self, history):

        quarterly = [
            x
            for x in history
            if x["period"] in (
                "Q1",
                "Q2",
                "Q3",
                "Q4"
            )
        ]

        values = [
            x["value"]
            for x in quarterly[:8]
        ]

        if len(values) < 4:
            return "UNKNOWN"

        increases = sum(
            values[i] > values[i + 1]
            for i in range(
                len(values) - 1
            )
        )

        ratio = increases / (
            len(values) - 1
        )

        if ratio >= 0.80:
            return "EXCELLENT"

        if ratio >= 0.60:
            return "GOOD"

        if ratio >= 0.40:
            return "MIXED"

        return "DECLINING"