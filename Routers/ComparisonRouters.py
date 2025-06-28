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

import ast
from statistics import median

@router.post("/calculate/")
def calculate_median_for_metrics(request: PeersRequest, db: Session = Depends(get_db)):
    peers = request.peers
    peer_stocks = db.query(Stock).filter(Stock.Ticker.in_(peers)).all()

    metrics = {
        "earning_metrics": {},
        "expense_metrics": {},
        "valuation_metrics": {},
        "operational_metrics": {},
        "efficiency_metrics": {},
    }

    def try_parse_and_median(val):
        if isinstance(val, str) and val.strip().startswith("[") and val.strip().endswith("]"):
            try:
                arr = ast.literal_eval(val)
                arr = [float(x) for x in arr if x not in ("", None)]
                return median(arr) if arr else None
            except Exception:
                return None
        try:
            return float(val)
        except Exception:
            return None

    for stock in peer_stocks:
        for em in stock.earning_metrics:
            for column, value in em.__dict__.items():
                if column not in ["id", "stock_id"]:
                    val = try_parse_and_median(value)
                    if val is not None:
                        metrics["earning_metrics"].setdefault(column, []).append(val)

        for exp in stock.expenses:
            for column, value in exp.__dict__.items():
                if column not in ["id", "stock_id"]:
                    val = try_parse_and_median(value)
                    if val is not None:
                        metrics["expense_metrics"].setdefault(column, []).append(val)

        for fin in stock.financials:
            for column, value in fin.__dict__.items():
                if column not in ["id", "stock_id"]:
                    val = try_parse_and_median(value)
                    if val is not None:
                        metrics["efficiency_metrics"].setdefault(column, []).append(val)

        for valm in stock.metrics:
            for column, value in valm.__dict__.items():
                if column not in ["id", "stock_id"]:
                    val = try_parse_and_median(value)
                    if val is not None:
                        metrics["valuation_metrics"].setdefault(column, []).append(val)

        for comp in stock.comparables:
            for column, value in comp.__dict__.items():
                if column not in ["id", "stock_id"]:
                    val = try_parse_and_median(value)
                    if val is not None:
                        metrics["operational_metrics"].setdefault(column, []).append(val)

    # Calculate medians for all columns in each section
    medians = {}
    for section, data in metrics.items():
        medians[section] = {}
        for key, values in data.items():
            try:
                medians[section][key] = median(values)
            except Exception as e:
                print(f"[❌ ERROR] Failed to compute median for: {section} -> {key}")
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
 