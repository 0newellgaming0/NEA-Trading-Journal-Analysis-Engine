import os
import pandas as pd
import logging

from modules.path_resolver import get_stock_data_path
from modules.eventEngine import EventStore
from modules.candlestick_state_engine import (
    CandlestickInstitutionalStateEngine
)

logger = logging.getLogger("candlestick_batch")


GLOBAL_EVENT_STORE = EventStore()


def load_daily_dataframe(ticker):

    path = get_stock_data_path(
        ticker,
        "daily"
    )

    if not os.path.exists(path):
        logger.warning(
            f"[CANDLE] Missing daily data {ticker}"
        )
        return None


    df = pd.read_csv(path)

    if df.empty:
        return None


    # Yahoo fetcher format normalization
    rename_map = {
        f"open_{ticker.lower()}": "Open",
        f"high_{ticker.lower()}": "High",
        f"low_{ticker.lower()}": "Low",
        f"close_{ticker.lower()}": "Close",
        f"volume_{ticker.lower()}": "Volume",
    }


    df = df.rename(
        columns=rename_map
    )


    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]


    missing = [
        c for c in required
        if c not in df.columns
    ]


    if missing:
        logger.error(
            f"[CANDLE] {ticker} missing {missing}"
        )
        return None


    return df



def run_candlestick_analysis(ticker):

    ticker = ticker.upper()

    logger.info(
        f"[CANDLE] Starting {ticker}"
    )


    df = load_daily_dataframe(
        ticker
    )


    if df is None:
        return None


    engine = CandlestickInstitutionalStateEngine(
        ticker,
        GLOBAL_EVENT_STORE
    )


    result = engine.run(
        df
    )


    logger.info(
        f"[CANDLE] Complete {ticker} rows={len(result)}"
    )


    return result



def run_all_candlestick_analysis(tickers):

    results = {}


    for ticker in tickers:

        try:

            results[ticker] = run_candlestick_analysis(
                ticker
            )

        except Exception as e:

            logger.exception(
                f"[CANDLE] Failed {ticker}: {e}"
            )


    return results