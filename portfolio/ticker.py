import functools
import yfinance as yf
from datetime import datetime

# --------------------------------------------------------
# collection of cached functions to reduce traffic with yf
# -------------------------------
@functools.cache
def _get_rates(rates_symbols, start:datetime, end:datetime):
    """
    Get currency exchange rates

    Attributes
    ----------
        rates_symbols: str
            string in the form "USDEUR=X, EURUSD=X"
        start: datetime
            start date of the search 
        end: datetime
            end date of the search 
        
    Return
    ------
        Pandas dataframe with currency exchange rates
    """
    tickers = yf.Tickers(rates_symbols)
    _rates = []
    for i in tickers.tickers: 
        _rates.append(tickers.tickers[i].history(start=start, end=end, period="1d").Close)
    return _rates

@functools.cache
def _get_history_ticker(symbol, start:datetime, end:datetime):
    """
    tbd
    """
    ticker = _get_ticker(symbol)
    ticker_df = ticker.history(start=start, end=end)
    return ticker_df, ticker.info["currency"]

@functools.cache
def _get_ticker_info(symbol):
    """
    tbd
    """
    ticker = _get_ticker(symbol)
    return ticker.info

@functools.cache
def _get_ticker(symbol):
    """
    tbd
    """
    ticker = yf.Ticker(symbol)
    return ticker
    