"""
====================================================================
NEA28 MARKET LIQUIDITY ENGINE

Module:
    modules/market/liquidity_engine.py

Purpose:
    Institutional market liquidity analysis.

Responsibilities:
    - Measure institutional participation
    - Analyze ETF flow strength
    - Measure index volume expansion
    - Detect breadth thrust participation
    - Produce standardized liquidity output

Output:
{
    "etf_flow_score":88,
    "institutional_participation":91,
    "liquidity_score":89
}
====================================================================
"""

import logging
from datetime import datetime


logger = logging.getLogger("MarketLiquidityEngine")


class MarketLiquidityEngine:
    """
    Institutional liquidity analysis engine.
    """

    def __init__(self):
        logger.info(
            "Market Liquidity Engine initialized"
        )

    def _safe_float(
        self,
        value,
        default=0
    ):
        try:
            return float(value)
        except Exception:
            return default

    def _calculate_etf_flow_score(
        self,
        data
    ):
        score = 50

        spy = self._safe_float(
            data.get(
                "SPY_flow",
                0
            )
        )

        qqq = self._safe_float(
            data.get(
                "QQQ_flow",
                0
            )
        )

        iwm = self._safe_float(
            data.get(
                "IWM_flow",
                0
            )
        )

        average_flow = (
            spy +
            qqq +
            iwm
        ) / 3

        if average_flow > 0:
            score += 30

        elif average_flow < 0:
            score -= 30

        return max(
            min(
                score,
                100
            ),
            0
        )

    def _calculate_volume_expansion(
        self,
        data
    ):
        current_volume = self._safe_float(
            data.get(
                "current_volume",
                0
            )
        )

        average_volume = self._safe_float(
            data.get(
                "average_volume",
                0
            )
        )

        if average_volume <= 0:
            return 0

        return round(
            (
                current_volume /
                average_volume
            )
            *
            100,
            2
        )

    def _calculate_breadth_thrust(
        self,
        data
    ):
        advancing = self._safe_float(
            data.get(
                "advancing_issues",
                0
            )
        )

        declining = self._safe_float(
            data.get(
                "declining_issues",
                0
            )
        )

        total = (
            advancing +
            declining
        )

        if total <= 0:
            return 0

        return round(
            (
                advancing /
                total
            )
            *
            100,
            2
        )

    def _calculate_institutional_participation(
        self,
        etf_score,
        volume_score,
        breadth_score
    ):
        return round(
            (
                etf_score +
                volume_score +
                breadth_score
            )
            /
            3,
            2
        )

    def _calculate_liquidity_score(
        self,
        institutional,
        breadth,
        volume
    ):
        score = 50

        if institutional >= 80:
            score += 25

        elif institutional >= 60:
            score += 15

        elif institutional < 40:
            score -= 20

        if breadth >= 70:
            score += 15

        elif breadth < 40:
            score -= 15

        if volume >= 120:
            score += 10

        elif volume < 80:
            score -= 10

        return max(
            min(
                score,
                100
            ),
            0
        )

    def run(
        self,
        liquidity_data
    ):
        """
        Execute liquidity analysis.

        Input:

        {
            "SPY_flow":,
            "QQQ_flow":,
            "IWM_flow":,
            "current_volume":,
            "average_volume":,
            "advancing_issues":,
            "declining_issues":
        }

        Output:

        {
            "etf_flow_score":,
            "institutional_participation":,
            "liquidity_score":
        }
        """

        logger.info(
            "Running Market Liquidity Analysis"
        )

        if not isinstance(
            liquidity_data,
            dict
        ):
            return {}

        etf_score = self._calculate_etf_flow_score(
            liquidity_data
        )

        volume_score = self._calculate_volume_expansion(
            liquidity_data
        )

        breadth_score = self._calculate_breadth_thrust(
            liquidity_data
        )

        institutional = self._calculate_institutional_participation(
            etf_score,
            volume_score,
            breadth_score
        )

        liquidity_score = self._calculate_liquidity_score(
            institutional,
            breadth_score,
            volume_score
        )

        return {
            "etf_flow_score": etf_score,
            "institutional_participation": institutional,
            "volume_expansion": volume_score,
            "breadth_thrust": breadth_score,
            "liquidity_score": liquidity_score,
            "timestamp": datetime.utcnow().isoformat()
        }