import yfinance as yf
import pandas as pd
import numpy as np
from uuid import uuid4
from .StockDIctScehma import *
from .StockMetricCalculation import *
from sqlalchemy.orm import Session
import traceback
import sys


def CalculateCAGR(array):
    array = np.array(array, dtype=np.float64)

    # Remove NaNs
    array = array[~np.isnan(array)]

    if len(array) == 0:
        return -1.0  # Or return np.nan to indicate invalid calculation
    if len(array) == 1:
        return 0.0
    
    start = array[-1]
    end = array[0]

    if (start > 0 and end > 0) or (start < 0 and end < 0):
        return ((end / start) ** (1 / len(array))) - 1

    if start < 0:
        return 0.0
    if end < 0:
        return 1.0
    return -1.0



def CretaeRawStockInstance(Ticker):
    try:
        companies_stock_data = yf.Ticker(f"{Ticker}.NS")
        print("Ticker: ", companies_stock_data.info)
        info_data = companies_stock_data.get_info()
        cashflow_data = companies_stock_data.cashflow
        balancesheet_data = companies_stock_data.balancesheet
        financials_data = companies_stock_data.financials

        if (
            not info_data or 
            'regularMarketPrice' not in info_data or 
            info_data['regularMarketPrice'] is None or
            cashflow_data.empty or 
            balancesheet_data.empty or 
            financials_data.empty
        ):
            return {
                "error": f"No sufficient data found for '{Ticker}'"
            }

        companyswholedata_rowwise["tickers"] = Ticker

        for infos in companysinfo:
            companyswholedata_rowwise[infos] = info_data.get(infos, None)

        for infos in companyscashflow:
            if infos in cashflow_data.index:
                companyswholedata_rowwise[infos] = cashflow_data.loc[infos].values.tolist()

        for infos in companysbalancesheet:
            if infos in balancesheet_data.index:
                companyswholedata_rowwise[infos] = balancesheet_data.loc[infos].values.tolist()

        for infos in companysfinancialsinfo:
            if infos in financials_data.index:
                companyswholedata_rowwise[infos] = financials_data.loc[infos].values.tolist()

        print(companyswholedata_rowwise)        

        x = companyswholedata_rowwise.get("Net Income From Continuing Operations", [])
        companyswholedata_rowwise["Net Income From Continuing Operations delta"] = (
            -np.diff(x)[0] if isinstance(x, (list, np.ndarray)) and len(x) > 1 else np.nan
        )

        companyswholedata_rowwise["ATR"] = CalculateATR(
            companyswholedata_rowwise.get("Total Assets"),
            companyswholedata_rowwise.get("Operating Revenue")
        )

        companyswholedata_rowwise["ROE"] = CalculateROE(
            companyswholedata_rowwise.get("Stockholders Equity"),
            companyswholedata_rowwise.get("Net Income From Continuing Operations")
        )

        row = np.array(companyswholedata_rowwise.get("Net Income", []))
        payout_ratio = companyswholedata_rowwise.get("payoutRatio", np.nan)
        companyswholedata_rowwise["reinvestedearnings"] = (
            np.nanmedian((1 - payout_ratio) * row) if not np.isnan(payout_ratio) else np.nan
        )

        companyswholedata_rowwise["RORE"] = CalculateRORE(
            companyswholedata_rowwise.get("Net Income From Continuing Operations"),
            companyswholedata_rowwise.get("reinvestedearnings")
        )

        companyswholedata_rowwise["ROIC"] = CalculateROIC(
            companyswholedata_rowwise.get("Invested Capital"),
            companyswholedata_rowwise.get("Net Income From Continuing Operations")
        )

        companyswholedata_rowwise["COE"] = CalculateCOE(
    companyswholedata_rowwise.get("beta") if companyswholedata_rowwise.get("beta") is not None else 1.0
)


        companyswholedata_rowwise["COD"] = CalculateCOI(
            companyswholedata_rowwise.get("Interest Expense"),
            companyswholedata_rowwise.get("Current Debt")
        )

        companyswholedata_rowwise["WACC"] = WACCcalculator(companyswholedata_rowwise)

        companyswholedata_rowwise["FCFF"] = CalculateFCFF(
            companyswholedata_rowwise.get("Operating Cash Flow"),
            companyswholedata_rowwise.get("Interest Expense"),
            companyswholedata_rowwise.get("Tax Rate For Calcs"),
            companyswholedata_rowwise.get("Capital Expenditure")
        )

        companyswholedata_rowwise["ICR"] = CalculateICR(
            companyswholedata_rowwise.get("EBIT"),
            companyswholedata_rowwise.get("Interest Expense")
        )

        companyswholedata_rowwise["EFF"] = (
            companyswholedata_rowwise["RORE"] / companyswholedata_rowwise["WACC"]
            if companyswholedata_rowwise["WACC"] != 0 else np.nan
        )

        for column in CAGR_COLUMNS:
            companyswholedata_rowwise[f"{column}_cagr"] = CalculateCAGR(
                companyswholedata_rowwise.get(column)
            )

        # Replace None or NaN with 0
        for key, value in companyswholedata_rowwise.items():
            if value is None or (isinstance(value, float) and np.isnan(value)):
                companyswholedata_rowwise[key] = 0

        return companyswholedata_rowwise

    except Exception as e:
        # Capture traceback info
        tb = traceback.extract_tb(sys.exc_info()[2])
        last_call = tb[-1]  # Get last line where error occurred
        error_location = f"{last_call.filename}, line {last_call.lineno}, in {last_call.name}"
        error_line = last_call.line.strip()

        return {
            "error": f"Data Not Found for stock {Ticker}: {str(e)}",
            "location": error_location,
            "code": error_line
        }