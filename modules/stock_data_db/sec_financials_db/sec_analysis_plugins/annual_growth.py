"""
====================================================================
NEA28 ANNUAL GROWTH ENGINE

Module:
    annual_growth.py

Purpose:
    Institutional long-term SEC growth analysis.

Features:
    - Revenue CAGR
    - Earnings CAGR
    - Operating Cash Flow CAGR
    - Free Cash Flow CAGR
    - Asset CAGR
    - Equity CAGR
    - Growth acceleration analysis
    - Growth consistency scoring
    - Growth quality classification
    - Institutional maturity classification
    - Multi-year fiscal history

Used By:
    SECAnalysis
    CANSLIM Engine
    Growth Asymmetry Engine
    Institutional Ranking
====================================================================
"""

from __future__ import annotations

import logging
import pandas as pd

from modules.stock_data_db.sec_financials_db.sec_concept_resolver import (
    resolve_concepts,
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.shared_utilities import (
    find_first_available_concept,
    resolve_priority_concepts,
    get_sec_concepts,
)
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.enhanced_earnings import (
    EnhancedEarnings
)
logger = logging.getLogger("AnnualGrowth")

REVENUE_KEYS = [
    "REVENUE",
]

NET_INCOME_KEYS = [
    "NET_INCOME",
    "PROFIT_LOSS",
    "NET_INCOME_COMMON",
    "CONTINUING_OPERATIONS",
]

OPERATING_CF_KEYS = [
    "OPERATING_CASHFLOW",
]

CAPEX_KEYS = [
    "CAPEX",
]

ASSET_KEYS = [
    "TOTAL_ASSETS",
]

EQUITY_KEYS = [
    "STOCKHOLDERS_EQUITY",
]

def _normalize_concept(value):
    if not isinstance(value, str):
        return ""
    return value.split(":")[-1]


def get_metric_concepts(keys):

    try:

        resolved = resolve_concepts(keys)

        concepts = [
            _normalize_concept(x)
            for x in resolved
            if x
        ]

        if not concepts:
            logger.warning(
                "No concepts resolved for keys: %s",
                keys,
            )

        return concepts

    except Exception:

        logger.exception(
            "Concept resolution failed: %s",
            keys,
        )

        return []

def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    data = df.copy()

    data.columns = [
        str(column).strip().lower()
        for column in data.columns
    ]

    required_columns = [
        "concept",
        "numeric_value",
        "period_start",
        "period_end",
        "fiscal_year",
        "fiscal_period",
    ]

    for column in required_columns:
        if column not in data.columns:
            logger.warning(
                "Missing SEC column: %s",
                column,
            )
            return pd.DataFrame()

    data["normalized_concept"] = (
        data["concept"]
        .astype(str)
        .apply(_normalize_concept)
    )

    data["numeric_value"] = pd.to_numeric(
        data["numeric_value"],
        errors="coerce",
    )

    data["fiscal_year"] = pd.to_numeric(
        data["fiscal_year"],
        errors="coerce",
    )

    data["period_start"] = pd.to_datetime(
        data["period_start"],
        format="%Y-%m-%d",
        errors="coerce",
    )

    data["period_end"] = pd.to_datetime(
        data["period_end"],
        format="%Y-%m-%d",
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "numeric_value",
            "period_end",
            "fiscal_year",
            "fiscal_period",
        ]
    )

    data["duration_days"] = (
        data["period_end"]
        -
        data["period_start"]
    ).dt.days


    duration_records = data[
        data["fiscal_period"].eq("FY")
        &
        data["duration_days"].between(
            330,
            380
        )
    ]


    instant_records = data[
        data["period_start"].isna()
        &
        data["period_end"].notna()
    ]


    data = pd.concat(
        [
            duration_records,
            instant_records,
        ],
        ignore_index=True,
    )


    data = data.sort_values(
        [
            "normalized_concept",
            "period_end",
        ]
    )


    if data.empty:
        logger.warning(
            "No annual fiscal records found"
        )

    return data


def _extract_metric(
    df: pd.DataFrame,
    concepts,
) -> pd.DataFrame:

    data = _prepare_dataframe(df)

    if data.empty:
        return pd.DataFrame()
    
    metric = data[
        data["normalized_concept"].isin(concepts)
    ].copy()

    if metric.empty:
        logger.warning(
            "No SEC records found for concepts: %s",
            concepts,
        )
        return pd.DataFrame()

    metric["concept_rank"] = (
        metric["normalized_concept"]
        .apply(
            lambda x:
            concepts.index(x)
            if x in concepts
            else 999
        )
    )

    metric = metric[
        metric["fiscal_period"] == "FY"
    ]

    metric = metric.sort_values(
        [
            "fiscal_year",
            "concept_rank",
            "period_end",
        ],
        ascending=[
            True,
            True,
            False,
        ],
    )

    metric = metric.drop_duplicates(
        subset=[
            "fiscal_year",
        ],
        keep="first",
    )

    return metric
    
def _build_history(metric_df: pd.DataFrame):

    history = []

    if metric_df.empty:
        return history

    for _, row in metric_df.iterrows():

        history.append(
            {
                "year": int(row["fiscal_year"]),
                "value": float(row["numeric_value"]),
                "period_start": row["period_start"],
                "period_end": row["period_end"],
            }
        )

    return history


def _calculate_fcf(
    df: pd.DataFrame,
    operating_concepts,
    capex_concepts,
):

    operating = _extract_metric(
        df,
        operating_concepts,
    )

    capex = _extract_metric(
        df,
        capex_concepts,
    )

    operating_history = _build_history(
        operating
    )

    capex_history = {
        item["year"]: item["value"]
        for item in _build_history(capex)
    }

    history = []

    for item in operating_history:

        history.append(
            {
                "year": item["year"],
                "value": (
                    item["value"]
                    -
                    abs(
                        capex_history.get(
                            item["year"],
                            0,
                        )
                    )
                ),
                "period_start": item["period_start"],
                "period_end": item["period_end"],
            }
        )

    return history


class AnnualGrowthEngine:

    def analyze(self, df: pd.DataFrame):

        report = {
            "revenue": {},
            "earnings": {},
            "operating_cashflow": {},
            "free_cashflow": {},
            "assets": {},
            "equity": {},
            "growth_profile": {},
            "growth_quality": {},
            "company_stage": "UNKNOWN",
        }

        try:

            if isinstance(df, list):
                df = pd.DataFrame(df)

            if not isinstance(df, pd.DataFrame):
                logger.error(
                    "AnnualGrowth expects DataFrame"
                )
                return report

            revenue_concepts = get_metric_concepts(
                REVENUE_KEYS
            )
            earnings_engine = EnhancedEarnings()
            operating_cf_concepts = get_metric_concepts(OPERATING_CF_KEYS)
            capex_concepts = get_metric_concepts(CAPEX_KEYS)
            asset_concepts = get_metric_concepts(ASSET_KEYS)
            equity_concepts = get_metric_concepts(EQUITY_KEYS)

            revenue_history = _build_history(
                _extract_metric(
                    df,
                    revenue_concepts,
                )
            )

            earnings_report = earnings_engine.analyze(
                df,
                log_output=False,
            )

            earnings_history = []

            for item in earnings_report.get(
                "history",
                []
            ):

                if item.get("period") == "FY":

                    earnings_history.append(
                        {
                            "year": item["year"],
                            "value": item["value"],
                            "period_start": item["period_start"],
                            "period_end": item["period_end"],
                        }
                    )

            operating_history = _build_history(
                _extract_metric(
                    df,
                    operating_cf_concepts,
                )
            )

            asset_history = _build_history(
                _extract_metric(
                    df,
                    asset_concepts,
                )
            )

            equity_history = _build_history(
                _extract_metric(
                    df,
                    equity_concepts,
                )
            )

            free_cashflow_history = _calculate_fcf(
                df,
                operating_cf_concepts,
                capex_concepts,
            )

            report["revenue"] = self._build_metric(
                revenue_history
            )

            report["earnings"] = self._build_metric(
                earnings_history
            )

            report["earnings"].update(
                {
                    "latest": earnings_report.get("latest"),
                    "previous_yoy": earnings_report.get("previous_yoy"),
                    "previous_period": earnings_report.get("previous_period"),
                    "growth_pct": earnings_report.get("growth_pct"),
                    "sequential_growth_pct": earnings_report.get("sequential_growth_pct"),
                    "annual_growth_pct": earnings_report.get("annual_growth_pct"),
                    "earnings_trend": earnings_report.get("trend"),
                    "earnings_consistency": earnings_report.get("consistency"),
                }
            )

            report["operating_cashflow"] = self._build_metric(
                operating_history
            )

            report["free_cashflow"] = self._build_metric(
                free_cashflow_history
            )

            report["assets"] = self._build_metric(
                asset_history
            )

            report["equity"] = self._build_metric(
                equity_history
            )

            report["growth_profile"] = (
                self._growth_profile(
                    report
                )
            )

            report["growth_quality"] = (
                self._growth_quality(
                    report
                )
            )

            report["company_stage"] = (
                self._institutional_classification(
                    report
                )
            )

            logger.info("=" * 70)
            logger.info(
                "ANNUAL GROWTH ANALYSIS"
            )
            logger.info("=" * 70)

            for metric in (
                "revenue",
                "earnings",
                "operating_cashflow",
                "free_cashflow",
                "assets",
                "equity",
            ):

                logger.info(
                    metric.replace("_", " ").title()
                )

                logger.info(
                    "  CAGR 3Y            : %s",
                    report[metric].get("cagr3"),
                )

                logger.info(
                    "  CAGR 5Y            : %s",
                    report[metric].get("cagr5"),
                )

                logger.info(
                    "  Acceleration       : %s",
                    report[metric]
                    .get("acceleration")
                    .get("state")
                    if report[metric].get("acceleration")
                    else None,
                )

                logger.info(
                    "  Consistency        : %s",
                    report[metric]
                    .get("consistency")
                    .get("rating")
                    if report[metric].get("consistency")
                    else None,
                )

                logger.info(
                    "  Trend              : %s",
                    report[metric].get("trend"),
                )

                logger.info(
                    "  History Years      : %s",
                    len(
                        report[metric]
                        .get("history", [])
                    ),
                )

                logger.info("")

            logger.info(
                "Company Stage        : %s",
                report["company_stage"],
            )

            logger.info(
                "Growth Rate          : %s",
                report["growth_profile"]
                .get("growth_rate"),
            )

            logger.info(
                "Growth Quality       : %s",
                report["growth_quality"]
                .get("rating"),
            )

            logger.info("=" * 70)

        except Exception:
            logger.exception(
                "Annual growth analysis failed"
            )

        return report

    def _build_metric(
        self,
        history,
    ):

        cagr3 = self._cagr(
            history,
            3,
        )

        cagr5 = self._cagr(
            history,
            5,
        )

        metric = {
            "history": history,
            "cagr3": cagr3,
            "cagr5": cagr5,
            "growth_rate": self._growth_rate(cagr3),
            "acceleration": self._growth_acceleration(
                cagr3,
                cagr5,
            ),
            "consistency": self._growth_consistency(
                history
            ),
            "trend": self._trend(
                history
            ),
        }

        return metric


    def _cagr(
        self,
        history,
        years,
    ):

        if len(history) <= years:
            return None

        ordered = sorted(
            history,
            key=lambda x: x["year"],
        )

        oldest = ordered[-(years + 1)]["value"]
        latest = ordered[-1]["value"]

        if oldest <= 0 or latest <= 0:
            return None

        return (
            (
                latest / oldest
            )
            **
            (
                1 / years
            )
            -
            1
        ) * 100


    def _growth_rate(
        self,
        cagr,
    ):

        if cagr is None:
            return "UNKNOWN"

        if cagr >= 25:
            return "VERY HIGH"

        if cagr >= 10:
            return "HIGH"

        if cagr >= 5:
            return "MODERATE"

        if cagr >= 0:
            return "LOW"

        return "NEGATIVE"


    def _growth_acceleration(
        self,
        cagr3,
        cagr5,
    ):

        if cagr3 is None or cagr5 is None:
            return {
                "value": None,
                "state": "UNKNOWN",
            }

        acceleration = cagr3 - cagr5

        if acceleration >= 5:
            state = "STRONGLY ACCELERATING"

        elif acceleration >= 2:
            state = "ACCELERATING"

        elif acceleration >= -2:
            state = "STABLE"

        elif acceleration >= -5:
            state = "DECELERATING"

        else:
            state = "STRONGLY DECELERATING"

        return {
            "value": round(acceleration, 2),
            "state": state,
        }


    def _growth_consistency(
        self,
        history,
    ):

        if len(history) < 4:

            return {
                "score": 0,
                "rating": "UNKNOWN",
            }

        values = [
            item["value"]
            for item in history
        ]

        changes = []

        for i in range(
            1,
            len(values),
        ):

            previous = values[i - 1]

            if previous == 0:
                continue

            changes.append(
                (
                    values[i]
                    -
                    previous
                )
                /
                abs(previous)
                *
                100
            )

        if not changes:

            return {
                "score": 0,
                "rating": "UNKNOWN",
            }

        positive_years = sum(
            change > 0
            for change in changes
        )

        consistency = (
            positive_years
            /
            len(changes)
        )

        if consistency >= 0.85:
            rating = "HIGH"

        elif consistency >= 0.60:
            rating = "MODERATE"

        else:
            rating = "LOW"

        return {
            "score": round(
                consistency * 100,
                1,
            ),
            "rating": rating,
        }


    def _trend(self, history):

        if len(history) < 3:
            return "UNKNOWN"

        values = [
            item["value"]
            for item in history
        ]

        increases = 0
        decreases = 0

        for i in range(1,len(values)):

            if values[i] > values[i-1]:
                increases += 1

            elif values[i] < values[i-1]:
                decreases += 1


        total = increases + decreases

        if total == 0:
            return "FLAT"


        ratio = increases / total


        if ratio >= .80:
            return "COMPOUNDING"


        if ratio <= .20:
            return "DECLINING"


        return "MIXED"

    def _growth_profile(
        self,
        report,
    ):

        revenue = max(
            report["revenue"].get("cagr3") or -999,
            report["revenue"].get("cagr5") or -999,
        )

        earnings = max(
            report["earnings"].get("cagr3") or -999,
            report["earnings"].get("cagr5") or -999,
        )

        cashflow = max(
            report["operating_cashflow"].get("cagr3") or -999,
            report["operating_cashflow"].get("cagr5") or -999,
        )

        fcf = max(
            report["free_cashflow"].get("cagr3") or -999,
            report["free_cashflow"].get("cagr5") or -999,
        )

        growth_score = 0

        if revenue is not None:

            if revenue >= 25:
                growth_score += 3

            elif revenue >= 10:
                growth_score += 2

            elif revenue >= 5:
                growth_score += 1

        if earnings is not None:

            if earnings >= 25:
                growth_score += 3

            elif earnings >= 10:
                growth_score += 2

            elif earnings >= 5:
                growth_score += 1

        if cashflow is not None:

            if cashflow >= 15:
                growth_score += 2

            elif cashflow >= 5:
                growth_score += 1

        if fcf is not None:

            if fcf >= 15:
                growth_score += 2

            elif fcf >= 5:
                growth_score += 1

        if growth_score >= 8:
            rating = "HIGH GROWTH"

        elif growth_score >= 5:
            rating = "MODERATE GROWTH"

        elif growth_score >= 2:
            rating = "LOW GROWTH"

        else:
            rating = "NEGATIVE GROWTH"

        return {
            "score": growth_score,
            "growth_rate": rating,
        }


    def _growth_quality(
        self,
        report,
    ):

        score = 0

        metrics = [
            "revenue",
            "earnings",
            "operating_cashflow",
            "free_cashflow",
        ]

        consistency_scores = []

        for metric in metrics:

            data = report.get(
                metric,
                {}
            )

            consistency = data.get(
                "consistency",
                {}
            )

            consistency_score = consistency.get(
                "score",
                0,
            )

            consistency_scores.append(
                consistency_score
            )

            if consistency_score >= 85:
                score += 2

            elif consistency_score >= 60:
                score += 1


            trend = data.get(
                "trend"
            )

            if trend == "COMPOUNDING":
                score += 1

            elif trend == "DECLINING":
                score -= 1


        fcf_history = report["free_cashflow"].get(
            "history",
            []
        )

        if fcf_history:

            positive_fcf = sum(
                item["value"] > 0
                for item in fcf_history
            )

            if positive_fcf == len(fcf_history):
                score += 2

            elif positive_fcf >= len(fcf_history) / 2:
                score += 1


        revenue_cagr = report["revenue"].get("cagr3")

        if (
            score >= 10
            and revenue_cagr is not None
            and revenue_cagr >= 15
        ):
            rating = "ELITE COMPOUNDER"

        elif (
            score >= 7
            and revenue_cagr is not None
            and revenue_cagr >= 8
        ):
            rating = "HIGH QUALITY"

        elif score >= 4:
            rating = "MODERATE QUALITY"

        elif score >= 1:
            rating = "LOW QUALITY"

        else:
            rating = "POOR QUALITY"


        return {
            "score": score,
            "rating": rating,
        }

    def safe(value):
        return value if value is not None else float("-inf")
    
    def _institutional_classification(
        self,
        report,
    ):
        revenue = report["revenue"]
        earnings = report["earnings"]
        quality = report["growth_quality"]

        revenue_cagr = revenue.get("cagr3")
        earnings_cagr = earnings.get("cagr3")

        revenue_acceleration = (
            revenue.get(
                "acceleration",
                {}
            )
            .get("value")
        )

        quality_score = quality.get(
            "score",
            0,
        )

        if revenue_cagr is None:
            return "UNKNOWN"

        earnings_cagr_valid = (
            earnings_cagr
            if earnings_cagr is not None
            else -999
        )

        if (
            revenue_cagr >= 20
            and earnings_cagr_valid >= 20
            and quality_score >= 7
        ):
            return "HIGH GROWTH COMPOUNDER"

        if (
            revenue_cagr >= 10
            and earnings_cagr_valid >= 10
            and quality_score >= 7
        ):
            return "GROWTH COMPOUNDER"

        if (
            revenue_acceleration is not None
            and revenue_acceleration >= 3
        ):
            return "ACCELERATING GROWER"

        if (
            revenue_cagr >= 5
            or earnings_cagr_valid >= 5
        ):
            return "MATURE COMPOUNDER"

        if (
            revenue_cagr >= 0
            and earnings_cagr_valid >= 0
            and revenue_acceleration is not None
            and revenue_acceleration >= -2
        ):
            return "MATURE STABLE"

        if (
            revenue_cagr >= 0
            and earnings_cagr_valid >= 0
        ):
            return "MATURE DECELERATING"

        return "DETERIORATING"