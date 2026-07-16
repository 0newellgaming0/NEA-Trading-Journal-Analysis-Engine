"""
====================================================================
NEA28 SEC FINANCIAL INTELLIGENCE SYSTEM

Module:
    enhanced_earnings.py

Purpose:
    Institutional-grade SEC earnings intelligence engine.

Responsibilities:
    - Extract SEC earnings concepts through resolver
    - Build earnings history
    - Analyze latest earnings
    - Calculate quarterly growth
    - Calculate annual growth
    - Prepare earnings intelligence output

Architecture:
    SECAnalysisExtensions
            |
            v
    enhanced_earnings.py
            |
            v
    downstream scoring engines

====================================================================
"""

import logging
import pandas as pd

from .shared_utilities import (
    validate_dataframe,
    normalize_sec_columns,
    normalize_concepts,
    clean_numeric_values,
    resolve_plugin_concepts,
    resolve_duplicate_facts,
    validate_quarter_period,
    validate_annual_period,
    filter_reporting_periods,
    calculate_growth,
    calculate_cagr,
    build_financial_history,
    empty_plugin_output,
    classify_growth,
)


logger = logging.getLogger(__name__)


class EnhancedEarnings:
    """
    Foundational SEC earnings intelligence engine.
    """

    EARNINGS_KEYS = [
        "NET_INCOME",
        "PROFIT_LOSS",
        "EPS_BASIC",
        "EPS_DILUTED",
        "WEIGHTED_SHARES_BASIC",
        "WEIGHTED_SHARES_DILUTED",
    ]


    EARNINGS_PRIORITY = [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
        "IncomeLossFromContinuingOperations",
    ]


    def __init__(
        self,
        resolver=None,
    ):
        self.resolver = resolver


    # ==============================================================
    # MAIN ENTRY POINT
    # ==============================================================

    def analyze(
        self,
        sec_data,
    ):

        logger.info(
            "Running Enhanced Earnings Analysis"
        )

        output = empty_plugin_output(
            "enhanced_earnings"
        )

        try:

            if not validate_dataframe(
                sec_data
            ):
                return output


            data = normalize_sec_columns(
                sec_data.copy()
            )


            data = normalize_concepts(
                data
            )


            if "numeric_value" in data.columns:

                data["numeric_value"] = (
                    data["numeric_value"]
                    .apply(
                        clean_numeric_values
                    )
                )


            concepts = (
                self._resolve_earnings_concepts()
            )


            earnings_data = (
                self._extract_earnings_data(
                    data,
                    concepts,
                )
            )


            if earnings_data.empty:

                return output


            quarterly = (
                self._build_quarter_history(
                    earnings_data
                )
            )


            annual = (
                self._build_annual_history(
                    earnings_data
                )
            )


            history = (
                self._select_history(
                    quarterly,
                    annual,
                )
            )


            latest = (
                self._latest_earnings(
                    history
                )
            )


            growth = (
                self._calculate_growth_metrics(
                    quarterly,
                    annual,
                )
            )


            output.update(
                {
                    "latest_earnings": latest,
                    "growth": growth,
                    "history": history,
                    "score": {},
                }
            )


            return output


        except Exception:

            logger.exception(
                "Enhanced Earnings failed"
            )

            return output


    # ==============================================================
    # CONCEPT RESOLUTION
    # ==============================================================

    def _resolve_earnings_concepts(self):

        return resolve_plugin_concepts(
            self.EARNINGS_KEYS,
            self.resolver,
        )


    # ==============================================================
    # DATA EXTRACTION
    # ==============================================================

    def _extract_earnings_data(
        self,
        df,
        concepts,
    ):

        if not concepts:

            return pd.DataFrame()


        result = df[
            df["concept"].isin(
                concepts
            )
        ].copy()


        if result.empty:

            return result


        result = resolve_duplicate_facts(
            result,
            self.EARNINGS_PRIORITY,
        )


        return result


    # ==============================================================
    # QUARTERLY HISTORY
    # ==============================================================

    def _build_quarter_history(
        self,
        df,
    ):

        records = []


        for _, row in df.iterrows():

            start = row.get(
                "period_start"
            )

            end = row.get(
                "period_end"
            )


            try:

                days = (
                    pd.to_datetime(end)
                    -
                    pd.to_datetime(start)
                ).days


            except Exception:

                continue


            if not validate_quarter_period(
                days
            ):
                continue


            records.append(
                {
                    "year":
                        row.get(
                            "fiscal_year"
                        ),

                    "period":
                        row.get(
                            "fiscal_period"
                        ),

                    "value":
                        row.get(
                            "numeric_value"
                        ),

                    "period_start":
                        start,

                    "period_end":
                        end,
                }
            )


        return self._sort_history(
            records
        )


    # ==============================================================
    # ANNUAL HISTORY
    # ==============================================================

    def _build_annual_history(
        self,
        df,
    ):

        records = []


        for _, row in df.iterrows():

            start = row.get(
                "period_start"
            )

            end = row.get(
                "period_end"
            )


            try:

                days = (
                    pd.to_datetime(end)
                    -
                    pd.to_datetime(start)
                ).days


            except Exception:

                continue


            if not validate_annual_period(
                days
            ):
                continue


            records.append(
                {
                    "year":
                        row.get(
                            "fiscal_year"
                        ),

                    "period":
                        row.get(
                            "fiscal_period"
                        ),

                    "value":
                        row.get(
                            "numeric_value"
                        ),

                    "period_start":
                        start,

                    "period_end":
                        end,
                }
            )


        return self._sort_history(
            records
        )
        
    # ==============================================================
    # HISTORY UTILITIES
    # ==============================================================

    def _sort_history(
        self,
        records,
    ):

        if not records:
            return []

        records = sorted(
            records,
            key=lambda x: (
                x.get("year") or 0,
                x.get("period_end") or "",
            )
        )

        return build_financial_history(
            records
        )


    def _select_history(
        self,
        quarterly,
        annual,
    ):

        if quarterly:

            return quarterly

        return annual


    # ==============================================================
    # LATEST EARNINGS
    # ==============================================================

    def _latest_earnings(
        self,
        history,
    ):

        if not history:

            return {
                "value": 0,
                "period": "",
                "fiscal_year": 0,
            }


        latest = history[-1]


        return {
            "value":
                latest.get(
                    "value",
                    0,
                ),

            "period":
                latest.get(
                    "period",
                    "",
                ),

            "fiscal_year":
                latest.get(
                    "year",
                    0,
                ),
        }


    # ==============================================================
    # GROWTH CALCULATIONS
    # ==============================================================

    def _calculate_growth_metrics(
        self,
        quarterly,
        annual,
    ):

        growth = {
            "yoy": 0,
            "qoq": 0,
            "cagr": 0,
        }


        if quarterly:

            current = quarterly[-1]


            if len(quarterly) >= 2:

                previous = quarterly[-2]

                growth["qoq"] = (
                    calculate_growth(
                        current.get(
                            "value",
                            0,
                        ),
                        previous.get(
                            "value",
                            0,
                        ),
                    )
                )


            if len(quarterly) >= 5:

                prior_year = quarterly[-5]

                growth["yoy"] = (
                    calculate_growth(
                        current.get(
                            "value",
                            0,
                        ),
                        prior_year.get(
                            "value",
                            0,
                        ),
                    )
                )


        if annual and len(annual) >= 2:

            start = annual[0]

            end = annual[-1]


            years = (
                end.get("year", 0)
                -
                start.get("year", 0)
            )


            growth["cagr"] = (
                calculate_cagr(
                    start.get(
                        "value",
                        0,
                    ),
                    end.get(
                        "value",
                        0,
                    ),
                    years,
                )
            )


        return growth


    # ==============================================================
    # EARNINGS TREND CLASSIFICATION
    # ==============================================================

    def analyze_trend(
        self,
        growth,
    ):

        yoy = growth.get(
            "yoy",
            0,
        )

        qoq = growth.get(
            "qoq",
            0,
        )


        if yoy >= 25 and qoq > 10:

            classification = (
                "STRONG_ACCELERATION"
            )

            strength = 5


        elif yoy >= 15 and qoq > 0:

            classification = (
                "ACCELERATING"
            )

            strength = 4


        elif yoy > 0:

            classification = (
                "GROWING"
            )

            strength = 3


        elif abs(yoy) < 5:

            classification = (
                "STABLE"
            )

            strength = 2


        elif yoy < 0 and yoy > -25:

            classification = (
                "DECLINING"
            )

            strength = 1


        else:

            classification = (
                "DETERIORATING"
            )

            strength = 0


        return {
            "classification":
                classification,

            "direction":
                (
                    "POSITIVE"
                    if strength >= 3
                    else "NEGATIVE"
                ),

            "strength":
                strength,
        }


    # ==============================================================
    # EARNINGS CONSISTENCY
    # ==============================================================

    def analyze_consistency(
        self,
        history,
    ):

        if not history:

            return {
                "score": 0,
                "classification":
                    "UNKNOWN",
            }


        values = [
            item.get(
                "value",
                0,
            )
            for item in history
        ]


        positive = sum(
            1
            for value in values
            if value > 0
        )


        positive_ratio = (
            positive /
            len(values)
        )


        growth_periods = 0


        for index in range(
            1,
            len(values),
        ):

            if values[index] > values[index - 1]:

                growth_periods += 1


        growth_ratio = (
            growth_periods /
            max(
                len(values) - 1,
                1,
            )
        )


        volatility = (
            pd.Series(values)
            .pct_change()
            .abs()
            .mean()
        )


        score = (
            positive_ratio * 2
            +
            growth_ratio * 2
        )


        if volatility < 0.25:

            score += 1


        score = round(
            min(score, 5),
            2,
        )


        if score >= 4:

            classification = "HIGH"

        elif score >= 3:

            classification = "GOOD"

        elif score >= 2:

            classification = "MODERATE"

        else:

            classification = "WEAK"


        return {
            "score":
                score,

            "classification":
                classification,

            "volatility":
                volatility,

            "interruptions":
                sum(
                    1
                    for value in values
                    if value <= 0
                ),
        }


    # ==============================================================
    # EARNINGS ACCELERATION
    # ==============================================================

    def analyze_acceleration(
        self,
        history,
    ):

        if len(history) < 3:

            return {
                "accelerating":
                    False,

                "strength":
                    0,
            }


        previous_growth = (
            calculate_growth(
                history[-2].get(
                    "value",
                    0,
                ),

                history[-3].get(
                    "value",
                    0,
                ),
            )
        )


        current_growth = (
            calculate_growth(
                history[-1].get(
                    "value",
                    0,
                ),

                history[-2].get(
                    "value",
                    0,
                ),
            )
        )


        accelerating = (
            current_growth >
            previous_growth
        )


        return {
            "accelerating":
                accelerating,

            "strength":
                2
                if accelerating
                else 0,

            "previous_growth":
                previous_growth,

            "current_growth":
                current_growth,
        }


    # ==============================================================
    # COMPLETE ANALYSIS
    # ==============================================================

    def analyze_full(
        self,
        sec_data,
    ):

        result = self.analyze(
            sec_data
        )


        result["trend"] = (
            self.analyze_trend(
                result.get(
                    "growth",
                    {},
                )
            )
        )


        result["consistency"] = (
            self.analyze_consistency(
                result.get(
                    "history",
                    [],
                )
            )
        )


        result["acceleration"] = (
            self.analyze_acceleration(
                result.get(
                    "history",
                    [],
                )
            )
        )


        return result



def run(
    sec_data,
    resolver=None,
):

    engine = EnhancedEarnings(
        resolver
    )

    return engine.analyze_full(
        sec_data
    )        