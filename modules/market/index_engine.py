"""
====================================================================
NEA28 MARKET INDEX ENGINE

Module:
    modules/market/index_engine.py

Purpose:
    Institutional index technical state analysis.

Responsibilities:
    - Analyze major market indexes
    - Calculate trend structure
    - Measure institutional index strength
    - Detect breakouts / breakdowns
    - Provide standardized output for MarketDirectionEngine

Indexes Supported:
    SP500
    NASDAQ
    RUSSELL2000
    NYSE
    DOW

Calculations:
    EMA20
    EMA50
    EMA200
    SMA50
    SMA200
    ATR
    Momentum
    Relative Strength
    Higher Highs
    Higher Lows
    Breakouts
    Breakdowns
    Trend Persistence

Output Contract:

{
    "SP500":
    {
        "trend": "STRONG_UPTREND",
        "ema_alignment": True,
        "sma_alignment": True,
        "trend_strength": 88,
        "higher_highs": True,
        "higher_lows": True,
        "breakout": True,
        "breakdown": False,
        "relative_strength": 92,
        "momentum": 85,
        "atr": 4.2,
        "trend_persistence": 91
    }
}

====================================================================
"""


import logging
from datetime import datetime

import pandas as pd


logger = logging.getLogger("MarketIndexEngine")


class MarketIndexEngine:
    """
    Institutional market index analysis engine.
    """


    INDEXES = (
        "SP500",
        "NASDAQ",
        "RUSSELL2000",
        "NYSE",
        "DOW"
    )


    def __init__(self):

        logger.info(
            "Market Index Engine initialized"
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



    def _calculate_ema(
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



    def _calculate_sma(
        self,
        series,
        period
    ):

        return (
            series
            .rolling(
                period
            )
            .mean()
        )



    def _calculate_atr(
        self,
        dataframe,
        period=14
    ):

        high = dataframe["High"]

        low = dataframe["Low"]

        close = dataframe["Close"]


        tr = pd.concat(
            [
                high - low,

                (high - close.shift())
                .abs(),

                (low - close.shift())
                .abs()
            ],
            axis=1
        ).max(
            axis=1
        )


        atr = (
            tr
            .rolling(
                period
            )
            .mean()
        )


        return atr.iloc[-1]



    def _calculate_momentum(
        self,
        close,
        period=20
    ):

        if len(close) <= period:

            return 0


        return (
            (
                close.iloc[-1]
                /
                close.iloc[-period]
            )
            - 1
        ) * 100



    def _detect_higher_highs(
        self,
        close,
        lookback=20
    ):

        if len(close) < lookback * 2:

            return False


        recent = close.tail(
            lookback
        )

        previous = close.iloc[
            -lookback * 2:
            -lookback
        ]


        return (
            recent.max()
            >
            previous.max()
        )



    def _detect_higher_lows(
        self,
        close,
        lookback=20
    ):

        if len(close) < lookback * 2:

            return False


        recent = close.tail(
            lookback
        )

        previous = close.iloc[
            -lookback * 2:
            -lookback
        ]


        return (
            recent.min()
            >
            previous.min()
        )



    def _detect_breakout(
        self,
        close,
        period=50
    ):

        if len(close) < period:

            return False


        current = close.iloc[-1]

        resistance = (
            close
            .iloc[-period:-1]
            .max()
        )


        return current > resistance



    def _detect_breakdown(
        self,
        close,
        period=50
    ):

        if len(close) < period:

            return False


        current = close.iloc[-1]

        support = (
            close
            .iloc[-period:-1]
            .min()
        )


        return current < support



    def _calculate_relative_strength(
        self,
        close,
        benchmark=None
    ):

        if benchmark is None:

            return 50


        if len(close) < 50:

            return 50


        asset_return = (
            close.iloc[-1]
            /
            close.iloc[-50]
            -
            1
        )


        benchmark_return = (
            benchmark.iloc[-1]
            /
            benchmark.iloc[-50]
            -
            1
        )


        relative = (
            asset_return
            -
            benchmark_return
        )


        score = (
            50
            +
            (
                relative * 500
            )
        )


        return round(
            max(
                min(
                    score,
                    100
                ),
                0
            ),
            2
        )



    def _calculate_trend_strength(
        self,
        ema_alignment,
        sma_alignment,
        higher_highs,
        higher_lows,
        momentum
    ):

        score = 0


        if ema_alignment:

            score += 25


        if sma_alignment:

            score += 25


        if higher_highs:

            score += 20


        if higher_lows:

            score += 20


        if momentum > 0:

            score += 10


        return min(
            score,
            100
        )



    def _calculate_trend(
        self,
        strength
    ):

        if strength >= 85:

            return "STRONG_UPTREND"


        if strength >= 65:

            return "UPTREND"


        if strength >= 45:

            return "SIDEWAYS"


        if strength >= 25:

            return "WEAK"


        return "DOWNTREND"



    def _calculate_persistence(
        self,
        close,
        period=50
    ):

        if len(close) < period:

            return 0


        changes = (
            close
            .pct_change()
            .tail(period)
        )


        positive = (
            changes > 0
        ).sum()


        return round(
            (
                positive
                /
                period
            )
            *
            100,
            2
        )



    def analyze_index(
        self,
        ticker,
        dataframe,
        benchmark=None
    ):

        if not isinstance(
            dataframe,
            pd.DataFrame
        ):

            return {}


        if dataframe.empty:

            return {}


        close = dataframe["Close"]


        ema20 = self._calculate_ema(
            close,
            20
        )

        ema50 = self._calculate_ema(
            close,
            50
        )

        ema200 = self._calculate_ema(
            close,
            200
        )


        sma50 = self._calculate_sma(
            close,
            50
        )

        sma200 = self._calculate_sma(
            close,
            200
        )


        ema_alignment = (

            close.iloc[-1]
            >
            ema20.iloc[-1]
            >
            ema50.iloc[-1]
            >
            ema200.iloc[-1]

        )


        sma_alignment = (

            close.iloc[-1]
            >
            sma50.iloc[-1]
            >
            sma200.iloc[-1]

        )


        higher_highs = self._detect_higher_highs(
            close
        )


        higher_lows = self._detect_higher_lows(
            close
        )


        breakout = self._detect_breakout(
            close
        )


        breakdown = self._detect_breakdown(
            close
        )


        momentum = self._calculate_momentum(
            close
        )


        trend_strength = self._calculate_trend_strength(
            ema_alignment,
            sma_alignment,
            higher_highs,
            higher_lows,
            momentum
        )


        return {

            "ticker": ticker,

            "trend": self._calculate_trend(
                trend_strength
            ),

            "ema_alignment": ema_alignment,

            "sma_alignment": sma_alignment,

            "trend_strength": trend_strength,

            "higher_highs": higher_highs,

            "higher_lows": higher_lows,

            "breakout": breakout,

            "breakdown": breakdown,

            "relative_strength": self._calculate_relative_strength(
                close,
                benchmark
            ),

            "momentum": round(
                momentum,
                2
            ),

            "atr": self._safe_float(
                self._calculate_atr(
                    dataframe
                )
            ),

            "trend_persistence": self._calculate_persistence(
                close
            ),

            "timestamp": datetime.utcnow().isoformat()

        }



    def run(
        self,
        market_data
    ):

        """
        Execute complete index analysis.

        Input:

        {
            "SP500": dataframe,
            "NASDAQ": dataframe,
            ...
        }

        Output:

        {
            "SP500": {...},
            ...
        }
        """


        logger.info(
            "Running Market Index Analysis"
        )


        results = {}


        benchmark = market_data.get(
            "SP500"
        )


        benchmark_close = None


        if isinstance(
            benchmark,
            pd.DataFrame
        ):

            benchmark_close = benchmark["Close"]



        for index in self.INDEXES:

            dataframe = market_data.get(
                index
            )


            if dataframe is None:

                continue


            results[index] = self.analyze_index(
                index,
                dataframe,
                benchmark_close
            )


        return results