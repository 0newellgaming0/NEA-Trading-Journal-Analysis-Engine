"""
====================================================================
NEA28 SEC ANALYSIS ENGINE

Module:
    secAnalysis.py

System:
    NEA28 Trading Intelligence Platform

Purpose:
    SEC Financial Intelligence
    Institutional Quality Analysis
    Growth Asymmetry Detection
    Fundamental Feature Generation
    ML/Screener Integration

Database Flow:

    SEC EDGAR
        |
    SEC Fetcher Engine
        |
    secFinancials.db
        |
    SECFinancialRepository
        |
    SECAnalysisEngine
        |
    secAnalysis.db
        |
    SECAnalysisRepository

Responsibilities:
    - SEC financial statement analysis
    - SEC XBRL fact normalization
    - Revenue growth analysis
    - Earnings quality analysis
    - Balance sheet analysis
    - Cash flow analysis
    - Margin analysis
    - Institutional scoring
    - Growth Asymmetry classification
    - Screener feature generation

Author:
    Newell Trading Group
====================================================================
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
import os
import csv
import pandas as pd
from modules.path_resolver import get_sec_financials_root
from modules.stock_data_db.sec_financials_db.sec_repository import (
    SECFinancialRepository,
    SECAnalysisRepository
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.sec_analysis_extensions import (
    SECAnalysisExtensions
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.enhanced_earnings import (
    EnhancedEarnings
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.share_structure import (
    ShareStructure
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.capital_allocation import (
    CapitalAllocationEngine
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.annual_growth import (
    AnnualGrowthEngine
)

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.canslim_engine import (
    CANSLIMEngine
)


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(
    "SECAnalysis"
)

if not logger.handlers:
    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | SECAnalysis | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logger.propagate = False

logger.setLevel(
    logging.INFO
)


# ============================================================
# SEC ANALYSIS ENGINE
# ============================================================

class SECAnalysisEngine:

    """
    Central SEC intelligence orchestration engine.

    Reads:
        secFinancials.db

    Writes:
        secAnalysis.db
    """

    def __init__(self):

        self.financial_repository = SECFinancialRepository()

        self.analysis_repository = SECAnalysisRepository()

        # SEC extension layer
        self.extensions_engine = SECAnalysisExtensions()

        logger.info(
            "SEC Analysis Engine initialized"
        )


    # ========================================================
    # JSON SAFETY
    # ========================================================

    def json_safe(
            self,
            data
    ):

        return json.loads(
            json.dumps(
                data,
                default=str
            )
        )


    # ========================================================
    # DATABASE STATUS
    # ========================================================

    def database_status(
            self
    ):

        try:

            return {
                "status": "CONNECTED",
                "financial_repository": "SECFinancialRepository",
                "analysis_repository": "SECAnalysisRepository",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:

            return {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


    # ========================================================
    # LOAD SEC STATEMENTS
    # ========================================================

    def load_financial_statements(self, ticker):
        logger = logging.getLogger("SECAnalysis")
        ticker = str(ticker).upper().strip()

        try:
            df = self.financial_repository.get_statements(ticker)

            if df.empty:
                logger.warning("No SEC statements found %s", ticker)
                return []

            statements = []

            for _, row in df.iterrows():
                try:
                    records = json.loads(row["data_json"])

                    for record in records:
                        record["_statement_type"] = row["statement_type"]
                        statements.append(record)

                except Exception as e:
                    logger.error("Statement decode failed %s %s", ticker, e)
            
            return statements

        except Exception:
            logger.exception("Financial loading failed %s", ticker)
            return []

    def load_xbrl_facts(self, ticker):
        ticker = str(ticker).upper().strip()

        try:
            df = self.financial_repository.get_facts(ticker)

            if df.empty:
                logger.warning("No XBRL facts found %s", ticker)
                return []

            return df.to_dict("records")

        except Exception:
            logger.exception(
                "XBRL fact loading failed %s",
                ticker
            )
            return []

    def build_analysis_dataset(self, ticker):
        statement_records = self.load_financial_statements(ticker)
        fact_records = self.load_xbrl_facts(ticker)

        records = []

        records.extend(statement_records)
        records.extend(fact_records)

        logger.info(
            "Unified SEC dataset: %s statements + %s facts = %s records",
            len(statement_records),
            len(fact_records),
            len(records)
        )

        return records
            
    # ========================================================
    # VALUE NORMALIZATION
    # ========================================================

    def normalize_value(
            self,
            value
    ):

        try:

            if value is None:
                return None

            if isinstance(
                value,
                (
                    int,
                    float
                )
            ):
                return float(value)

            value = (
                str(value)
                .replace(",", "")
                .replace("$", "")
            )

            return float(value)

        except Exception:

            return None


    # ========================================================
    # CONCEPT SEARCH
    # ========================================================

    def find_concept(
            self,
            records,
            concepts
    ):

        results = []

        for row in records:

            concept = str(
                row.get(
                    "concept",
                    ""
                )
            ).lower()

            for target in concepts:

                concept_name = concept.split(":")[-1].lower()

                targets = {
                    c.lower()
                    for c in concepts
                }

                if concept_name in targets:

                    value = self.normalize_value(
                        row.get(
                            "value"
                        )
                    )

                    if value is not None:

                        record = dict(row)

                        record["concept"] = concept

                        record["numeric_value"] = self.normalize_value(
                            row.get("numeric_value", row.get("value"))
                        )

                        record["value"] = record["numeric_value"]

                        results.append(record)

        results.sort(
            key=lambda x: str(
                x.get(
                    "period_end"
                )
            ),
            reverse=True
        )

        return results


    # ========================================================
    # CONCEPT DEBUG LOGGER
    # ========================================================

    def log_concept_candidates(
            self,
            records,
            concepts,
            name
    ):

        logger.info("=" * 70)
        logger.info("CONCEPT DEBUG: %s", name)

        matches = []

        for row in records:

            concept = str(
                row.get(
                    "concept",
                    ""
                )
            )

            for target in concepts:

                if target.lower() in concept.lower():

                    matches.append(
                        {
                            "concept": concept,
                            "label": row.get("label"),
                            "value": row.get("value"),
                            "numeric_value": row.get("numeric_value"),
                            "unit": row.get("unit"),
                            "period_type": row.get("period_type"),
                            "period_start": row.get("period_start"),
                            "period_end": row.get("period_end"),
                            "fiscal_year": row.get("fiscal_year"),
                            "fiscal_period": row.get("fiscal_period"),
                            "statement": row.get("_statement_type")
                        }
                    )

        logger.info(
            "Matches Found: %s",
            len(matches)
        )

        debug_df = pd.DataFrame(matches)

        if not debug_df.empty:

            debug_df = debug_df.sort_values(
                [
                    "period_end",
                    "fiscal_period"
                ],
                ascending=False
            )

            logger.info(
                "\n%s",
                debug_df.to_string(
                    index=False
                )
            )

        logger.info("=" * 70)

        return matches
        
        
    # ========================================================
    # FINANCIAL EXTRACTION
    # ========================================================

    def extract_metrics(
            self,
            records
    ):
        return {
            "revenue": self.find_concept(
                records,
                [
                    "Revenue",
                    "Revenues",
                    "SalesRevenueNet",
                    "SalesRevenueGoodsNet",
                    "OperatingRevenue",
                    "RevenueFromContract",
                    "RevenueFromContractWithCustomerExcludingAssessedTax"
                ]
            ),

            "net_income": self.find_concept(
                records,
                [
                    "NetIncomeLoss",
                    "ProfitLoss",
                    "NetIncomeLossAvailableToCommonStockholdersBasic"
                ]
            ),

            "cash": self.find_concept(
                records,
                [
                    "CashAndCashEquivalentsAtCarryingValue",
                    "CashAndCashEquivalents",
                    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                    "Cash"
                ]
            ),

            "debt": self.find_concept(
                records,
                [
                    "LongTermDebtNoncurrent",
                    "LongTermDebtCurrent",
                    "LongTermDebt",
                    "DebtInstrumentCarryingAmount",
                    "Debt"
                ]
            ),

            "operating_cashflow": self.find_concept(
                records,
                [
                    "NetCashProvidedByUsedInOperatingActivities",
                    "NetCashProvidedByUsedInOperations"
                ]
            )
        }
        
        logger.info("GROWTH INPUT COLUMNS:")
        logger.info(list(df.columns))

        logger.info("GROWTH INPUT SAMPLE:")
        logger.info(
            df[
                [
                    "concept",
                    "numeric_value",
                    "period_start",
                    "period_end",
                    "fiscal_year",
                    "fiscal_period"
                ]
            ].tail(10).to_string()
        )

        logger.info(
            "GROWTH DATA TYPES:\n%s",
            df.dtypes.to_string()
        )        
    
    # ========================================================
    # GROWTH CALCULATION
    # ========================================================

    def calculate_growth(self, df, metric_name="Revenue"):
        try:
            if df is None:
                return {
                    "latest": 0,
                    "previous": 0,
                    "growth": 0,
                    "state": "UNKNOWN"
                }

            if isinstance(df, list):
                if len(df) == 0:
                    return {
                        "latest": 0,
                        "previous": 0,
                        "growth": 0,
                        "state": "UNKNOWN"
                    }

                df = pd.DataFrame(df)

            if not isinstance(df, pd.DataFrame):
                logging.getLogger("SECAnalysis").error(
                    f"calculate_growth invalid input type: {type(df)}"
                )

                return {
                    "latest": 0,
                    "previous": 0,
                    "growth": 0,
                    "state": "INVALID_INPUT"
                }

            if df.empty:
                return {
                    "latest": 0,
                    "previous": 0,
                    "growth": 0,
                    "state": "UNKNOWN"
                }

            required_columns = [
                "numeric_value",
                "period_end",
                "fiscal_year",
                "fiscal_period",
                "concept"
            ]

            missing = [
                c for c in required_columns
                if c not in df.columns
            ]

            if missing:
                logging.getLogger("SECAnalysis").error(
                    f"Growth calculation missing columns: {missing}"
                )

                return {
                    "latest": 0,
                    "previous": 0,
                    "growth": 0,
                    "state": "UNKNOWN"
                }

            growth_df = df[required_columns].copy()

            growth_df["period_end"] = pd.to_datetime(
                growth_df["period_end"],
                errors="coerce"
            )

            growth_df = growth_df.sort_values("period_end")

            growth_df = growth_df.dropna(
                subset=["numeric_value"]
            )

            if len(growth_df) < 2:
                return {
                    "latest": float(
                        growth_df["numeric_value"].iloc[-1]
                    ) if len(growth_df) else 0,
                    "previous": 0,
                    "growth": 0,
                    "state": "INSUFFICIENT_DATA"
                }

            latest = growth_df.iloc[-1]
            previous = growth_df.iloc[-2]

            latest_value = float(latest["numeric_value"])
            previous_value = float(previous["numeric_value"])

            if previous_value == 0:
                growth = 0
            else:
                growth = (
                    (latest_value - previous_value)
                    /
                    abs(previous_value)
                ) * 100

            return {
                "latest": latest_value,
                "previous": previous_value,
                "growth": round(growth, 2),
                "comparison_period": (
                    previous["fiscal_year"],
                    previous["fiscal_period"]
                ),
                "state": (
                    "ACCELERATING"
                    if growth > 10
                    else
                    "DECLINING"
                    if growth < -10
                    else
                    "STABLE"
                )
            }

        except Exception:
            logging.getLogger("SECAnalysis").exception(
                f"{metric_name} growth calculation failed"
            )

            return {
                "latest": 0,
                "previous": 0,
                "growth": 0,
                "state": "ERROR"
            }
    # ========================================================
    # BALANCE SHEET ANALYSIS
    # ========================================================

    def calculate_balance_sheet(
            self,
            records
    ):
        try:
            cash = self.find_concept(
                records,
                [
                    "CashAndCashEquivalentsAtCarryingValue",
                    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
                    "CashAndCashEquivalents",
                    "Cash"
                ]
            )

            debt = self.find_concept(
                records,
                [
                    "LongTermDebtNoncurrent",
                    "LongTermDebtCurrent",
                    "ShortTermBorrowings",
                    "Debt"
                ]
            )

            assets = self.find_concept(
                records,
                [
                    "Assets",
                    "AssetsCurrent"
                ]
            )

            liabilities = self.find_concept(
                records,
                [
                    "Liabilities",
                    "LiabilitiesCurrent"
                ]
            )

            cash_value = (
                cash[0]["value"]
                if cash
                else 0
            )

            debt_value = (
                debt[0]["value"]
                if debt
                else 0
            )

            asset_value = (
                assets[0]["value"]
                if assets
                else 0
            )

            liability_value = (
                liabilities[0]["value"]
                if liabilities
                else 0
            )

            net_cash = (
                cash_value -
                debt_value
            )

            debt_ratio = 0

            if asset_value:
                debt_ratio = (
                    debt_value /
                    asset_value
                ) * 100

            result = {
                "cash": cash_value,
                "debt": debt_value,
                "assets": asset_value,
                "liabilities": liability_value,
                "net_cash": net_cash,
                "debt_to_assets": round(
                    debt_ratio,
                    2
                )
            }

            logger.info(
                "Balance Sheet | Cash=%s Debt=%s Net Cash=%s Debt/Assets=%s",
                cash_value,
                debt_value,
                net_cash,
                result["debt_to_assets"]
            )

            return result

        except Exception as e:
            logger.exception(
                "Balance sheet calculation failed: %s",
                e
            )

            return {}


    # ========================================================
    # CASH FLOW ANALYSIS
    # ========================================================

    def calculate_cashflow(
            self,
            records
    ):
        """
        Evaluates operating cash flow quality.
        """

        try:

            cashflow = self.find_concept(
                records,
                [
                    "netcashprovidedbyusedinoperatingactivities"
                ]
            )

            if not cashflow:

                return {

                    "operating_cashflow": 0,

                    "state":
                        "UNKNOWN"

                }

            value = cashflow[0]["value"]

            if value > 0:

                state = "POSITIVE"

            elif value < 0:

                state = "NEGATIVE"

            else:

                state = "BREAKEVEN"

            logger.info(
                "Cash Flow State=%s Value=%s",
                state,
                value
            )

            return {

                "operating_cashflow":
                    value,

                "state":
                    state

            }

        except Exception as e:

            logger.exception(
                "Cashflow calculation failed: %s",
                e
            )

            return {}


    # ========================================================
    # EARNINGS GROWTH
    # ========================================================

    def calculate_earnings_growth(self, records):

        try:
            income = self.find_concept(
                records,
                [
                    "NetIncomeLoss",
                    "ProfitLoss",
                    "NetIncomeLossAvailableToCommonStockholdersBasic"
                ]
            )

            result = self.calculate_growth(
                income,
                "Net Income"
            )

            logger.info(
                "Earnings Growth | Latest=%s Previous=%s Growth=%s%%",
                result.get("latest"),
                result.get("previous"),
                result.get("growth")
            )

            return {
                "latest_income": result.get("latest",0),
                "previous_income": result.get("previous",0),
                "growth_percent": result.get("growth",0),
                "comparison_period": result.get("comparison_period"),
                "state": result.get("state")
            }

        except Exception:
            logger.exception(
                "Earnings growth failed"
            )
            return {}


    # ========================================================
    # MARGIN ANALYSIS
    # ========================================================

    def calculate_margins(
            self,
            records
    ):
        try:
            revenue = self.find_concept(
                records,
                [
                    "Revenue",
                    "Revenues",
                    "SalesRevenueNet",
                    "RevenueFromContractWithCustomerExcludingAssessedTax"
                ]
            )

            gross_profit = self.find_concept(
                records,
                [
                    "GrossProfit",
                    "GrossProfitLoss"
                ]
            )

            operating_income = self.find_concept(
                records,
                [
                    "OperatingIncomeLoss",
                    "OperatingIncome"
                ]
            )

            revenue_value = 0
            gross_value = 0
            operating_value = 0


            if revenue:
                revenue_value = max(
                    revenue,
                    key=lambda x: x.get(
                        "value",
                        0
                    )
                )["value"]


            if gross_profit:
                gross_value = max(
                    gross_profit,
                    key=lambda x: x.get(
                        "value",
                        0
                    )
                )["value"]


            if operating_income:
                operating_value = max(
                    operating_income,
                    key=lambda x: x.get(
                        "value",
                        0
                    )
                )["value"]

            gross_margin = 0
            operating_margin = 0

            if revenue_value:
                gross_margin = (
                    gross_value /
                    revenue_value
                ) * 100

                operating_margin = (
                    operating_value /
                    revenue_value
                ) * 100

            result = {
                "gross_margin": round(
                    gross_margin,
                    2
                ),
                "operating_margin": round(
                    operating_margin,
                    2
                )
            }

            logger.info(
                "Margins | Gross=%s Operating=%s",
                result["gross_margin"],
                result["operating_margin"]
            )

            return result

        except Exception as e:
            logger.exception(
                "Margin calculation failed: %s",
                e
            )

            return {}     
            
    # ========================================================
    # FINANCIAL RISK
    # ========================================================

    def calculate_financial_risk(self, balance):
        """
        Evaluate balance-sheet financial risk using debt-to-assets.
        """

        ratio = balance.get("debt_to_assets", 1)

        if ratio < 0.25:
            risk = "LOW"
        elif ratio < 0.50:
            risk = "MODERATE"
        elif ratio < 0.70:
            risk = "HIGH"
        else:
            risk = "EXTREME"

        return {
            "risk": risk,
            "debt_to_assets": ratio
        }

    # ========================================================
    # REVENUE ACCELERATION
    # ========================================================

    def calculate_revenue_acceleration(self, revenue):
        """
        Classify revenue growth acceleration.
        """

        growth = revenue.get("growth_percent", 0)

        if growth >= 25:
            state = "ACCELERATING"
        elif growth >= 10:
            state = "GROWING"
        elif growth >= 0:
            state = "STABLE"
        else:
            state = "DECLINING"

        return {
            "state": state,
            "growth": growth
        }

    # ========================================================
    # LIQUIDITY SCORE
    # ========================================================

    def calculate_liquidity_score(self, balance):
        """
        Score balance-sheet liquidity strength using
        total assets versus liabilities.
        """

        assets = balance.get("assets", 0)
        liabilities = balance.get("liabilities", 0)

        if assets <= 0 or liabilities <= 0:
            return 0

        ratio = assets / liabilities

        if ratio >= 2.0:
            return 100
        if ratio >= 1.5:
            return 85
        if ratio >= 1.2:
            return 70
        if ratio >= 1.0:
            return 55
        if ratio >= 0.75:
            return 35

        return 10

    # ========================================================
    # INSTITUTIONAL SCORE
    # ========================================================

    def calculate_institutional_score(self, report):
        """
        Composite institutional-quality score.

        Inputs:
            revenue
            balance sheet
            cash flow
            annual growth
            CANSLIM

        Maximum score = 100
        """

        score = 0

        revenue = report.get("revenue", {})
        balance = report.get("balance_sheet", {})
        cashflow = report.get("cash_flow", {})
        annual_growth = report.get("annual_growth", {})
        canslim = report.get("canslim", {})

        revenue_growth = revenue.get("growth_percent", 0)

        # ----------------------------------------------------
        # Revenue Expansion
        # ----------------------------------------------------

        if revenue_growth > 20:
            score += 35
        elif revenue_growth > 10:
            score += 25
        elif revenue_growth > 0:
            score += 10

        # ----------------------------------------------------
        # Balance Sheet
        # ----------------------------------------------------

        if balance.get("net_cash", 0) > 0:
            score += 30

        if balance.get("debt_to_assets", 1) < 0.40:
            score += 15

        # ----------------------------------------------------
        # Operating Cash Flow
        # ----------------------------------------------------

        if cashflow.get("state") == "POSITIVE":
            score += 20

        # ----------------------------------------------------
        # Annual Growth Plugin
        # ----------------------------------------------------

        growth_quality = annual_growth.get(
            "growth_quality",
            ""
        )

        if growth_quality == "ELITE COMPOUNDER":
            score += 15
        elif growth_quality == "HIGH GROWTH":
            score += 10

        # ----------------------------------------------------
        # CANSLIM Plugin
        # ----------------------------------------------------

        if canslim.get("classification") == "CANSLIM QUALITY":
            score += 15

        return min(score, 100)

    # ========================================================
    # GROWTH ASYMMETRY CLASSIFICATION
    # ========================================================

    def generate_classification(self, report):
        """
        Convert institutional score into
        Growth Asymmetry classifications.
        """

        score = report.get(
            "institutional_score",
            0
        )

        if score >= 85:
            state = "ELITE"
        elif score >= 70:
            state = "INSTITUTIONAL_ACCUMULATION"
        elif score >= 55:
            state = "ACCUMULATION"
        elif score >= 40:
            state = "NEUTRAL"
        elif score >= 20:
            state = "DISTRIBUTION"
        else:
            state = "HIGH_RISK"

        return {
            "classification": state,
            "score": score
        }

    # ========================================================
    # COMPANY ANALYSIS PIPELINE
    # PART 4A
    # ========================================================
    def analyze_company(self, ticker):
        """
        Complete SEC company analysis pipeline.
        Workflow:
        1. Normalize ticker
        2. Load SEC statements
        3. Expand SEC JSON records
        4. Create dataframe
        5. Normalize SEC concepts
        6. Run diagnostics
        7. Execute financial analysis
        8. Execute intelligence plugins
        9. Calculate scoring
        10. Persist analysis
        """

        ticker = str(ticker).upper().strip()

        logger.info("Running SEC analysis %s", ticker)

        try:
            records = self.build_analysis_dataset(ticker)

            if not records:
                logger.warning("No SEC data available %s", ticker)
                return {
                    "ticker": ticker,
                    "status": "NO_DATA"
                }

            df = pd.DataFrame(records)
            
            if "concept" in df.columns and "period_end" in df.columns:
                df = (
                    df.sort_values("period_end")
                      .drop_duplicates(
                          subset=[
                              "concept",
                              "period_end",
                              "fiscal_period",
                              "fiscal_year"
                          ],
                          keep="last"
                      )
                )            

            if df.empty:
                logger.warning("SEC dataframe empty %s", ticker)
                return {"ticker": ticker, "status": "EMPTY_DATA"}

            df.columns = [str(col).lower().strip() for col in df.columns]

            statement_types = df.get(
                "_statement_type",
                pd.Series()
            ).dropna().unique().tolist()

            records = df.to_dict(
                orient="records"
            )

            for record in records:
                if "value" in record:
                    record["value"] = self.normalize_value(
                        record["value"]
                    )

            report = {
                "ticker": ticker,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "records_analyzed": len(records),
                "diagnostics": {
                    "statement_types": statement_types,
                    "records": len(df)
                }
            }

            logger.info("Core SEC calculations complete %s", ticker)
            
            plugin_df = pd.DataFrame(records)

            try:
                extension_results = self.extensions_engine.analyze(plugin_df,ticker,)
            except Exception as e:
                logger.exception("SEC extension analysis failed %s: %s", ticker, e)
                extension_results = {}

            report["extensions"] = extension_results
            logger.info("SEC extension analysis complete %s", ticker)

            report["enhanced_earnings"] = extension_results.get("enhanced_earnings", {})
            report["share_structure"] = extension_results.get("share_structure", {})
            report["float_analysis"] = extension_results.get("float_analysis", {})
            report["annual_growth"] = extension_results.get("annual_growth", {})
            report["new_developments"] = extension_results.get("new_developments", {})
            report["capital_allocation"] = extension_results.get("capital_allocation", {})
            report["canslim"] = extension_results.get("canslim", {})
            
            # ============================================================
            # Markdown Report Blocks (CANSLIM ORDER)
            # ============================================================

            ee = report["enhanced_earnings"]
            ag = report["annual_growth"]
            nd = report["new_developments"]
            fa = report["float_analysis"]
            ss = report["share_structure"]
            ca = report["capital_allocation"]
            cs = report["canslim"]

            latest = ee.get("latest", {})
            previous = ee.get("previous_yoy", {})


            # ============================================================
            # C — CURRENT EARNINGS
            # ============================================================

            report["earnings_report"] = f"""## Current Earnings

            Latest Quarter: {latest.get("year")} {latest.get("period")}
            Latest Earnings: {latest.get("value")}

            Previous YoY Quarter: {previous.get("year")} {previous.get("period")}
            Previous Earnings: {previous.get("value")}

            YoY Growth: {ee.get("growth_pct")}%
            Sequential Growth: {ee.get("sequential_growth_pct")}%
            Annual Growth: {ee.get("annual_growth_pct")}%

            Trend: {ee.get("trend")}
            Consistency: {ee.get("consistency")}""".strip()


            # ============================================================
            # A — ANNUAL EARNINGS / GROWTH
            # ============================================================

            report["annual_growth_report"] = f"""## Annual Growth

            Revenue CAGR 3Y: {ag.get("revenue",{}).get("cagr3")}
            Revenue CAGR 5Y: {ag.get("revenue",{}).get("cagr5")}
            Revenue Trend: {ag.get("revenue",{}).get("trend")}
            Revenue Acceleration: {ag.get("revenue",{}).get("acceleration",{}).get("state")}

            Earnings CAGR 3Y: {ag.get("earnings",{}).get("cagr3")}
            Earnings CAGR 5Y: {ag.get("earnings",{}).get("cagr5")}
            Earnings Trend: {ag.get("earnings",{}).get("trend")}

            Operating CF CAGR 3Y: {ag.get("operating_cashflow",{}).get("cagr3")}
            Operating CF CAGR 5Y: {ag.get("operating_cashflow",{}).get("cagr5")}

            Growth Profile: {ag.get("growth_profile",{}).get("growth_rate")}
            Growth Profile Score: {ag.get("growth_profile",{}).get("score")}

            Growth Quality: {ag.get("growth_quality",{}).get("rating")}
            Growth Quality Score: {ag.get("growth_quality",{}).get("score")}

            Company Stage: {ag.get("company_stage")}""".strip()


            # ============================================================
            # N — NEW DEVELOPMENTS
            # ============================================================

            report["new_developments_report"] = f"""## New Developments

            {json.dumps(nd, indent=2, default=str)}""".strip()


            # ============================================================
            # S — SUPPLY / DEMAND
            # ============================================================

            report["float_analysis_report"] = f"""## Supply / Demand

            Public Float: {fa.get("public_float")}
            Shares Outstanding: {fa.get("shares_outstanding")}

            Float Category: {fa.get("float_category")}
            Float Scarcity: {fa.get("float_scarcity")}

            Supply Trend: {fa.get("share_supply_trend")}
            Dilution State: {fa.get("dilution_state")}

            Buyback Support: {fa.get("buyback_support")}
            Institutional Supply Impact: {fa.get("institutional_supply_impact")}

            Float Quality: {fa.get("float_quality")}
            Float Score: {fa.get("float_score")}""".strip()


            report["ownership_report"] = f"""## Share Structure

            Current Shares: {ss.get("current_shares")}
            Previous Shares: {ss.get("previous_shares")}

            Current Share Change: {ss.get("current_share_change_pct")}%
            3-Year Share CAGR: {ss.get("three_year_cagr")}%
            5-Year Share CAGR: {ss.get("five_year_cagr")}%

            Capital Base Trend: {ss.get("capital_base_trend")}
            Share Supply Direction: {ss.get("share_supply_direction")}

            Buyback Support: {ss.get("buyback_support")}
            Net Share Impact: {ss.get("net_share_impact")}

            Supply Impact: {ss.get("supply_impact")}
            Ownership Trend: {ss.get("ownership_trend")}

            Dilution Risk: {ss.get("dilution_risk")}
            Capital Quality: {ss.get("capital_quality")}""".strip()


            # ============================================================
            # L — LEADERSHIP / CAPITAL ALLOCATION QUALITY
            # ============================================================

            report["capital_allocation_report"] = f"""## Capital Allocation

            Net Position: {ca.get("net_position")}
            Capital Structure: {ca.get("structure")}

            Balance Sheet Strength: {ca.get("balance_sheet_strength")}
            Financial Flexibility: {ca.get("financial_flexibility")}

            CapEx: {ca.get("capex")}
            CapEx State: {ca.get("capex_state")}

            R&D: {ca.get("rnd")}
            R&D / Revenue: {ca.get("rnd_to_revenue_pct")}%

            CapEx / OCF: {ca.get("capex_to_ocf_pct")}

            Investment Strategy: {ca.get("investment_strategy")}
            Capital Efficiency: {ca.get("capital_efficiency")}

            Allocation Sustainability: {ca.get("allocation_sustainability")}
            Allocation Score: {ca.get("score")}
            Quality: {ca.get("quality")}""".strip()


            # ============================================================
            # I — INSTITUTIONAL SPONSORSHIP
            # ============================================================

            report["canslim_report"] = f"""## Institutional Sponsorship

            Current Earnings: {cs.get("current_earnings")}
            Annual Growth: {cs.get("annual_growth")}

            Institutional Sponsorship: {cs.get("institutional")}
            Leadership: {cs.get("leadership")}

            Supply / Demand: {cs.get("supply_demand")}
            New Development: {cs.get("new_development")}

            CANSLIM Score: {cs.get("score")}
            Classification: {cs.get("classification")}""".strip()


            # ============================================================
            # M — MARKET DIRECTION
            # ============================================================

            report["market_direction_report"] = f"""## Market Direction

            Market Direction: {cs.get("market_direction")}""".strip()

            enhanced_earnings = report.get("enhanced_earnings", {})
            share_structure = report.get("share_structure", {})
            capital_allocation = report.get("capital_allocation", {})
            annual_growth = report.get("annual_growth", {})
            canslim = report.get("canslim", {})

            report["institutional_score"] = self.calculate_institutional_score(report)
            report["growth_asymmetry_score"] = report["institutional_score"]

            classification = self.generate_classification(report)

            report["classification"] = classification

            report["financial_risk"] = ca.get(
                "financial_risk",
                {}
            )

            report["liquidity_score"] = ca.get(
                "liquidity_score",
                0
            )

            report["revenue_acceleration"] = ag.get(
                "revenue",
                {}
            ).get(
                "acceleration",
                {}
            )

            report["analysis_status"] = "COMPLETE"
            report["completed_timestamp"] = datetime.utcnow().isoformat()

            try:
                self.analysis_repository.save_company_analysis(
                    ticker,
                    report
                )
                logger.info("SEC analysis saved %s", ticker)
            except Exception as e:
                logger.exception("SEC analysis persistence failed %s: %s", ticker, e)

            return report

            report["analysis_status"] = "COMPLETE"
            report["completed_timestamp"] = datetime.utcnow().isoformat()

            try:
                self.analysis_repository.save_company_analysis(
                    ticker,
                    report
                )
                logger.info("SEC analysis saved %s", ticker)
            except Exception as e:
                logger.exception("SEC analysis persistence failed %s: %s", ticker, e)

            return report

        except Exception as e:
            logger.exception("Company analysis failed %s: %s", ticker, e)
            return {
                "ticker": ticker,
                "status": "ERROR",
                "error": str(e)
            }            


    # ========================================================
    # REPORTING AND SCREENER INTERFACE
    # PART 5
    # ========================================================

    def get_analysis(self, ticker):
        """
        Retrieve stored SEC analysis.

        Source:
            secAnalysis.db

        Repository:
            SECAnalysisRepository
        """

        ticker = str(ticker).upper().strip()

        try:
            analysis = self.analysis_repository.get_company_analysis(
                ticker
            )

            if not analysis:
                logger.warning(
                    "No stored SEC analysis found %s",
                    ticker
                )
                return None

            logger.info(
                "Stored SEC analysis retrieved %s",
                ticker
            )

            return analysis

        except Exception as e:
            logger.exception(
                "Analysis retrieval failed %s: %s",
                ticker,
                e
            )
            return None

    # ========================================================
    # SCREENER OUTPUT
    # ========================================================

    def screener_output(self, ticker):
        """
        Generate machine-readable SEC intelligence output.

        Used by:
        - Growth Asymmetry Screener
        - Fundamental Ranking
        - ML Feature Generation
        - Trading Dashboard
        """

        ticker = str(ticker).upper().strip()

        try:
            report = self.get_analysis(
                ticker
            )

            if not report:
                return {
                    "ticker": ticker,
                    "status": "NO_ANALYSIS"
                }

            output = {
                "ticker": ticker,

                "sec_quality_score": report.get(
                    "institutional_score",
                    0
                ),

                "growth_asymmetry_score": report.get(
                    "growth_asymmetry_score",
                    0
                ),

                "institutional_state": report.get(
                    "classification",
                    "UNKNOWN"
                ),

                "revenue_growth": report.get(
                    "revenue",
                    {}
                ).get(
                    "growth_percent",
                    0
                ),

                "cash_position": report.get(
                    "balance_sheet",
                    {}
                ).get(
                    "cash",
                    0
                ),

                "net_cash": report.get(
                    "balance_sheet",
                    {}
                ).get(
                    "net_cash",
                    0
                ),

                "cashflow_state": report.get(
                    "cash_flow",
                    {}
                ).get(
                    "state",
                    "UNKNOWN"
                ),

                "capital_structure": report.get(
                    "balance_sheet",
                    {}
                ),

                "float": report.get(
                    "share_structure",
                    {}
                ).get(
                    "float",
                    None
                ),

                "annual_growth": report.get(
                    "annual_growth",
                    {}
                ),

                "canslim": report.get(
                    "canslim",
                    {}
                ),

                "classification": report.get(
                    "classification",
                    "UNKNOWN"
                ),

                "analysis_timestamp": report.get(
                    "analysis_timestamp"
                )
            }

            logger.info(
                "Screener output generated %s",
                ticker
            )

            return output

        except Exception as e:
            logger.exception(
                "Screener output failed %s: %s",
                ticker,
                e
            )

            return {
                "ticker": ticker,
                "status": "ERROR",
                "error": str(e)
            }

    # ========================================================
    # CLOSE ENGINE
    # ========================================================

    def close(self):
        """
        Safely close repository connections.
        """

        try:
            if hasattr(
                    self.analysis_repository,
                    "close"
            ):
                self.analysis_repository.close()

            if hasattr(
                    self.financial_repository,
                    "close"
            ):
                self.financial_repository.close()

            logger.info(
                "SEC Analysis Engine closed"
            )

        except Exception as e:
            logger.exception(
                "SEC Analysis Engine shutdown failed: %s",
                e
            )

            