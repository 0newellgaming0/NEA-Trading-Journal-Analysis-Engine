"""
====================================================================
NEA28 MARKET BREADTH ENGINE

Module:
    modules/market/breadth_engine.py

Purpose:
    Institutional market breadth analysis engine.

Responsibilities:
    - Analyze advance/decline participation
    - Calculate breadth strength
    - Calculate McClellan indicators
    - Measure DMA participation
    - Calculate bullish participation
    - Produce standardized breadth output

Calculations:
    - Advancing Issues
    - Declining Issues
    - Advancing Volume
    - Declining Volume
    - New Highs
    - New Lows
    - Advance Decline Ratio
    - McClellan Oscillator
    - McClellan Summation Index
    - Bullish Percent Index
    - % Above 50 DMA
    - % Above 200 DMA

Output:
{
    "breadth_score":91,
    "mcclellan_oscillator":34,
    "mcclellan_summation":1850,
    "bullish_percent_index":72,
    "above_50_dma":81,
    "above_200_dma":68,
    "new_highs":642,
    "new_lows":37
}
====================================================================
"""

import logging
from datetime import datetime

import pandas as pd


logger = logging.getLogger("MarketBreadthEngine")


class MarketBreadthEngine:
    """
    Institutional market breadth calculation engine.
    """

    def __init__(self):
        self.previous_summation = 0
        logger.info(
            "Market Breadth Engine initialized"
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

    def _ema(
        self,
        series,
        period
    ):
        return (
            series
            .ewm(
                span=period,
                adjust=False
            )
            .mean()
        )

    def _calculate_advance_decline_ratio(
        self,
        advancing,
        declining
    ):
        if declining <= 0:
            return 0

        return round(
            advancing / declining,
            2
        )

    def _calculate_mcclellan_oscillator(
        self,
        advances,
        declines
    ):
        ad_line = advances - declines

        ema19 = self._ema(
            ad_line,
            19
        )

        ema39 = self._ema(
            ad_line,
            39
        )

        return round(
            ema19.iloc[-1] - ema39.iloc[-1],
            2
        )

    def _calculate_mcclellan_summation(
        self,
        oscillator
    ):
        self.previous_summation += oscillator

        return round(
            self.previous_summation,
            2
        )

    def _calculate_bullish_percent_index(
        self,
        breadth
    ):
        bullish = self._safe_float(
            breadth.get(
                "bullish_stocks",
                0
            )
        )

        total = self._safe_float(
            breadth.get(
                "total_stocks",
                0
            )
        )

        if total <= 0:
            return 0

        return round(
            (
                bullish /
                total
            ) * 100,
            2
        )

    def _calculate_dma_participation(
        self,
        count,
        total
    ):
        if total <= 0:
            return 0

        return round(
            (
                count /
                total
            ) * 100,
            2
        )

    def _calculate_high_low_ratio(
        self,
        highs,
        lows
    ):
        if lows <= 0:
            return 0

        return round(
            highs / lows,
            2
        )

    def _calculate_breadth_score(
        self,
        data
    ):
        score = 50

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

        new_highs = self._safe_float(
            data.get(
                "new_highs",
                0
            )
        )

        new_lows = self._safe_float(
            data.get(
                "new_lows",
                0
            )
        )

        above_50 = self._safe_float(
            data.get(
                "above_50_dma",
                0
            )
        )

        above_200 = self._safe_float(
            data.get(
                "above_200_dma",
                0
            )
        )

        if advancing > declining:
            score += 15

        elif declining > advancing:
            score -= 15

        if new_highs > new_lows:
            score += 15

        elif new_lows > new_highs:
            score -= 15

        if above_50 >= 60:
            score += 10

        elif above_50 < 40:
            score -= 10

        if above_200 >= 60:
            score += 10

        elif above_200 < 40:
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
        breadth_data
    ):
        """
        Execute breadth analysis.

        Input:
            {
                advancing_issues,
                declining_issues,
                advancing_volume,
                declining_volume,
                new_highs,
                new_lows,
                bullish_stocks,
                total_stocks,
                above_50_dma_count,
                above_200_dma_count,
                history
            }
        """

        logger.info(
            "Running Market Breadth Analysis"
        )

        if not isinstance(
            breadth_data,
            dict
        ):
            return {}

        advancing = self._safe_float(
            breadth_data.get(
                "advancing_issues",
                0
            )
        )

        declining = self._safe_float(
            breadth_data.get(
                "declining_issues",
                0
            )
        )

        advancing_volume = self._safe_float(
            breadth_data.get(
                "advancing_volume",
                0
            )
        )

        declining_volume = self._safe_float(
            breadth_data.get(
                "declining_volume",
                0
            )
        )

        new_highs = self._safe_float(
            breadth_data.get(
                "new_highs",
                0
            )
        )

        new_lows = self._safe_float(
            breadth_data.get(
                "new_lows",
                0
            )
        )

        oscillator = 0

        history = breadth_data.get(
            "history"
        )

        if isinstance(
            history,
            pd.DataFrame
        ):

            if (
                "advances" in history.columns
                and
                "declines" in history.columns
            ):

                oscillator = self._calculate_mcclellan_oscillator(
                    history["advances"],
                    history["declines"]
                )

        summation = self._calculate_mcclellan_summation(
            oscillator
        )

        total_issues = (
            advancing +
            declining
        )

        above_50 = self._calculate_dma_participation(
            breadth_data.get(
                "above_50_dma_count",
                0
            ),
            total_issues
        )

        above_200 = self._calculate_dma_participation(
            breadth_data.get(
                "above_200_dma_count",
                0
            ),
            total_issues
        )

        normalized = {
            **breadth_data,
            "above_50_dma": above_50,
            "above_200_dma": above_200
        }

        return {
            "breadth_score": self._calculate_breadth_score(
                normalized
            ),
            "advancing_issues": advancing,
            "declining_issues": declining,
            "advancing_volume": advancing_volume,
            "declining_volume": declining_volume,
            "advance_decline_ratio": self._calculate_advance_decline_ratio(
                advancing,
                declining
            ),
            "mcclellan_oscillator": oscillator,
            "mcclellan_summation": summation,
            "bullish_percent_index": self._calculate_bullish_percent_index(
                breadth_data
            ),
            "above_50_dma": above_50,
            "above_200_dma": above_200,
            "new_highs": new_highs,
            "new_lows": new_lows,
            "high_low_ratio": self._calculate_high_low_ratio(
                new_highs,
                new_lows
            ),
            "timestamp": datetime.utcnow().isoformat()
        }