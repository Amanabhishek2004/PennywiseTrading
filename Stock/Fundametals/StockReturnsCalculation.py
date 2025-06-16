import yfinance as yf 
import pandas as pd 
import numpy as np 
from datetime import datetime , timedelta



def CalculateReturns(stock):
    """
    Calculates the returns of the stock in 6m, 1m, 9m, 12m.
    Returns a dictionary with these values.
    """
    from datetime import datetime, timedelta
    import yfinance as yf
    import pandas as pd
    print(stock)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    stock = yf.Ticker(f"{stock}.NS").history(
        end=end_date,
        start=start_date
    )
    
    # Normalize index to dates
    stock.index = stock.index # Converts to just the date part
    print(stock.index)
    monthly_stock_data = stock.resample("M").last()
    lags = [1, 3, 6, 9, 12]

    returns = {}

    for lag in lags:
        returns[f"{lag}m"] = monthly_stock_data["Close"].pct_change(lag).mean()

    return returns 
            

def CalculatePortfolioReturns(stocksarray):
    returns_1m = []
    returns_3m = []
    returns_6m = []
    returns_9m = []
    returns_12m = []

    for stock in stocksarray:
        returns_data = CalculateReturns(stock)
        returns_1m.append(returns_data["1m"])
        returns_3m.append(returns_data["3m"])
        returns_6m.append(returns_data["6m"])
        returns_9m.append(returns_data["9m"])
        returns_12m.append(returns_data["12m"])

    # Create DataFrame
    dataframe = pd.DataFrame({
        "Stock": stocksarray,
        "1m Returns": returns_1m,
        "3m Returns": returns_3m,
        "6m Returns": returns_6m,
        "9m Returns": returns_9m,
        "12m Returns": returns_12m
    })

    if dataframe.empty:
        raise ValueError("Generated dataframe is empty. Ensure valid stock data is provided.")

    # Debug: Print the dataframe
    print("DataFrame:\n", dataframe)

    # Create Pivot Table
    pivot_table = dataframe.pivot_table(
        index="Stock",
        values=["1m Returns", "3m Returns", "6m Returns", "9m Returns", "12m Returns"],
        aggfunc="mean"
    )

    # Debug: Print the pivot table
    print("Pivot Table:\n", pivot_table)

    # Calculate Correlation
    correlation_between_stocks = pivot_table.T.corr()

    # Debug: Print the correlation matrix
    print("Correlation Matrix:\n", correlation_between_stocks)

    # Convert DataFrames to NumPy arrays
    pivot_table_array = pivot_table.to_numpy().tolist()
    correlation_matrix_array = correlation_between_stocks.to_numpy().tolist()

    return {
        "pivot_table": pivot_table_array,
        "correlation_matrix": correlation_matrix_array
    }

