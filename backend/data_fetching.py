# backend/data_fetching.py
import requests
import yfinance as yf
import pandas as pd
import streamlit as st

def fetch_quotes(symbols, api_key):
    url = "https://api.12data.com/quote"
    params = {
        "symbol": ",".join(symbols),
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    # Parse and return in your app's expected format
    return data

@st.cache_data(show_spinner=False)
def get_company_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get('shortName', ticker)
    except Exception:
        return ticker

@st.cache_data(show_spinner=False)
def get_top_stocks_quotes():
    """
    Fetches the latest quote data for 30 well-known stocks using Yahoo Finance (yfinance),
    including company name, change, and percent change. Uses caching for efficiency.
    Returns a DataFrame with columns: ticker, name, last_price, day_high, day_low, open, volume, change, change_pct.
    """
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "BRK-B", "JPM",
        "V", "UNH", "HD", "MA", "PG", "DIS", "KO", "PEP", "BAC", "XOM",
        "PFE", "CSCO", "T", "VZ", "WMT", "INTC", "CVX", "MCD", "NKE", "ADBE", "SAP", "BNTX"
    ]
    data = yf.download(tickers, period="1d", interval="1d", group_by='ticker', auto_adjust=True, threads=True)
    quotes = []
    for ticker in tickers:
        try:
            last_close = data[ticker]['Close'][-1]
            high = data[ticker]['High'][-1]
            low = data[ticker]['Low'][-1]
            open_ = data[ticker]['Open'][-1]
            volume = data[ticker]['Volume'][-1]
            name = get_company_name(ticker)
            info = yf.Ticker(ticker).info
            currency = info.get('currency', None)
            bid = info.get('bid', None)
            ask = info.get('ask', None)
            year_high = info.get('fiftyTwoWeekHigh', None)
            year_low = info.get('fiftyTwoWeekLow', None)
            market_cap = info.get('marketCap', None)
            change = last_close - open_ if open_ is not None else None
            change_pct = (change / open_ * 100) if (open_ not in [None, 0]) else None
            quotes.append({
                'ticker': ticker,
                'name': name,
                'last_price': last_close,
                'day_high': high,
                'day_low': low,
                'open': open_,
                'volume': volume,
                'change': change,
                'change_pct': change_pct,
                'currency': currency,
                'bid': bid,
                'ask': ask,
                'year_high': year_high,
                'year_low': year_low,
                'market_cap': market_cap
            })
        except Exception:
            quotes.append({
                'ticker': ticker,
                'name': ticker,
                'last_price': None,
                'day_high': None,
                'day_low': None,
                'open': None,
                'volume': None,
                'change': None,
                'change_pct': None,
                'currency': None,
                'bid': None,
                'ask': None,
                'year_high': None,
                'year_low': None,
                'market_cap': None
            })
    return pd.DataFrame(quotes)