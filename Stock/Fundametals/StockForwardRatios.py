from Database.models import *
import numpy as np 
import pandas as pd 
import yfinance as yf 
from datetime import datetime , timedelta


def parse_data(data_string):

    if data_string is None:
        return []

    if isinstance(data_string, (int, float)):
        return [float(data_string)]

    elif isinstance(data_string, str):
        cleaned_data = data_string.strip().replace("[", "").replace("]", "").replace("'", "").replace("%", "")
        elements = cleaned_data.split(",")
        result = []

        for element in elements:
            element = element.strip()
            if element == "":
                element = "0"
            try:
                number = float(element.replace(",", ""))
                result.append(number)
            except ValueError:
                result.append(element)
        return result

    else:
        return []


def calculate_forward_pe(ticker, db, tax_rate=0.3):


    # Fetch stock data
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        raise ValueError(f"Stock with ticker '{ticker}' not found.")
    
    # Parse data
    interest_expenses = parse_data(stock.expenses[0].Intrest_Expense)
    depriciation = parse_data(stock.financials[0].DepreciationAmortization)
    operating_expenses = parse_data(stock.expenses[0].Operating_Expense)
    sales = parse_data(stock.earning_metrics[0].OperatingRevenue)

    if not (interest_expenses and operating_expenses and sales):
        raise ValueError("Parsed data is empty or invalid.")

    # Calculate recent values and growth rates
    recent_interest = interest_expenses[-1]
    recent_depriciation = depriciation[-1]
    recent_operating_expense = operating_expenses[-1]
    recent_sales = sales[-1]
    
    interest_growth = np.nanmean(np.diff(interest_expenses) / np.array(interest_expenses[1:]))
    operating_expense_growth = np.nanmean(np.diff(operating_expenses) / np.array(operating_expenses[1:]))
    sales_growth = np.nanmedian(np.diff(sales) / np.array(sales[1:]))
    depriciationgrowthrate = np.nanmedian(np.diff(depriciation) /np.array(depriciation[1:]))
    print(operating_expenses)
    
    # Project forward values
    forward_interest_expense = recent_interest * (1 + interest_growth) * (1 - tax_rate)
    forward_depriciation = recent_depriciation * (1+depriciationgrowthrate)
    forward_operating_expense = recent_operating_expense * (1 + operating_expense_growth)
    forward_sales = recent_sales * (1 + sales_growth)
    
    print(f"Forward Sales: {forward_sales}, Forward Interest Expense: {forward_interest_expense}, Forward Operating Expense: {forward_operating_expense} , Depricitaion :  {forward_depriciation}")
    # Calculate net earnings and forward EPS
    outstanding_shares = stock.sharesOutstanding
    print(f"Outstanding Shares: {outstanding_shares}")
    net_earnings = (forward_sales - forward_interest_expense - forward_operating_expense - forward_depriciation) * (1 - tax_rate)
    forward_eps = net_earnings * 1e7 / outstanding_shares
    
    # Calculate forward PE ratio
    print(stock.CurrentPrice)
    forward_pe = stock.CurrentPrice / forward_eps
    
    # Debug information
    
    return { "FPE" :  forward_pe ,
             "SalesGrowth" : sales_growth  , 
             "OperatingExpense" : operating_expense_growth , 
             "InterestExpenseGrowth" : interest_growth}

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

def CalculateMedianpe(ticker, db: Session):
    # Fetch stock and EPS
    stock_data = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock_data or not stock_data.earning_metrics:
        print("error")
        return {"error": "Stock or earning metrics not found."}

    epsarray = parse_data(stock_data.earning_metrics[0].epsTrailingTwelveMonths)
    epsgrowth = stock_data.earning_metrics[0].epsForward
    peg = (stock_data.CurrentPrice / epsarray[-1]) if epsarray[-1] != 0 else 0

    # Get all price data in chronological order
    price_data = (
        db.query(PriceData)
        .filter(PriceData.stock_id == stock_data.id, PriceData.period == "1d")
        .order_by(PriceData.date.asc())
        .all()
    )

    # Get unique years from price data, sorted descending
    unique_years = sorted({pd.Timestamp(p.date).year for p in price_data})[::-1]

    all_pe_ratios = []
    for i, year in enumerate(unique_years):
        if i >= len(epsarray) or epsarray[i] == 0:
            continue  # skip if no EPS data for this year

        # Get all daily prices for the year
        prices_for_year = [p for p in price_data if pd.Timestamp(p.date).year == year]
        if not prices_for_year:
            continue

        # Compute PE for each day of that year
        yearly_pe = [p.close_price / epsarray[i] for p in prices_for_year if epsarray[i] != 0]
        all_pe_ratios.extend(yearly_pe) 

    # Calculate median across all PEs
    all_pe_ratios = [pe for pe in all_pe_ratios if not np.isnan(pe)]
    median_pe = float(np.median(all_pe_ratios)) if all_pe_ratios else None

    return {
        "PEG": round(peg / epsgrowth, 2) if epsgrowth else None,
        "MedianPE": round(median_pe, 2) if median_pe is not None else None
    }