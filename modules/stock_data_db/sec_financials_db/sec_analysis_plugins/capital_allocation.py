"""
====================================================================
NEA28 CAPITAL ALLOCATION ENGINE

Module:
    capital_allocation.py

Purpose
-------
Institutional capital allocation intelligence using SEC XBRL data.

Analyzes:
- Cash Position
- Debt Structure
- Net Cash / Net Debt
- Buybacks
- Dividends
- Capital Expenditures
- R&D Investment
- Operating Cash Flow Support
- Capital Allocation Quality

Used By:
- SECAnalysis
- SECAnalysisExtensions
- CANSLIM Engine
- Institutional Ranking
- Growth Asymmetry Engine

====================================================================
"""

from __future__ import annotations

import logging

import pandas as pd

from modules.stock_data_db.sec_financials_db.sec_concepts import (
    SEC_BALANCE_SHEET_CONCEPTS,
    SEC_CASHFLOW_CONCEPTS,
    SEC_DEBT_CONCEPTS,
    SEC_INCOME_CONCEPTS,
)

logger = logging.getLogger("CapitalAllocation")


CASH_CONCEPTS = [
    SEC_BALANCE_SHEET_CONCEPTS["CASH"],
    SEC_BALANCE_SHEET_CONCEPTS["CASH_RESTRICTED"],
]

DEBT_CONCEPTS = [
    SEC_DEBT_CONCEPTS["LONG_TERM_DEBT"],
    SEC_DEBT_CONCEPTS["LONG_TERM_DEBT_CURRENT"],
    SEC_DEBT_CONCEPTS["LONG_TERM_DEBT_NONCURRENT"],
    SEC_DEBT_CONCEPTS["DEBT_CARRYING_VALUE"],
    SEC_DEBT_CONCEPTS["COMMERCIAL_PAPER"],
    SEC_DEBT_CONCEPTS["DEBT_REPAYMENT_CURRENT"],
]

DIVIDEND_CONCEPTS = [
    SEC_CASHFLOW_CONCEPTS["DIVIDENDS"],
]

BUYBACK_CONCEPTS = [
    SEC_CASHFLOW_CONCEPTS["SHARE_REPURCHASES"],
]

CAPEX_CONCEPTS = [
    SEC_CASHFLOW_CONCEPTS["CAPEX"],
]

RND_CONCEPTS = [
    SEC_INCOME_CONCEPTS["R_AND_D"],
]

OPERATING_CF_CONCEPTS = [
    SEC_CASHFLOW_CONCEPTS["OPERATING_CASHFLOW"],
]


class CapitalAllocationEngine:

    def __init__(self):

        logger.info(
            "Capital Allocation Engine initialized"
        )


    def analyze(self, df: pd.DataFrame):
        try:
            logger.info("Running Capital Allocation Analysis")

            buybacks = self._latest(df, BUYBACK_CONCEPTS)
            dividends = self._latest(df, DIVIDEND_CONCEPTS)

            report = {
                "cash": self._latest(df, CASH_CONCEPTS),
                "debt": self._sum_latest(df, DEBT_CONCEPTS),
                "capex": self._latest(df, CAPEX_CONCEPTS),
                "rnd": self._latest(df, RND_CONCEPTS),
                "operating_cashflow": self._latest(df, OPERATING_CF_CONCEPTS),
                "revenue": self._latest(df, [SEC_INCOME_CONCEPTS["REVENUE"]]),
            }

            cash = report["cash"] or 0.0
            debt = report["debt"] or 0.0
            capex = abs(report["capex"] or 0.0)
            rnd = abs(report["rnd"] or 0.0)
            ocf = abs(report["operating_cashflow"] or 0.0)
            revenue = abs(report["revenue"] or 0.0)

            report["net_position"] = cash - debt

            report.update(self._classify_structure(report))

            report["capex_to_ocf_pct"] = (capex / ocf * 100.0) if ocf else 0.0
            report["rnd_to_revenue_pct"] = (rnd / revenue * 100.0) if revenue else 0.0

            report["capex_state"] = self._capex_state(report)
            report["cash_reinvestment"] = self._cash_reinvestment(report)
            report["investment_strategy"] = self._investment_strategy(report)
            report["financial_flexibility"] = self._financial_flexibility(report)
            report["allocation_sustainability"] = self._allocation_sustainability(report)

            report["score"] = self._score(
                report,
                buybacks=buybacks,
                dividends=dividends,
            )

            report["capital_efficiency"] = self._capital_efficiency(report)
            report["quality"] = self._quality(report)

            self._log_report(report)

            return report

        except Exception:
            logger.exception("Capital allocation analysis failed")

            return {
                "score": 0,
                "quality": "FAILED",
                "error": True,
            }


    def _latest(
        self,
        df,
        concepts
    ):

        rows = df[
            df["concept"].isin(
                concepts
            )
        ].copy()


        if rows.empty:
            return None


        rows["numeric_value"] = pd.to_numeric(
            rows["numeric_value"],
            errors="coerce"
        )


        rows = rows.dropna(
            subset=[
                "numeric_value"
            ]
        )


        if rows.empty:
            return None


        rows = rows.sort_values(
            [
                "period_end",
                "filing_date"
            ],
            ascending=False
        )


        return float(
            rows.iloc[0]["numeric_value"]
        )


    def _sum_latest(
        self,
        df,
        concepts
    ):

        rows = df[
            df["concept"].isin(
                concepts
            )
        ].copy()


        if rows.empty:
            return 0.0


        rows["numeric_value"] = pd.to_numeric(
            rows["numeric_value"],
            errors="coerce"
        )


        rows = rows.dropna(
            subset=[
                "numeric_value"
            ]
        )


        if rows.empty:
            return 0.0


        rows = rows.sort_values(
            "period_end",
            ascending=False
        )


        latest = rows.iloc[0]["period_end"]


        rows = rows[
            rows["period_end"] == latest
        ]


        return float(
            rows["numeric_value"].sum()
        )


    def _classify_structure(
        self,
        report
    ):

        net = report["net_position"]


        if net > 0:

            return {
                "structure": "NET CASH",
                "balance_sheet_strength": "STRONG"
            }


        if net < 0:

            return {
                "structure": "NET DEBT",
                "balance_sheet_strength": "WEAK"
            }


        return {
            "structure": "BALANCED",
            "balance_sheet_strength": "NEUTRAL"
        }


    def _classify_allocation(
        self,
        report
    ):


        buybacks = report["buybacks"]

        dividends = report["dividends"]


        return {

            "buyback_state": (
                "ACTIVE"
                if buybacks and abs(buybacks) > 0
                else "NONE"
            ),

            "dividend_state": (
                "PAYING"
                if dividends and abs(dividends) > 0
                else "NONE"
            ),


            "capex_state":
                self._capex_state(
                    report
                )

        }

    def _capex_state(self, report):
        ratio = report.get("capex_to_ocf_pct", 0.0)

        if ratio >= 50:
            return "CAPITAL INTENSIVE"
        if ratio >= 25:
            return "EXPANSION"
        if ratio >= 10:
            return "EFFICIENT GROWTH"
        if ratio > 0:
            return "ASSET-LIGHT"
        return "UNKNOWN"

    def _cash_reinvestment(self, report):
        ocf = abs(report.get("operating_cashflow") or 0.0)
        capex = abs(report.get("capex") or 0.0)
        rnd = abs(report.get("rnd") or 0.0)

        if ocf == 0:
            return "UNKNOWN"

        ratio = ((capex + rnd) / ocf) * 100.0

        report["total_reinvestment_pct"] = ratio

        if ratio >= 50:
            return "HIGH"
        if ratio >= 25:
            return "MODERATE"
        if ratio > 0:
            return "LOW"
        return "NONE"


    def _investment_strategy(self, report):
        capex_state = report.get("capex_state")
        rnd_pct = report.get("rnd_to_revenue_pct", 0.0)

        if rnd_pct >= 10:
            return "INNOVATION LED"

        if capex_state == "CAPITAL INTENSIVE":
            return "INFRASTRUCTURE EXPANSION"

        if capex_state == "EXPANSION":
            return "GROWTH INVESTMENT"

        if capex_state == "ASSET-LIGHT":
            return "ASSET-LIGHT INNOVATION"

        return "BALANCED ALLOCATION"


    def _financial_flexibility(self, report):
        cash = report.get("cash") or 0.0
        debt = report.get("debt") or 0.0
        ocf = abs(report.get("operating_cashflow") or 0.0)

        if cash >= debt:
            return "HIGH"

        if ocf >= debt * 0.25:
            return "HIGH"

        if ocf >= debt * 0.10:
            return "MODERATE"

        return "LOW"


    def _allocation_sustainability(self, report):
        ocf = abs(report.get("operating_cashflow") or 0.0)
        capex = abs(report.get("capex") or 0.0)
        rnd = abs(report.get("rnd") or 0.0)

        if ocf == 0:
            return "UNKNOWN"

        ratio = (capex + rnd) / ocf

        if ratio <= 0.60:
            return "HIGHLY SUSTAINABLE"

        if ratio <= 0.90:
            return "SUSTAINABLE"

        if ratio <= 1.00:
            return "FULLY FUNDED"

        return "UNSUSTAINABLE"


    def _capital_efficiency(self, report):
        efficiency = 0

        if report.get("structure") == "NET CASH":
            efficiency += 2

        if report.get("financial_flexibility") == "HIGH":
            efficiency += 2

        if report.get("allocation_sustainability") in (
            "HIGHLY SUSTAINABLE",
            "SUSTAINABLE",
        ):
            efficiency += 2

        if report.get("cash_reinvestment") in (
            "MODERATE",
            "HIGH",
        ):
            efficiency += 2

        if report.get("investment_strategy") in (
            "INNOVATION LED",
            "ASSET-LIGHT INNOVATION",
            "GROWTH INVESTMENT",
        ):
            efficiency += 2

        if efficiency >= 9:
            return "ELITE"

        if efficiency >= 7:
            return "EXCELLENT"

        if efficiency >= 5:
            return "STRONG"

        if efficiency >= 3:
            return "AVERAGE"

        return "WEAK"

    def _score(self, report, buybacks=None, dividends=None):
        score = 50

        if report.get("structure") == "NET CASH":
            score += 20

        elif report.get("structure") == "NET DEBT":
            score -= 15

        if buybacks and abs(buybacks) > 0:
            score += 10

        if dividends and abs(dividends) > 0:
            score += 5

        if report.get("capex_state") in (
            "EFFICIENT GROWTH",
            "EXPANSION",
        ):
            score += 10

        if report.get("investment_strategy") == "INNOVATION LED":
            score += 5

        if report.get("rnd"):
            score += 5

        return max(0, min(100, score))


    def _quality(self, report):

        score = report.get("score", 0)

        if (
            report.get("investment_strategy") in (
                "INNOVATION LED",
                "ASSET-LIGHT INNOVATION",
            )
            and report.get("allocation_sustainability") == "HIGHLY SUSTAINABLE"
            and report.get("capital_efficiency") in (
                "STRONG",
                "EXCELLENT",
                "ELITE",
            )
        ):
            return "HIGH QUALITY"

        if score >= 75:
            return "EXCELLENT"

        if score >= 60:
            return "GOOD"

        if score >= 45:
            return "MODERATE"

        return "WEAK"
        

    def _safe_percent(self, value):

        if value is None:
            return 0.0

        try:
            return float(value)

        except (TypeError, ValueError):
            return 0.0


    def _log_report(self, report):

        def pct(value):
            return self._safe_percent(value)

        logger.info("=" * 70)
        logger.info("CAPITAL ALLOCATION ANALYSIS")
        logger.info("=" * 70)

        logger.info("BALANCE SHEET")
        logger.info("-" * 70)
        logger.info("Cash Position              : %s", report.get("cash"))
        logger.info("Total Debt                 : %s", report.get("debt"))
        logger.info("Net Position               : %s", report.get("net_position"))
        logger.info("Capital Structure          : %s", report.get("structure"))
        logger.info("Balance Sheet Strength     : %s", report.get("balance_sheet_strength"))

        logger.info("CAPITAL DEPLOYMENT")
        logger.info("-" * 70)
        logger.info("Operating Cash Flow        : %s", report.get("operating_cashflow"))
        logger.info("Capital Expenditures       : %s", report.get("capex"))
        logger.info("Research & Development     : %s", report.get("rnd"))
        logger.info("CapEx Strategy             : %s", report.get("capex_state"))
        logger.info("CapEx / OCF                : %.2f%%", pct(report.get("capex_to_ocf_pct")))
        logger.info("R&D / Revenue              : %.2f%%", pct(report.get("rnd_to_revenue_pct")))

        logger.info("CAPITAL POLICY")
        logger.info("-" * 70)
        logger.info("Cash Reinvestment          : %s", report.get("cash_reinvestment"))
        logger.info("Investment Strategy        : %s", report.get("investment_strategy"))
        logger.info("Financial Flexibility      : %s", report.get("financial_flexibility"))
        logger.info("Allocation Sustainability  : %s", report.get("allocation_sustainability"))

        logger.info("INSTITUTIONAL ASSESSMENT")
        logger.info("-" * 70)
        logger.info("Capital Efficiency         : %s", report.get("capital_efficiency"))
        logger.info("Capital Allocation Quality : %s", report.get("quality"))
        logger.info("Allocation Score           : %.2f", pct(report.get("score")))

        logger.info("=" * 70)