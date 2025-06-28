from Database.models import *
import numpy as np 
import pandas as pd 
import yfinance as yf 
from datetime import datetime , timedelta


def parse_data(data_string):

    import ast
    if not data_string:
        return []
    
    try:
        parsed_list = ast.literal_eval(data_string)  # Convert string to list
        return [float(x) if x != 'nan' else float('nan') for x in parsed_list]
    except (ValueError, SyntaxError):
        raise ValueError(f"Invalid data format: {data_string}")

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





def CalculateMedianpe(Stock , db) : 
     
     stock_data = db.query(Stock).filter(Stock.Ticker == Stock).first()
     epsarray = parse_data(stock_data.earning_metrics[0].epsTrailingTwelveMonths)
     epsgrowth = stock_data.earning_metrics[0].epsForward*100
     peg = stock_data.comparables[0].trailingPE
     return {
          "PEG":peg /epsgrowth,  
     }

