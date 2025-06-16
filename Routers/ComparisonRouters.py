from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import * 
from typing import List
from Database.Schemas.StockSchema import *
from statistics import median
from Stock.Fundametals.Stock import * 
from Stock.Fundametals.StockCashFlow import *
from Stock.Fundametals.StockDIctScehma import *
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/Metrics", tags=["Stock Metrics"])

class PeersRequest(BaseModel):
    peers: List[str]

@router.post("/calculate/")
def calculate_median_for_metrics(request: PeersRequest, db: Session = Depends(get_db)):
     peers = request.peers
     peer_stocks = db.query(Stock).filter(Stock.Ticker.in_(peers)).all()
 
     metrics = {
         "earning_metric": {},
         "expense_metric": {},
         "valuation_metric": {},
         "operational_metric": {},
         "efficiency_metric": {},
     }
 
     for stock in peer_stocks:
         for em in stock.earning_metrics:
             for column, value in em.__dict__.items():
                 print(f"Column: {column}, Value: {value}")
                 if column not in ["id", "stock_id"] and column in eaningparams:
                     try:
                         metrics["earning_metric"].setdefault(column, []).append(float(value))
                     except (ValueError, TypeError):
                         print(f"[❌ SKIPPED] earning_metric.{column} - Invalid value: {value}")
 
         for exp in stock.expenses:
             for column, value in exp.__dict__.items():
                 if column not in ["id", "stock_id"] and column in expensesparams:
                     try:
                         metrics["expense_metric"].setdefault(column, []).append(float(value))
                     except (ValueError, TypeError):
                         print(f"[❌ SKIPPED] expense_metric.{column} - Invalid value: {value}")
 
         for fin in stock.financials:
             for column, value in fin.__dict__.items():
                 if column not in ["id", "stock_id"] and column in financialsparams:
                     try:
                         metrics["efficiency_metric"].setdefault(column, []).append(float(value))
                     except (ValueError, TypeError):
                         print(f"[❌ SKIPPED] efficiency_metric.{column} - Invalid value: {value}")
 
         for val in stock.metrics:
             for column, value in val.__dict__.items():
                 if column not in ["id", "stock_id"] and column in efficiencyparams:
                     try:
                         metrics["valuation_metric"].setdefault(column, []).append(float(value))
                     except (ValueError, TypeError):
                         print(f"[❌ SKIPPED] valuation_metric.{column} - Invalid value: {value}")
 
         for comp in stock.comparables:
             for column, value in comp.__dict__.items():
                 if column not in ["id", "stock_id"] and column in comparablesparams:
                     try:
                         metrics["operational_metric"].setdefault(column, []).append(float(value))
                     except (ValueError, TypeError):
                         print(f"[❌ SKIPPED] operational_metric.{column} - Invalid value: {value}")
 
     # Calculate medians with error reporting
     medians = {}
     for metric_name, data in metrics.items():
         medians[metric_name] = {}
         for key, values in data.items():
             try:
                 medians[metric_name][key] = median(values)
             except Exception as e:
                 print(f"[❌ ERROR] Failed to compute median for: {metric_name} -> {key}")
                 print(f"   Values: {values}")
                 print(f"Error: {e}")
 
     return medians
 

def calculate_median_value(benchmark, stock):
     negative_impact = [
         "trailingPE", "pricetoFreeCashFlow", "pricetoSales", "DebttoEquity",
         "trailingAnnualDividendYield", "CapitalExpenditure_Cagr",
         "TotalExpenses_Cagr", "InterestExpense_Cagr", "WACC",
         "Debt_Cagr", "COD", "enterpriseToEbitda", "pricetobook"
     ]
 
     scores = {}
 
     for metric, data in benchmark.items():
         scores[metric] = {}
         for key, benchmark_value in data.items():
             stock_value = stock.get(metric, {}).get(key, None)
             if stock_value is None:
                 continue
 
             if key in negative_impact:
                 scores[metric][key] = benchmark_value - stock_value 
             else:
                 scores[metric][key] = stock_value - benchmark_value
                   
     return scores

def CalculateAllscores(data) :
     metrics = {metric : 0 in metric for metric in data.keys()}
 
     for key in metrics.keys() :
         metrics[key] = sum(data[key].values())
 
     for key in metrics.keys() :
         total_score = sum(metrics[key].values())    
     return metrics  , total_score  
 


@router.get("/FCFF/{ticker}")
def get_the_cashflows(ticker: str, db: Session = Depends(get_db)):
     """
     Endpoint to calculate and return the Free Cash Flow to Firm (FCFF) for a given stock ticker.
 
     Args:
         ticker (str): Stock ticker symbol.
         db (Session): Database session dependency.
 
     Returns:
         dict: A dictionary containing the ticker and its calculated FCFF value.
     """
     try:
         # Call the FCFF calculation function
         fcff = CalculateFCFF(ticker, db)
         
         if fcff is None:
             raise HTTPException(
                 status_code=404,
                 detail=f"FCFF calculation failed for ticker: {ticker}"
             )
         
         return {
             "TICKER": ticker,
             "FCFF": fcff
         }
     
     except Exception as e:
         # Generic error handling
         raise HTTPException(
             status_code=500,
             detail=f"An error occurred: {str(e)}"
         )
 