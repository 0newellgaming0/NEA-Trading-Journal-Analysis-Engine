"""
NEA28 SEC ANALYSIS EXTENSIONS

Integration layer for advanced SEC intelligence:

- Enhanced Earnings
- Share Structure
- Annual Growth
- Capital Allocation
- CANSLIM

Used by:
- SECAnalysis
- Growth Asymmetry Engine
- Institutional Ranking Engine
"""

from __future__ import annotations

import logging

from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.enhanced_earnings import EnhancedEarnings
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.share_structure import ShareStructure
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.annual_growth import AnnualGrowthEngine
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.capital_allocation import CapitalAllocationEngine
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.canslim_engine import CANSLIMEngine
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.float_analysis import FloatAnalysis
from modules.stock_data_db.sec_financials_db.sec_analysis_plugins.new_developments import NewDevelopmentsEngine


logger = logging.getLogger("SECAnalysisExtensions")


class SECAnalysisExtensions:

    def __init__(self):

        self.earnings_engine = EnhancedEarnings()
        self.share_engine = ShareStructure()
        self.float_engine = FloatAnalysis()
        self.growth_engine = AnnualGrowthEngine()
        self.capital_engine = CapitalAllocationEngine()
        self.canslim_engine = CANSLIMEngine() 
        self.developments_engine = NewDevelopmentsEngine()

        logger.info(
            "SEC extension engines initialized"
        )


    def _execute(
        self,
        name,
        engine,
        *args
    ):

        logger.info(
            "Running %s",
            name
        )

        try:

            result = engine.analyze(
                *args
            )

            if result is None:
                return {}

            if isinstance(result, dict):
                return result

            return {
                "value": result
            }

        except Exception as exc:

            logger.exception(
                "%s failed",
                name
            )

            return {
                "status": "ERROR",
                "error": str(exc)
            }


    def safe_round(
        self,
        value,
        digits=2
    ):

        try:

            if value is None:
                return 0

            return round(
                float(value),
                digits
            )

        except Exception:

            return 0


    def analyze(
        self,
        df,
        ticker=None,
        market_context=None
    ):

        results = {}

        results["enhanced_earnings"] = self._execute(
            "Enhanced Earnings",
            self.earnings_engine,
            df
        )

        self._log_earnings(
            results["enhanced_earnings"]
        )


        results["share_structure"] = self._execute(
            "Share Structure",
            self.share_engine,
            df,
            ticker
        )

        self._log_share_structure(
            results["share_structure"]
        )

        results["float_analysis"] = self._execute(
            "Float Analysis",
            self.float_engine,
            df
        )

        self._log_float_analysis(
            results["float_analysis"]
        )

        results["annual_growth"] = self._execute(
            "Annual Growth",
            self.growth_engine,
            df
        )

        self._log_growth(
            results["annual_growth"]
        )

        results["new_developments"] = self._execute(
            "New Developments",
            self.developments_engine,
            df
        )

        self._log_developments(
            results["new_developments"]
        )


        results["capital_allocation"] = self._execute(
            "Capital Allocation",
            self.capital_engine,
            df
        )

        self._log_capital(
            results["capital_allocation"]
        )


        results["canslim"] = self.canslim_engine.analyze(
            ticker=ticker,
            earnings=results["enhanced_earnings"],
            annual_growth=results["annual_growth"],
            share_structure=results["share_structure"],
            capital_allocation=results["capital_allocation"],
            market_context=market_context,
            new_events=results["new_developments"],
            leadership=results["float_analysis"]
        )

        self._log_canslim(
            results["canslim"]
        )


        results["fundamental_quality_score"] = self._quality_score(
            results
        )

        logger.info(
            "Fundamental Quality Score : %s",
            results["fundamental_quality_score"]
        )

        logger.info(
            "SEC extension analysis complete"
        )

        return results


    def _log_earnings(
        self,
        data
    ):

        logger.info(
            "=============================="
        )


    def _log_share_structure(
        self,
        data
    ):

        logger.info(
            "=============================="
        )

    def _log_float_analysis(
        self,
        data
    ):

        logger.info(
            "=============================="
        )

    def _log_growth(
        self,
        data
    ):

        logger.info(
            "=============================="
        )

    def _log_developments(
        self,
        data
    ):

        logger.info(
            "=============================="
        )
        
    def _log_capital(
        self,
        data
    ):

        logger.info(
            "=============================="
        )


    def _log_canslim(
        self,
        data
    ):

        logger.info(
            "=============================="
        )


    def _quality_score(
        self,
        data
    ):

        score = 0

        earnings = data.get(
            "enhanced_earnings",
            {}
        )

        if earnings.get("trend") == "STRONG UP":
            score += 20

        elif earnings.get("trend") == "UP":
            score += 10


        growth = data.get(
            "annual_growth",
            {}
        )

        if growth.get("growth_quality") in (
            "ELITE COMPOUNDER",
            "HIGH GROWTH"
        ):
            score += 25

        elif growth.get("growth_quality") == "GROWING":
            score += 10


        capital = data.get(
            "capital_allocation",
            {}
        )
        
        float_data = data.get(
            "float_analysis",
            {}
        )

        try:

            score += (
                float_data.get(
                    "float_score",
                    0
                )
                *
                0.25
            )

        except Exception:
            pass        

        if capital.get("capital_structure") == "NET CASH":
            score += 20


        canslim = data.get(
            "canslim",
            {}
        )

        try:
            score += float(
                canslim.get(
                    "score",
                    0
                )
            ) * 0.35

        except Exception:
            pass


        return round(
            min(score,100),
            2
        )