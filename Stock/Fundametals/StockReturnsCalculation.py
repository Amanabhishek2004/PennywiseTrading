import yfinance as yf 
import pandas as pd 
import numpy as np 
from datetime import datetime , timedelta



def CalculateReturns(ticker):
    returns = {
        "1m": None,
        "3m": None,
        "6m": None,
        "12m": None
    }
    data = yf.download(tickers=[f"{ticker}.NS"], group_by="ticker", period="10y", interval="1d")
    if data.empty:
        raise ValueError(f"No data found for ticker: {ticker}")

    # Use 'Close' directly if single ticker
    close = data["Close"] if "Close" in data else data[f"{ticker}.NS"]["Close"]

    returns["1m"] = close.pct_change(1).shift(1).dropna().cumsum().resample("M").last().mean()
    returns["3m"] = close.pct_change(3).shift(1).dropna().cumsum().resample("M").last().mean()
    returns["6m"] = close.pct_change(6).shift(1).dropna().cumsum().resample("M").last().mean()
    returns["12m"] = close.pct_change(12).shift(1).dropna().cumsum().resample("M").last().mean()
    return returns

def CalculatePortfolioReturns(stocksarray):
    returns_1m = []
    returns_3m = []
    returns_6m = []
    returns_12m = []

    for stock in stocksarray:
        returns_data = CalculateReturns(stock)
        returns_1m.append(returns_data["1m"])
        returns_3m.append(returns_data["3m"])
        returns_6m.append(returns_data["6m"])
        returns_12m.append(returns_data["12m"])

    # Create DataFrame
    dataframe = pd.DataFrame({
        "Stock": stocksarray,
        "1m Returns": returns_1m,
        "3m Returns": returns_3m,
        "6m Returns": returns_6m,
        "12m Returns": returns_12m
    })
    
    if dataframe.empty:
        raise ValueError("Generated dataframe is empty. Ensure valid stock data is provided.")

    print("DataFrame:\n", dataframe)

    correlation_between_stocks = dataframe[[ "1m Returns" , "3m Returns" , "6m Returns", "12m Returns" ]].corr()

    print("Correlation Matrix:\n", correlation_between_stocks)

    correlation_matrix_array = correlation_between_stocks.to_numpy().tolist()

    return {
        "correlation_matrix": correlation_matrix_array , 
        "returns_dataframe": dataframe.to_dict(orient="records")    
    }
