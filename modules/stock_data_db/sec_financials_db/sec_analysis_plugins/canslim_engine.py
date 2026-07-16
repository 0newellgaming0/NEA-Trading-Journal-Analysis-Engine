"""
====================================================================
NEA28 CANSLIM FUNDAMENTAL ENGINE

Module:
    canslim_engine.py

Purpose
-------
Institutional CANSLIM ranking layer using SEC analysis plugins.

Consumes:
- Enhanced Earnings
- Annual Growth
- Share Structure
- Capital Allocation

Analyzes:
- C Current Earnings
- A Annual Earnings Growth
- S Supply / Share Structure
- N New Products / Events
- L Leadership
- I Institutional Sponsorship
- M Market Direction

Used By:
- SECAnalysis
- Growth Asymmetry Engine
- Institutional Ranking
- Stock Screening

====================================================================
"""

from __future__ import annotations

import logging

logger = logging.getLogger("CANSLIM")


class CANSLIMEngine:

    def __init__(self):

        logger.info("CANSLIM Engine initialized as scoring layer")


    def _normalize_input(self, data):
        if data is None:
            return {}

        if isinstance(data, dict):
            return data

        if hasattr(data, "empty"):
            if data.empty:
                return {}

            try:
                return data.iloc[-1].to_dict()
            except Exception:
                return {}

        try:
            return dict(data)
        except Exception:
            return {}


    def _normalize_earnings(self, earnings):
        if not earnings or not isinstance(earnings, dict):
            return {}

        normalized = dict(earnings)

        try:
            earnings_data = earnings.get("earnings", {})

            if isinstance(earnings_data, dict):
                history = earnings_data.get("history", [])
                cagr5 = earnings_data.get("cagr5", 0)

                if history:
                    latest = history[-1].get("value", 0)
                    previous = history[-2].get("value", 0) if len(history) > 1 else 0

                    if previous:
                        normalized["growth_pct"] = ((latest - previous) / previous) * 100

                normalized["earnings_cagr"] = cagr5

            growth_quality = earnings.get("growth_quality", {})

            if isinstance(growth_quality, dict):
                normalized["earnings_quality"] = growth_quality.get("rating")

        except Exception:
            logger.exception("CANSLIM earnings normalization failed")

        return normalized


    def _normalize_growth(self, annual_growth):
        if not annual_growth or not isinstance(annual_growth, dict):
            return {}

        normalized = dict(annual_growth)

        try:
            earnings = annual_growth.get("earnings", {})
            revenue = annual_growth.get("revenue", {})

            if isinstance(earnings, dict):
                normalized["earnings_cagr"] = earnings.get("cagr5", 0)

            if isinstance(revenue, dict):
                normalized["revenue_cagr"] = revenue.get("cagr5", 0)

            growth_quality = annual_growth.get("growth_quality", {})

            if isinstance(growth_quality, dict):
                normalized["growth_quality"] = growth_quality.get("rating")

        except Exception:
            logger.exception("CANSLIM growth normalization failed")

        return normalized


    def _normalize_supply(self, share_structure):
        if not share_structure or not isinstance(share_structure, dict):
            return {}

        normalized = dict(share_structure)

        try:
            supply_score = 0

            if share_structure.get("supply_impact") == "FAVORABLE":
                supply_score = 80

            elif share_structure.get("share_supply_direction") == "CONTRACTING":
                supply_score = 70

            elif share_structure.get("dilution_risk") == "LOW":
                supply_score = 60

            normalized["supply_score"] = supply_score

        except Exception:
            logger.exception("CANSLIM supply normalization failed")

        return normalized


    def _normalize_capital(self, capital_allocation):
        if not capital_allocation or not isinstance(capital_allocation, dict):
            return {}

        normalized = dict(capital_allocation)

        try:
            if "capital_quality" in capital_allocation:
                normalized["quality"] = capital_allocation["capital_quality"]

            if "buyback_support" in capital_allocation:
                normalized["investment_strategy"] = capital_allocation["buyback_support"]

            if "management_alignment" in capital_allocation:
                normalized["capital_efficiency"] = capital_allocation["management_alignment"]

        except Exception:
            logger.exception("CANSLIM capital normalization failed")

        return normalized

    def _normalize_developments(self, new_events):
        if not new_events or not isinstance(new_events, dict):
            return {}

        normalized = dict(new_events)

        try:
            events = new_events.get("events", [])

            if not isinstance(events, list):
                events = []

            validated_events = []

            for event in events:
                if not isinstance(event, dict):
                    continue

                if event.get("catalyst", False):
                    validated_events.append({
                        "type": event.get("type"),
                        "category": event.get("category"),
                        "date": event.get("date"),
                        "source": event.get("source"),
                        "confidence": event.get("confidence", 0),
                        "materiality": event.get("materiality"),
                        "evidence": event.get("evidence", "")
                    })

            normalized["validated_events"] = validated_events
            normalized["event_count"] = len(validated_events)

            try:
                normalized["institutional_n_score"] = float(
                    new_events.get("institutional_n_score", 0)
                )
            except Exception:
                normalized["institutional_n_score"] = 0

            normalized["innovation_state"] = new_events.get(
                "innovation_state",
                "UNKNOWN"
            )

            normalized["classification"] = new_events.get(
                "classification",
                "UNRATED"
            )

        except Exception:
            logger.exception(
                "CANSLIM development normalization failed"
            )

        return normalized
        
    def analyze(
        self,
        ticker=None,
        earnings=None,
        annual_growth=None,
        share_structure=None,
        capital_allocation=None,
        market_context=None,
        new_events=None,
        leadership=None
    ):
        try:
            logger.info("Running CANSLIM Analysis")

            report = {
                "C_current_earnings": {},
                "A_annual_growth": {},
                "S_supply": {},
                "N_new_products": {},
                "L_leadership": {},
                "I_institutional": {},
                "M_market": {},
                "component_scores": {},
                "score": 0,
                "classification": "UNRATED",
            }          

            earnings = self._normalize_earnings(earnings)
            annual_growth = self._normalize_growth(annual_growth)
            share_structure = self._normalize_supply(share_structure)
            capital_allocation = self._normalize_capital(capital_allocation)
            new_events = self._normalize_developments(new_events)

            scores = {
                "C": self._current_earnings(
                    earnings,
                    report
                ),
                "A": self._annual_growth(
                    annual_growth,
                    report
                ),
                "N": self._new_products(
                    new_events,
                    report
                ),
                "S": self._supply(
                    share_structure,
                    report
                ),
                "L": self._leadership(
                    leadership,
                    report
                ),
                "I": self._institutional(
                    capital_allocation,
                    report
                ),
                "M": self._market(
                    market_context,
                    report
                ),
            }

            report["component_scores"] = scores

            report["score"] = round(
                min(sum(scores.values()), 100),
                2
            )

            report["classification"] = self._classification(
                report["score"]
            )

            self._log_report(report)

            return report

        except Exception:
            logger.exception(
                "CANSLIM analysis failed"
            )

            return {
                "score": 0,
                "classification": "FAILED",
                "error": True,
            }
            
    def _current_earnings(
        self,
        earnings,
        report
    ):

        score = 0

        if not earnings:
            return score

        report["C_current_earnings"] = earnings

        growth = earnings.get(
            "growth_pct",
            earnings.get("growth_percent", 0)
        )

        quality = earnings.get(
            "earnings_quality"
        )

        try:
            growth = float(
                growth
            )
        except Exception:
            growth = 0

        if growth >= 25:
            score += 25
        elif growth >= 15:
            score += 15
        elif growth >= 5:
            score += 5

        if quality in (
            "EXCELLENT",
            "STRONG",
        ):
            score += 10

        return min(
            score,
            35
        )


    def _annual_growth(
        self,
        annual_growth,
        report
    ):

        score = 0

        if not annual_growth:
            return score

        report["A_annual_growth"] = annual_growth

        earnings_growth = annual_growth.get(
            "earnings_cagr",
            annual_growth.get(
                "earnings",
                {}
            ).get(
                "cagr5",
                0
            )
        )

        revenue_growth = annual_growth.get(
            "revenue_cagr",
            annual_growth.get(
                "revenue",
                {}
            ).get(
                "cagr5",
                0
            )
        )

        growth_quality = annual_growth.get(
            "growth_quality"
        )

        try:
            earnings_growth = float(
                earnings_growth
            )
        except Exception:
            earnings_growth = 0

        try:
            revenue_growth = float(
                revenue_growth
            )
        except Exception:
            revenue_growth = 0

        if earnings_growth >= 25:
            score += 25
        elif earnings_growth >= 15:
            score += 15
        elif earnings_growth >= 8:
            score += 5

        if revenue_growth >= 15:
            score += 5

        if growth_quality in (
            "ELITE COMPOUNDER",
            "HIGH GROWTH",
        ):
            score += 5

        return min(
            score,
            35
        )


    def _supply(
        self,
        share_structure,
        report
    ):

        score = 0

        if not share_structure:
            return score

        report["S_supply"] = share_structure

        supply_score = share_structure.get(
            "supply_score",
            share_structure.get(
                "float_score",
                0
            )
        )

        try:
            supply_score = float(
                supply_score
            )
        except Exception:
            supply_score = 0

        if supply_score >= 80:
            score += 20
        elif supply_score >= 60:
            score += 15
        elif supply_score >= 40:
            score += 5

        return min(
            score,
            20
        )


    def _institutional(
        self,
        capital_allocation,
        report
    ):

        score = 0

        if not capital_allocation:
            return score

        report["I_institutional"] = capital_allocation

        quality = capital_allocation.get(
            "quality"
        )

        efficiency = capital_allocation.get(
            "capital_efficiency"
        )

        if quality == "HIGH QUALITY":
            score += 10

        elif quality in (
            "EXCELLENT",
            "GOOD",
        ):
            score += 5

        if efficiency in (
            "ELITE",
            "EXCELLENT",
            "STRONG",
        ):
            score += 5

        return min(
            score,
            15
        )


    def _new_products(self, new_events, report):
        if not new_events:
            report["N_new_products"] = {
                "status": "NO DATA"
            }
            return 0

        report["N_new_products"] = new_events

        validated = new_events.get(
            "validated_events",
            []
        )

        if not validated:
            return 0

        score = new_events.get(
            "institutional_n_score",
            0
        )

        try:
            score = float(score)
        except Exception:
            score = 0

        if score >= 90:
            return 10

        if score >= 75:
            return 8

        if score >= 60:
            return 5

        return 2


    def _leadership(
        self,
        leadership,
        report
    ):

        if not leadership:
            report["L_leadership"] = {
                "status": "NO DATA"
            }
            return 0

        report["L_leadership"] = leadership

        relative_strength = leadership.get(
            "relative_strength",
            0
        )

        try:
            relative_strength = float(
                relative_strength
            )
        except Exception:
            relative_strength = 0

        if relative_strength >= 90:
            return 10

        if relative_strength >= 70:
            return 5

        return 0

    def _market(
        self,
        market_context,
        report
    ):

        score = 0

        if not market_context:
            report["M_market"] = {
                "status": "NO DATA"
            }
            return score

        report["M_market"] = market_context

        market_score = market_context.get(
            "market_score",
            0
        )

        try:
            market_score = float(
                market_score
            )
        except Exception:
            market_score = 0

        if market_score >= 80:
            score += 10
        elif market_score >= 60:
            score += 5

        return score


    def _classification(
        self,
        score
    ):

        if score >= 85:
            return "CANSLIM LEADER"

        if score >= 70:
            return "CANSLIM QUALITY"

        if score >= 55:
            return "CANSLIM DEVELOPING"

        if score >= 40:
            return "WATCHLIST"

        return "WEAK"


    def _log_report(self, report):

        logger.info("=" * 70)
        logger.info("CANSLIM FUNDAMENTAL ANALYSIS")
        logger.info("=" * 70)

        logger.info("CURRENT CANSLIM SCORE")
        logger.info("-" * 70)
        logger.info("Current Earnings          : %.2f", report.get("component_scores", {}).get("C", 0))
        logger.info("Annual Earnings Growth    : %.2f", report.get("component_scores", {}).get("A", 0))
        logger.info("New Products / Events     : %.2f", report.get("component_scores", {}).get("N", 0))
        logger.info("Supply / Share Structure  : %.2f", report.get("component_scores", {}).get("S", 0))
        logger.info("Leadership                : %.2f", report.get("component_scores", {}).get("L", 0))
        logger.info("Institutional Sponsorship : %.2f", report.get("component_scores", {}).get("I", 0))
        logger.info("Market Direction          : %.2f", report.get("component_scores", {}).get("M", 0))

        logger.info("-" * 70)
        logger.info("INSTITUTIONAL ASSESSMENT")
        logger.info("  CANSLIM Score          : %.2f", report.get("score", 0))
        logger.info("  Classification         : %s", report.get("classification"))

        logger.info("-" * 70)
        logger.info("COMPONENT STATUS")
        logger.info("  Current Earnings       : %s", "AVAILABLE" if report.get("C_current_earnings") else "NO DATA")
        logger.info("  Annual Growth          : %s", "AVAILABLE" if report.get("A_annual_growth") else "NO DATA")
        logger.info("  Supply Structure       : %s", "AVAILABLE" if report.get("S_supply") else "NO DATA")
        logger.info("  New Products / Events  : %s", "AVAILABLE" if report.get("N_new_products") else "NO DATA")
        logger.info("  Leadership             : %s", "AVAILABLE" if report.get("L_leadership") else "NO DATA")
        logger.info("  Institutional Sponsor  : %s", "AVAILABLE" if report.get("I_institutional") else "NO DATA")
        logger.info("  Market Direction       : %s", "AVAILABLE" if report.get("M_market") else "NO DATA")

        logger.info("=" * 70)