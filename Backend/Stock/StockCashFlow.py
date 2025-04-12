import numpy as np
import pandas as pd
import yfinance as yf
from .StockCRUD import CalculateCAGR
from Database.models import *


def CalculateFCFF(Ticker, db):
    ticker_data = yf.Ticker(f"{Ticker}.NS")
    cashflow = ticker_data.cashflow
    financials = ticker_data.financials

    try:
        OFC = cashflow.loc["Operating Cash Flow"].values
        Interest = cashflow.loc["Interest Paid Cff"].values
        Capex = cashflow.loc["Capital Expenditure"].values
        tax_rate = financials.loc["Tax Rate For Calcs"].values
    except KeyError as e:
        print(f"Missing data: {e}")
        return None

    # Compute FCFF
    FCFF = OFC + Interest * (1 - tax_rate) - Capex

    # Ensure FCFF is stored as a string (for JSON compatibility)
    FCFF_result = FCFF.tolist()  # Convert NumPy array to list
    FCFF_result_str = ", ".join(map(str, FCFF_result))  # Join as a string

    # Save to the database
    stock = db.query(Stock).filter(Stock.Ticker == Ticker).first()
    stock.metrics.FCFF = FCFF_result_str 

    db.commit()

    return FCFF_result 
