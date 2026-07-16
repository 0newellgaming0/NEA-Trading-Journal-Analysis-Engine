"""
====================================================================
NEA28 MARKET VOLATILITY ENGINE

Module:
    modules/market/volatility_engine.py

Purpose:
    Institutional market volatility analysis.

Responsibilities:
    - Calculate volatility regime
    - Measure ATR expansion
    - Measure realized volatility
    - Detect volatility compression
    - Detect volatility expansion
    - Produce standardized volatility output

Calculations:
    VIX Regime
    ATR Expansion
    Realized Volatility
    Volatility Compression
    Volatility Expansion
    Market Risk Level

Output:
{
    "vix":16,
    "volatility_regime":"LOW_VOLATILITY",
    "realized_volatility":14,
    "risk_level":"LOW",
    "volatility_score":86
}
====================================================================
"""

import logging
import math
from datetime import datetime

import pandas as pd


logger = logging.getLogger("MarketVolatilityEngine")


class MarketVolatilityEngine:
    """
    Institutional volatility analysis engine.
    """

    def __init__(self):
        logger.info(
            "Market Volatility Engine initialized"
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

    def _calculate_true_range(
        self,
        data
    ):
        high = data["High"]
        low = data["Low"]
        close = data["Close"]

        previous_close = close.shift(1)

        ranges = pd.concat(
            [
                high - low,
                abs(high - previous_close),
                abs(low - previous_close)
            ],
            axis=1
        )

        return ranges.max(
            axis=1
        )

    def _calculate_atr(
        self,
        data,
        period=14
    ):
        true_range = self._calculate_true_range(
            data
        )

        return round(
            true_range.rolling(
                period
            ).mean().iloc[-1],
            2
        )

    def _calculate_realized_volatility(
        self,
        data,
        period=20
    ):
        returns = (
            data["Close"]
            .pct_change()
        )

        volatility = (
            returns
            .rolling(
                period
            )
            .std()
            *
            math.sqrt(
                252
            )
            *
            100
        )

        return round(
            volatility.iloc[-1],
            2
        )

    def _calculate_atr_expansion(
        self,
        data
    ):
        atr = self._calculate_atr(
            data
        )

        previous_atr = (
            self._calculate_true_range(
                data
            )
            .rolling(
                14
            )
            .mean()
            .iloc[-2]
        )

        if previous_atr <= 0:
            return 0

        return round(
            (
                (
                    atr -
                    previous_atr
                )
                /
                previous_atr
            )
            *
            100,
            2
        )

    def _detect_regime(
        self,
        vix,
        realized_volatility
    ):
        if (
            vix >= 30
            or realized_volatility >= 30
        ):
            return "HIGH_VOLATILITY"

        if (
            vix >= 20
            or realized_volatility >= 20
        ):
            return "ELEVATED_VOLATILITY"

        if (
            vix <= 15
            and realized_volatility <= 15
        ):
            return "LOW_VOLATILITY"

        return "NORMAL_VOLATILITY"

    def _calculate_compression(
        self,
        data
    ):
        volatility = (
            data["Close"]
            .pct_change()
            .rolling(
                20
            )
            .std()
        )

        current = volatility.iloc[-1]

        average = (
            volatility
            .mean()
        )

        if average <= 0:
            return 0

        compression = (
            1 -
            (
                current /
                average
            )
        ) * 100

        return round(
            max(
                compression,
                0
            ),
            2
        )

    def _calculate_expansion(
        self,
        atr_expansion
    ):
        return round(
            max(
                atr_expansion,
                0
            ),
            2
        )

    def _calculate_score(
        self,
        vix,
        realized_volatility,
        compression,
        expansion
    ):
        score = 100

        if vix >= 35:
            score -= 40

        elif vix >= 25:
            score -= 25

        if realized_volatility >= 30:
            score -= 30

        elif realized_volatility >= 20:
            score -= 15

        if expansion >= 20:
            score -= 10

        if compression >= 20:
            score += 5

        return max(
            min(
                score,
                100
            ),
            0
        )

    def _risk_level(
        self,
        score
    ):
        if score >= 75:
            return "LOW"

        if score >= 50:
            return "MODERATE"

        if score >= 25:
            return "HIGH"

        return "EXTREME"

    def run(
        self,
        volatility_data
    ):
        """
        Execute volatility analysis.

        Input:

        {
            "ohlcv":DataFrame,
            "vix":16
        }

        Output:

        {
            "vix":16,
            "volatility_regime":"",
            "realized_volatility":0,
            "risk_level":"",
            "volatility_score":0
        }
        """

        logger.info(
            "Running Market Volatility Analysis"
        )

        if not isinstance(
            volatility_data,
            dict
        ):
            return {}

        ohlcv = volatility_data.get(
            "ohlcv"
        )

        if not isinstance(
            ohlcv,
            pd.DataFrame
        ):
            return {}

        vix = self._safe_float(
            volatility_data.get(
                "vix",
                0
            )
        )

        realized_volatility = self._calculate_realized_volatility(
            ohlcv
        )

        atr_expansion = self._calculate_atr_expansion(
            ohlcv
        )

        compression = self._calculate_compression(
            ohlcv
        )

        expansion = self._calculate_expansion(
            atr_expansion
        )

        regime = self._detect_regime(
            vix,
            realized_volatility
        )

        score = self._calculate_score(
            vix,
            realized_volatility,
            compression,
            expansion
        )

        return {
            "vix": vix,
            "volatility_regime": regime,
            "realized_volatility": realized_volatility,
            "atr_expansion": atr_expansion,
            "volatility_compression": compression,
            "volatility_expansion": expansion,
            "risk_level": self._risk_level(
                score
            ),
            "volatility_score": score,
            "timestamp": datetime.utcnow().isoformat()
        }