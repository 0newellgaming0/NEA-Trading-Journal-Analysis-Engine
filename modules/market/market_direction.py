"""
====================================================================
NEA28 MARKET DIRECTION ENGINE

Module:
    modules/market/market_direction.py

Purpose:
    Institutional CANSLIM Market Direction (M) engine.

Responsibilities:
    - Consume institutional market subsystem outputs
    - Calculate CANSLIM M score
    - Determine market condition
    - Determine market cycle
    - Aggregate institutional warnings
    - Generate ML features
    - Produce standardized market report

Dependencies:
    index_engine
    breadth_engine
    trend_engine
    follow_through_engine
    distribution_engine
    volatility_engine
    liquidity_engine
    market_state_store

Architecture:
    Market plugins calculate data.
    MarketDirectionEngine interprets state.

====================================================================
"""

import logging
from datetime import datetime


logger = logging.getLogger("MarketDirectionEngine")


class MarketDirectionEngine:
    """
    Institutional CANSLIM Market Direction Engine.
    """

    def __init__(self):
        logger.info(
            "Market Direction Engine initialized"
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

    def _calculate_market_score(
        self,
        context
    ):
        """
        CANSLIM M composite score.

        Weighting:

        Index strength       30%
        Breadth              20%
        Trend                15%
        Follow-through       15%
        Liquidity            10%
        Volatility           10%
        """

        score = 0

        indexes = context.get(
            "indexes",
            {}
        )

        breadth = context.get(
            "breadth",
            {}
        )

        trend = context.get(
            "trend",
            {}
        )

        follow = context.get(
            "follow_through",
            {}
        )

        liquidity = context.get(
            "liquidity",
            {}
        )

        volatility = context.get(
            "volatility",
            {}
        )


        index_scores = []

        for data in indexes.values():

            index_scores.append(
                self._safe_float(
                    data.get(
                        "trend_strength",
                        0
                    )
                )
            )


        index_score = 0

        if index_scores:
            index_score = sum(
                index_scores
            ) / len(
                index_scores
            )


        score += index_score * 0.30

        score += self._safe_float(
            breadth.get(
                "breadth_score",
                0
            )
        ) * 0.20

        score += self._safe_float(
            trend.get(
                "trend_strength",
                0
            )
        ) * 0.15

        score += self._safe_float(
            follow.get(
                "follow_through_strength",
                0
            )
        ) * 0.15

        score += self._safe_float(
            liquidity.get(
                "liquidity_score",
                0
            )
        ) * 0.10

        score += self._safe_float(
            volatility.get(
                "volatility_score",
                0
            )
        ) * 0.10


        return round(
            min(
                score,
                100
            ),
            2
        )

    def _detect_market_condition(
        self,
        score,
        context
    ):
        distribution = context.get(
            "distribution",
            {}
        )

        follow = context.get(
            "follow_through",
            {}
        )

        distribution_days = distribution.get(
            "distribution_days",
            0
        )

        follow_day = follow.get(
            "follow_through_day",
            False
        )


        if (
            score >= 80
            and distribution_days <= 3
            and follow_day
        ):
            return "BUYABLE_UPTREND"


        if (
            score >= 65
            and distribution_days <= 5
        ):
            return "UPTREND_UNDER_REVIEW"


        if distribution_days >= 6:
            return "MARKET_UNDER_PRESSURE"


        if score < 40:
            return "BEARISH_CONDITIONS"


        return "NEUTRAL"

    def _detect_cycle_position(
        self,
        score,
        context
    ):
        distribution = context.get(
            "distribution",
            {}
        )

        breadth = context.get(
            "breadth",
            {}
        )

        distribution_days = distribution.get(
            "distribution_days",
            0
        )

        breadth_score = breadth.get(
            "breadth_score",
            0
        )


        if (
            score >= 85
            and breadth_score >= 75
            and distribution_days <= 2
        ):
            return "CONFIRMED_ADVANCE"


        if (
            score >= 70
            and distribution_days <= 4
        ):
            return "EARLY_ADVANCE"


        if (
            score >= 80
            and distribution_days >= 4
        ):
            return "LATE_ADVANCE"


        if distribution_days >= 6:
            return "DISTRIBUTION"


        if score < 40:
            return "DECLINE"


        return "SIDEWAYS"

    def _calculate_confidence(
        self,
        context
    ):
        confidence = 0

        if context.get(
            "indexes"
        ):
            confidence += 25

        if context.get(
            "breadth"
        ):
            confidence += 20

        if context.get(
            "trend"
        ):
            confidence += 20

        if context.get(
            "volatility"
        ):
            confidence += 15

        if context.get(
            "liquidity"
        ):
            confidence += 20


        return min(
            confidence,
            100
        )

    def _generate_warnings(
        self,
        context
    ):
        warnings = []

        distribution = context.get(
            "distribution",
            {}
        )

        breadth = context.get(
            "breadth",
            {}
        )

        volatility = context.get(
            "volatility",
            {}
        )


        if distribution.get(
            "distribution_days",
            0
        ) >= 4:

            warnings.append(
                "RISING_DISTRIBUTION"
            )


        if breadth.get(
            "breadth_score",
            0
        ) < 45:

            warnings.append(
                "BREADTH_DETERIORATION"
            )


        if volatility.get(
            "risk_level",
            ""
        ) in (
            "HIGH",
            "EXTREME"
        ):

            warnings.append(
                "VOLATILITY_RISK"
            )


        if not warnings:

            warnings.append(
                "NO_MAJOR_WARNING"
            )


        return warnings

    def _build_ml_features(
        self,
        result
    ):
        return {

            "market_score": result.get(
                "market_score",
                0
            ),

            "breadth_score": result.get(
                "breadth_score",
                0
            ),

            "volatility_score": result.get(
                "volatility_score",
                0
            ),

            "liquidity_score": result.get(
                "liquidity_score",
                0
            ),

            "distribution_days": result.get(
                "distribution_days",
                0
            ),

            "confidence": result.get(
                "confidence",
                0
            )

        }
        
    def analyze(
        self,
        market_context
    ):
        """
        Execute institutional CANSLIM
        market direction analysis.

        Input:

        {
            "indexes": {},
            "breadth": {},
            "trend": {},
            "follow_through": {},
            "distribution": {},
            "volatility": {},
            "liquidity": {},
            "history": {}
        }

        Output:

        {
            "component": "M",
            "market_score":,
            "market_condition":,
            "cycle_position":,
            "confidence":,
            "warnings":,
            "ml_features":
        }
        """

        logger.info(
            "Running Market Direction Analysis"
        )


        if not isinstance(
            market_context,
            dict
        ):
            return {}


        score = self._calculate_market_score(
            market_context
        )


        breadth = market_context.get(
            "breadth",
            {}
        )

        distribution = market_context.get(
            "distribution",
            {}
        )

        volatility = market_context.get(
            "volatility",
            {}
        )

        liquidity = market_context.get(
            "liquidity",
            {}
        )

        trend = market_context.get(
            "trend",
            {}
        )


        result = {

            "component": "M",

            "component_name": "Market Direction",

            "timestamp": datetime.utcnow().isoformat(),

            "market_score": score,

            "market_condition": self._detect_market_condition(
                score,
                market_context
            ),

            "cycle_position": self._detect_cycle_position(
                score,
                market_context
            ),

            "trend_state": trend.get(
                "trend_state",
                "UNKNOWN"
            ),

            "trend_strength": trend.get(
                "trend_strength",
                0
            ),

            "breadth_score": breadth.get(
                "breadth_score",
                0
            ),

            "volatility_score": volatility.get(
                "volatility_score",
                0
            ),

            "liquidity_score": liquidity.get(
                "liquidity_score",
                0
            ),

            "distribution_days": distribution.get(
                "distribution_days",
                0
            ),

            "stall_days": distribution.get(
                "stall_days",
                0
            ),

            "churning_days": distribution.get(
                "churning_days",
                0
            ),

            "follow_through_day": market_context.get(
                "follow_through",
                {}
            ).get(
                "follow_through_day",
                False
            ),

            "confidence": self._calculate_confidence(
                market_context
            )

        }


        result["risk_level"] = volatility.get(
            "risk_level",
            "UNKNOWN"
        )


        result["institutional_warnings"] = self._generate_warnings(
            market_context
        )


        result["ml_features"] = self._build_ml_features(
            result
        )


        return result


    def get_market_report(
        self,
        analysis
    ):
        """
        Public market report API.
        """

        if not isinstance(
            analysis,
            dict
        ):
            return {}


        return {

            "component": "M",

            "name": "Market Direction",

            "score": analysis.get(
                "market_score",
                0
            ),

            "condition": analysis.get(
                "market_condition",
                "UNKNOWN"
            ),

            "cycle_position": analysis.get(
                "cycle_position",
                "UNKNOWN"
            ),

            "trend": analysis.get(
                "trend_state",
                "UNKNOWN"
            ),

            "trend_strength": analysis.get(
                "trend_strength",
                0
            ),

            "breadth": analysis.get(
                "breadth_score",
                0
            ),

            "volatility": analysis.get(
                "volatility_score",
                0
            ),

            "liquidity": analysis.get(
                "liquidity_score",
                0
            ),

            "distribution_days": analysis.get(
                "distribution_days",
                0
            ),

            "follow_through_day": analysis.get(
                "follow_through_day",
                False
            ),

            "risk_level": analysis.get(
                "risk_level",
                "UNKNOWN"
            ),

            "confidence": analysis.get(
                "confidence",
                0
            ),

            "warnings": analysis.get(
                "institutional_warnings",
                []
            )

        }


    def get_canslim_market_report(
        self,
        analysis
    ):
        """
        CANSLIM M component accessor.
        """

        return self.get_market_report(
            analysis
        )


    def get_institutional_snapshot(
        self,
        analysis
    ):
        """
        Condensed institutional state.
        """

        if not isinstance(
            analysis,
            dict
        ):
            return {}


        return {

            "timestamp": analysis.get(
                "timestamp",
                datetime.utcnow().isoformat()
            ),

            "market_score": analysis.get(
                "market_score",
                0
            ),

            "condition": analysis.get(
                "market_condition",
                "UNKNOWN"
            ),

            "cycle": analysis.get(
                "cycle_position",
                "UNKNOWN"
            ),

            "trend": analysis.get(
                "trend_state",
                "UNKNOWN"
            ),

            "risk": analysis.get(
                "risk_level",
                "UNKNOWN"
            ),

            "confidence": analysis.get(
                "confidence",
                0
            ),

            "warnings": analysis.get(
                "institutional_warnings",
                []
            )

        }


    def export_features(
        self,
        analysis
    ):
        """
        ML feature export.
        """

        if not isinstance(
            analysis,
            dict
        ):
            return {}


        return self._build_ml_features(
            analysis
        )


    def compare_market_conditions(
        self,
        current,
        previous
    ):
        """
        Compare institutional states.
        """

        if (
            not isinstance(
                current,
                dict
            )
            or not isinstance(
                previous,
                dict
            )
        ):
            return {}


        current_score = self._safe_float(
            current.get(
                "market_score",
                0
            )
        )

        previous_score = self._safe_float(
            previous.get(
                "market_score",
                0
            )
        )


        return {

            "score_change": round(
                current_score -
                previous_score,
                2
            ),

            "improving":
                current_score >
                previous_score,

            "deteriorating":
                current_score <
                previous_score,

            "condition_changed":
                current.get(
                    "market_condition"
                )
                !=
                previous.get(
                    "market_condition"
                ),

            "cycle_changed":
                current.get(
                    "cycle_position"
                )
                !=
                previous.get(
                    "cycle_position"
                )

        }


    def save_analysis_state(
        self,
        analysis
    ):
        """
        Persistent state payload.
        Database writes handled by
        MarketStateStore.
        """

        if not isinstance(
            analysis,
            dict
        ):
            return {}


        return {

            "timestamp": analysis.get(
                "timestamp",
                datetime.utcnow().isoformat()
            ),

            "market_score": analysis.get(
                "market_score",
                0
            ),

            "market_condition": analysis.get(
                "market_condition",
                "UNKNOWN"
            ),

            "cycle_position": analysis.get(
                "cycle_position",
                "UNKNOWN"
            ),

            "trend_state": analysis.get(
                "trend_state",
                "UNKNOWN"
            ),

            "breadth_score": analysis.get(
                "breadth_score",
                0
            ),

            "volatility_score": analysis.get(
                "volatility_score",
                0
            ),

            "liquidity_score": analysis.get(
                "liquidity_score",
                0
            ),

            "confidence": analysis.get(
                "confidence",
                0
            )

        }        