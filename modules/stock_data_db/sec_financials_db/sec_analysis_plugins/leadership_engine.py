"""
====================================================================
NEA28 LEADERSHIP ENGINE

Module:
    leadership_engine.py

Purpose
-------
Provides the CANSLIM "L" (Leader or Laggard) component.

This engine determines whether a company demonstrates
institutional leadership based on fundamental quality.

Inputs
------
- Enhanced Earnings
- Annual Growth
- Share Structure
- Float Analysis
- Capital Allocation

Future Inputs
-------------
- Relative Price Strength
- Industry Group Ranking
- Sector Ranking
- Relative Performance vs S&P500
- Relative Performance vs Industry ETF

Outputs
-------
{
    "relative_strength": 92,
    "leader_state": "LEADER",
    "industry_rank": 8,
    "sector_strength": 88,
    "leadership_score": 91,
    "growth_leader": True,
    "profitability_leader": True,
    "institutional_leader": True
}

Used By
-------
- CANSLIM Engine
- Growth Asymmetry Engine
- Institutional Ranking
====================================================================
"""

from __future__ import annotations

import logging

logger = logging.getLogger("Leadership")


class LeadershipEngine:

    def __init__(self):

        logger.info(
            "Leadership Engine initialized"
        )

    # ==========================================================
    # PUBLIC ANALYSIS
    # ==========================================================

    def analyze(
        self,
        enhanced_earnings=None,
        annual_growth=None,
        share_structure=None,
        float_analysis=None,
        capital_allocation=None,
    ):

        enhanced_earnings = enhanced_earnings or {}
        annual_growth = annual_growth or {}
        share_structure = share_structure or {}
        float_analysis = float_analysis or {}
        capital_allocation = capital_allocation or {}

        score = 0

        # ------------------------------------------------------
        # Earnings Leadership
        # ------------------------------------------------------

        growth = self._safe_float(

            enhanced_earnings.get(
                "growth_pct",
                enhanced_earnings.get(
                    "growth_percent",
                    0
                )
            )

        )

        if growth >= 50:
            score += 20

        elif growth >= 25:
            score += 15

        elif growth >= 10:
            score += 10

        # ------------------------------------------------------
        # Annual Growth Leadership
        # ------------------------------------------------------

        revenue = annual_growth.get(
            "revenue",
            {}
        )

        earnings = annual_growth.get(
            "earnings",
            {}
        )

        revenue_cagr = self._safe_float(
            revenue.get(
                "cagr5",
                0
            )
        )

        earnings_cagr = self._safe_float(
            earnings.get(
                "cagr5",
                0
            )
        )

        if revenue_cagr >= 20:
            score += 10

        elif revenue_cagr >= 10:
            score += 5

        if earnings_cagr >= 20:
            score += 10

        elif earnings_cagr >= 10:
            score += 5

        # ------------------------------------------------------
        # Margin Leadership
        # ------------------------------------------------------

        gross_margin = self._safe_float(
            enhanced_earnings.get(
                "gross_margin",
                0
            )
        )

        operating_margin = self._safe_float(
            enhanced_earnings.get(
                "operating_margin",
                0
            )
        )

        if gross_margin >= 60:
            score += 5

        elif gross_margin >= 40:
            score += 3

        if operating_margin >= 25:
            score += 5

        elif operating_margin >= 15:
            score += 3

        # ------------------------------------------------------
        # Float Leadership
        # ------------------------------------------------------

        float_score = self._safe_float(

            float_analysis.get(
                "float_score",

                share_structure.get(
                    "float_score",
                    0
                )
            )

        )

        if float_score >= 90:
            score += 10

        elif float_score >= 75:
            score += 7

        elif float_score >= 60:
            score += 5

        # ------------------------------------------------------
        # Capital Allocation
        # ------------------------------------------------------

        quality = capital_allocation.get(
            "capital_quality",

            capital_allocation.get(
                "quality"
            )
        )

        if quality == "HIGH QUALITY":
            score += 10

        elif quality in (
            "EXCELLENT",
            "GOOD",
        ):
            score += 5

        # ------------------------------------------------------
        # Normalize
        # ------------------------------------------------------

        score = min(
            round(score),
            100
        )

        # ------------------------------------------------------
        # Classification
        # ------------------------------------------------------

        if score >= 90:

            leader_state = "ELITE LEADER"

        elif score >= 75:

            leader_state = "LEADER"

        elif score >= 60:

            leader_state = "EMERGING LEADER"

        elif score >= 40:

            leader_state = "AVERAGE"

        else:

            leader_state = "LAGGARD"

        result = {

            "relative_strength": score,

            "leader_state": leader_state,

            "industry_rank": max(
                1,
                int(
                    (100 - score) / 10
                ) + 1
            ),

            "sector_strength": score,

            "leadership_score": score,

            "growth_leader":
                revenue_cagr >= 15
                and
                earnings_cagr >= 15,

            "profitability_leader":
                gross_margin >= 40
                and
                operating_margin >= 15,

            "institutional_leader":
                (
                    float_score >= 70
                    and
                    quality in (
                        "HIGH QUALITY",
                        "EXCELLENT",
                        "GOOD"
                    )
                )
        }

        self._log_report(
            result
        )

        return result

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _safe_float(
        self,
        value
    ):

        try:
            return float(value)

        except Exception:
            return 0.0

    # ==========================================================
    # LOGGING
    # ==========================================================

    def _log_report(
        self,
        report
    ):

        logger.info("=" * 70)
        logger.info("LEADERSHIP ANALYSIS")
        logger.info("=" * 70)

        logger.info(
            "Relative Strength     : %s",
            report["relative_strength"]
        )

        logger.info(
            "Leadership State      : %s",
            report["leader_state"]
        )

        logger.info(
            "Industry Rank         : %s",
            report["industry_rank"]
        )

        logger.info(
            "Sector Strength       : %s",
            report["sector_strength"]
        )

        logger.info(
            "Leadership Score      : %s",
            report["leadership_score"]
        )

        logger.info(
            "Growth Leader         : %s",
            report["growth_leader"]
        )

        logger.info(
            "Profitability Leader  : %s",
            report["profitability_leader"]
        )

        logger.info(
            "Institutional Leader  : %s",
            report["institutional_leader"]
        )

        logger.info("=" * 70)