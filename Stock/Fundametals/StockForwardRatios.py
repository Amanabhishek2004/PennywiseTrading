from Database.models import *
import numpy as np 
import pandas as pd 
import yfinance as yf 
from datetime import datetime , timedelta


def process_data(row):
        specific_column_data = row.replace("[" , "").replace("]" , "")
        data = specific_column_data.split(",") 
        
        vals =  [float(x)  if x !="nan" else np.nan for x in data][:-1]  if len(data) > 4 else [float(x)  if x !="nan" else np.nan for x in data]
        print(vals[0])
        return vals

def CalculateForwardPe(Ticker, db):
    # Tax rate
    taxrate = 0.3

    # Fetch stock data
    stock = db.query(Stock).filter(Stock.Ticker == Ticker).first()
    if not stock:
        raise ValueError(f"Stock with Ticker {Ticker} not found.")
    
    # Calculate forward interest expense
    intrests = process_data(stock.expenses[0].Intrest_Expense)
    recent_intrest = process_data(stock.expenses[0].Intrest_Expense)[0]
    intrestexpencegrowth = np.nanmean(-np.diff(intrests)/intrests[1:])  # Ensure numeric conversion
    forward_intrest_expense = recent_intrest * (1 + intrestexpencegrowth) * (1 - taxrate)
    # Calculate forward operating expense
    operating_expense = process_data(stock.expenses[0].Operating_Expense)
    recent_operating_expense = process_data(stock.expenses[0].Operating_Expense)[0]
    operating_expensegrowth = (np.nanmean(-np.diff(operating_expense) / operating_expense[1:]))# Ensure numeric conversion
    forward_operating_expense = recent_operating_expense * (1 + operating_expensegrowth)

    # Calculate forward sales
    sales  = process_data(stock.earning_metrics[0].OperatingRevenue)
    recentsales = process_data(stock.earning_metrics[0].OperatingRevenue)[0]
    salesgrowth = np.nanmedian( -np.diff(sales)/ sales[1:] ) # Ensure numeric conversion
    forwardsales = recentsales * (1 + salesgrowth)
    print("salesGrowth" , salesgrowth)
    print("IntrestGrowth" , intrestexpencegrowth)
    print("OperatingExpenseGrowth" , operating_expensegrowth)
    # Calculate net earnings and forward EPS
    stock.CurrentPrice = 61
    stock.marketCap = 5691440128
    num_outstanding_stocks = stock.marketCap  / stock.CurrentPrice
    NetEarning = (forwardsales - forward_intrest_expense - forward_operating_expense) * (1 - taxrate)
    forwardeps = NetEarning / num_outstanding_stocks
    print(forwardeps)
    print( "CAP" , stock.marketCap )
    # Return forward PE ratio
    return stock.CurrentPrice / forwardeps




def CalculateMedianpe(Stock) : 
     
     stock_data = yf.Ticker(f"{Stock}.NS")
     eps_df = stock_data.quarterly_financials.T["Basic EPS"]
     eps_df.index = pd.to_datetime(eps_df.index)
     
     end_date = datetime.now()
     start_date = end_date - timedelta(days=2 * 365)

     data = stock_data.history(start=start_date, end=end_date)
     data.index = pd.to_datetime(data.index.date)
     eps_df = eps_df.resample("Y").sum()
     epsgrowth = (np.diff(eps_df) / eps_df[1:])*100
     current_date = datetime.now().date()
     eps_df = eps_df.resample("D").last().ffill()
     new_index = pd.date_range(start=eps_df.index[0], end=current_date)    
     eps_df = eps_df.reindex(new_index).ffill()
     merged_data = data.merge(eps_df , how="inner" , left_index=True , right_index=True)
     ttmpe = (merged_data["Close"] / merged_data["Basic EPS"]).median()
     peg = ttmpe / epsgrowth

     return {
          "PEG":peg , 
          "TTMPE" :ttmpe 
     }

