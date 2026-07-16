import math
import logging

try:
    import yfinance as yf
except Exception:
    yf = None


logger = logging.getLogger("MarketData")


def get_snapshot(ticker):

    if yf is None:
        return None

    try:

        ticker = str(ticker).upper().strip()

        t = yf.Ticker(
            ticker
        )

        hist = t.history(
            period="5d",
            interval="1d"
        )


        if hist is None or hist.empty:
            return None


        closes = hist["Close"].dropna()


        if closes.empty:
            return None


        last = float(
            closes.iloc[-1]
        )


        if math.isnan(last):
            return None


        return {
            "price": round(
                last,
                2
            )
        }


    except Exception as e:

        logger.exception(
            f"Market snapshot failed {ticker}: {e}"
        )

        return None