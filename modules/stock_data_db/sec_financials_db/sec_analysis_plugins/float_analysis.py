"""
====================================================================
NEA28 FLOAT ANALYSIS ENGINE

Module:
    float_analysis.py

Purpose:
    Institutional SEC tradable supply intelligence.

Features:
    - SEC DEI float extraction
    - Share count analysis
    - Float classification
    - Float scarcity analysis
    - Supply trend analysis
    - Dilution detection
    - Buyback support analysis
    - Institutional supply impact
    - Multi-period share history

Used By:
    SECAnalysis
    SECAnalysisExtensions
    Institutional Ranking Engine
    Growth Asymmetry Engine
    CANSLIM Engine
====================================================================
"""

from __future__ import annotations

import logging
import pandas as pd

logger = logging.getLogger("FloatAnalysis")

FLOAT_CONCEPTS = [
    "EntityPublicFloat",
    "EntityCommonStockSharesOutstanding",
]

SHARE_COUNT_CONCEPTS = [
    "WeightedAverageNumberOfSharesOutstandingBasic",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
]

BUYBACK_CONCEPTS = [
    "PaymentsForRepurchaseOfCommonStock",
]

EQUITY_CONCEPTS = [
    "StockholdersEquity",
]


def _normalize_concept(value):
    if not isinstance(value, str):
        return ""
    return value.split(":")[-1]


def _extract_concepts(df: pd.DataFrame, concepts):
    if df.empty:
        return pd.DataFrame()

    data = df.copy()
    data["normalized_concept"] = data["concept"].apply(_normalize_concept)

    data = data[
        data["normalized_concept"].isin(concepts)
    ].copy()

    if data.empty:
        return data

    return (
        data
        .drop_duplicates(
            subset=[
                "normalized_concept",
                "period_end"
            ]
        )
        .sort_values(
            [
                "period_end",
                "period_start"
            ],
            ascending=False
        )
    )


def _extract_float_data(df):
    return _extract_concepts(df, FLOAT_CONCEPTS)


def _extract_share_data(df):
    return _extract_concepts(df, SHARE_COUNT_CONCEPTS)


def _extract_buybacks(df):
    return _extract_concepts(df, BUYBACK_CONCEPTS)


def _extract_equity(df):
    return _extract_concepts(df, EQUITY_CONCEPTS)


class FloatAnalysis:

    def analyze(self, df: pd.DataFrame):
       
            
        report = {
            "public_float": None,
            "shares_outstanding": None,
            "float_category": "UNKNOWN",
            "float_scarcity": "UNKNOWN",
            "share_supply_trend": "UNKNOWN",
            "dilution_state": "UNKNOWN",
            "buyback_support": "UNKNOWN",
            "institutional_supply_impact": "UNKNOWN",
            "float_quality": "UNKNOWN",
            "float_score": None,
            "history": []
        }

        try:
            float_data = _extract_float_data(df)
            share_data = _extract_share_data(df)
            buybacks = _extract_buybacks(df)
            equity = _extract_equity(df)

            history = [
                {
                    "concept": row["normalized_concept"],
                    "value": float(row["numeric_value"]),
                    "period_end": row["period_end"],
                    "fiscal_year": row["fiscal_year"],
                    "fiscal_period": row["fiscal_period"]
                }
                for _, row in share_data.iterrows()
            ]

            latest_float = (
                float(float_data.iloc[0]["numeric_value"])
                if not float_data.empty
                else None
            )

            latest_shares = (
                float(share_data.iloc[0]["numeric_value"])
                if not share_data.empty
                else None
            )

            report.update(
                {
                    "public_float": latest_float,
                    "shares_outstanding": latest_shares,
                    "float_category": self._classify_float(latest_float),
                    "float_scarcity": self._scarcity(latest_float),
                    "share_supply_trend": self._supply_trend(share_data),
                    "dilution_state": self._dilution(share_data),
                    "buyback_support": self._buyback_analysis(buybacks),
                    "institutional_supply_impact": self._institutional_impact(latest_float),
                    "float_quality": self._quality(latest_float, share_data),
                    "float_score": self._score(
                        latest_float,
                        share_data,
                        buybacks
                    ),
                    "history": history
                }
            )

            logger.info("=" * 70)
            logger.info("FLOAT ANALYSIS")
            logger.info("=" * 70)
            logger.info("Public Float: %s", report["public_float"])
            logger.info("Shares Outstanding: %s", report["shares_outstanding"])
            logger.info("Float Category: %s", report["float_category"])
            logger.info("Float Scarcity: %s", report["float_scarcity"])
            logger.info("Supply Trend: %s", report["share_supply_trend"])
            logger.info("Dilution State: %s", report["dilution_state"])
            logger.info("Buyback Support: %s", report["buyback_support"])
            logger.info("Float Score: %s", report["float_score"])
            logger.info("=" * 70)

        except Exception:
            logger.exception("Float analysis failed")

        return report


    def _classify_float(self, value):
        if value is None:
            return "UNKNOWN"

        if value < 10_000_000:
            return "ULTRA LOW FLOAT"

        if value < 50_000_000:
            return "LOW FLOAT"

        if value < 250_000_000:
            return "MODERATE FLOAT"

        if value < 1_000_000_000:
            return "HIGH FLOAT"

        return "VERY HIGH FLOAT"


    def _scarcity(self, value):
        if value is None:
            return "UNKNOWN"

        if value < 50_000_000:
            return "HIGH"

        if value < 250_000_000:
            return "MEDIUM"

        return "LOW"


    def _supply_trend(self, shares):
        if shares.empty:
            return "UNKNOWN"

        values = (
            shares["numeric_value"]
            .astype(float)
            .tolist()
        )

        if len(values) < 2:
            return "UNKNOWN"

        if values[0] > values[1]:
            return "EXPANDING SUPPLY"

        if values[0] < values[1]:
            return "CONTRACTING SUPPLY"

        return "STABLE SUPPLY"


    def _dilution(self, shares):
        trend = self._supply_trend(shares)

        if trend == "EXPANDING SUPPLY":
            return "HIGH"

        if trend == "CONTRACTING SUPPLY":
            return "LOW"

        if trend == "STABLE SUPPLY":
            return "NONE"

        return "UNKNOWN"


    def _buyback_analysis(self, buybacks):
        if buybacks.empty:
            return "UNKNOWN"

        value = float(
            buybacks.iloc[0]["numeric_value"]
        )

        if value < 0:
            return "STRONG SUPPORT"

        return "NEUTRAL"


    def _institutional_impact(self, value):
        if value is None:
            return "UNKNOWN"

        if value < 50_000_000:
            return "POSITIVE"

        if value < 250_000_000:
            return "NEUTRAL"

        return "NEGATIVE"


    def _quality(self, float_value, shares):
        if float_value is None:
            return "UNKNOWN"

        if float_value < 250_000_000:
            return "GOOD"

        return "AVERAGE"


    def _score(self, float_value, shares, buybacks):

        score = 0

        if float_value:
            if float_value < 50_000_000:
                score += 40
            elif float_value < 250_000_000:
                score += 25
            else:
                score += 10

        if not buybacks.empty:
            score += 20

        if not shares.empty:
            if self._supply_trend(shares) == "CONTRACTING SUPPLY":
                score += 20

        return score if score else None