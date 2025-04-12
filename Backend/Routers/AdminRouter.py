from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import * 
from typing import List
from Database.Schemas.StockSchema import *
import math
from fastapi import  UploadFile
from Stock.Stock import * 

router = APIRouter(prefix="/Admin", tags=["Admin"])



@router.post("/upload/")
async def upload_data(file: UploadFile, db: Session = Depends(get_db)):
     Base.metadata.drop_all(bind=engine)
     Base.metadata.create_all(bind=engine)
     
     if not file.filename.endswith(".xlsx"):
         raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
 
     try:
         df = pd.read_excel(file.file)
     except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error reading Excel file: {str(e)}")
 
     try:
         for _, row in df.iterrows():
             stock = Stock(
                 id=str(uuid4()),
                 Ticker=safe_get_as_string(row.get("tickers")),
                 CurrentPrice=safe_get_as_float(row.get("Current Price"),0),
                 marketCap=safe_get_as_float(row.get("marketCap"), 0),
                 twoHundredDayAverage=safe_get_as_float(row.get("twoHundredDayAverage"), 0),
                 fiftyDayAverage=safe_get_as_float(row.get("fiftyDayAverage"), "0"),
                 grossProfits=safe_get_as_float(row.get("grossProfits"), 0),
                 sector=safe_get_as_string(row.get("sector"), "Unknown"),
                 beta=safe_get_as_float(row.get("beta"), 0)
             )
             db.add(stock)
             db.commit()
             db.refresh(stock)
 
             earning_metric = EarningMetric(
                 id=str(uuid4()),
                 stock_id=stock.id,
                 EBIT_cagr=safe_get_as_float(row.get("EBIT_cagr"), 0),
                 EBITDA_cagr=safe_get_as_float(row.get("EBITDA_cagr"), 0),
                 OperatingRevenue_Cagr=safe_get_as_float(row.get("Operating Revenue_cagr"), 0),
                 OperatingRevenue = safe_get_as_string(row.get("Operating Revenue") , 0 ) , 
                 BasicEps_Cagr=safe_get_as_float(row.get("Basic EPS_cagr"), 0),
                 operatingMargins=safe_get_as_float(row.get("operatingMargins"), 0),
                 grossMargins=safe_get_as_float(row.get("grossMargins"), 0),
                 epsTrailingTwelveMonths=safe_get_as_float(row.get("epsTrailingTwelveMonths"), 0),
                 epsForward=safe_get_as_float(row.get("epsForward"), 0),
                 FreeCashFlow_cagr=safe_get_as_float(row.get("Free Cash Flow_cagr"), 0),
                 NetIncomeFromContinuingOperations_cagr=safe_get_as_float(row.get("Net Income From Continuing Operations_cagr"), 0),
                 NetIncome_cagr=safe_get_as_float(row.get("Net Income_cagr"), 0)
             )
             db.add(earning_metric)
             db.commit()
             print(earning_metric.stock.Ticker)
         
             comparables = Comparables(
                 id=str(uuid4()),
                 stock_id=stock.id,
                 trailingPE=safe_get_as_float(row.get("trailingPE"), 0),
                 forwardPE=safe_get_as_float(row.get("forwardPE"), 0),
                 pricetoBook=safe_get_as_float(row.get("bookValue"), 0),
                 pricetoFreeCashFlow=safe_get_as_float(row.get("Free Cash Flow_avggrowth"), 0),
                 pricetoSales=safe_get_as_float(row.get("Free Cash Flow_cagr"), 0),
                 DebttoEquity=safe_get_as_float(row.get("debtToEquity"), 0),
                 trailingAnnualDividendYield=safe_get_as_float(row.get("trailingAnnualDividendYield"), 0),
                 dividendYield=safe_get_as_float(row.get("dividendYield"), 0),
                 dividendRate=safe_get_as_float(row.get("dividendRate"), 0),
                 fiveYearAvgDividendYield=safe_get_as_float(row.get("fiveYearAvgDividendYield"), 0),
                 payoutRatio=safe_get_as_float(row.get("payoutRatio"), 0)
             )
             db.add(comparables)
             db.commit()
 
             expenses = Expenses(
                 id=str(uuid4()),
                 stock_id=stock.id,
                 CurrentDebt_cagr=safe_get_as_float(row.get("Current Debt_cagr"), 0),
                 CapitalExpenditure_cagr=safe_get_as_float(row.get("Capital Expenditure Reported"), 0),
                 InterestExpense_cagr=safe_get_as_float(row.get("Interest Expense_cagr"), 0),
                 Intrest_Expense = safe_get_as_string(row.get("Interest Expense") ,"0" ) , 
                 Operating_Expense = safe_get_as_string(row.get('Operating Expense') , "0" ) , 
                 TotalExpenses_cagr=safe_get_as_float(row.get("Total Expenses"), 0),
                 WACC=safe_get_as_float(row.get("WACC"), 0)
             )
             db.add(expenses)
             db.commit()
 
             financials = Financials(
                 id=str(uuid4()),
                 stock_id=stock.id,
                 NetTangibleAssets_cagr=safe_get_as_float(row.get("Net Tangible Assets_cagr"), 0),
                 InvestedCapital=safe_get_as_string(row.get("Invested Capital"), "0"),
                 InvestedCapital_cagr=safe_get_as_float(row.get("Invested Capital_cagr"), 0),
                 RetainedEarnings_cagr=safe_get_as_float(row.get("Retained Earnings_cagr"), 0),
                 TotalAssets=safe_get_as_string(row.get("Total Assets_cagr"), "0"),
                 TaxRateForCalcs=safe_get_as_string(row.get("Tax Rate For Calcs"), "0")
             )
             db.add(financials)
             db.commit()
             metrics = ValuationMetrics(
                 id=str(uuid4()),
                 stock_id=stock.id,
                 ROE=safe_get_as_float(row.get("ROE"), 0),
                 ROA=safe_get_as_float(row.get("ROA"), 0),
                 ROIC=safe_get_as_float(row.get("ROIC"), 0),
                 WACC=safe_get_as_float(row.get("WACC"), 0),
                 COD=safe_get_as_float(row.get("COD"), 0),
                 ICR=safe_get_as_float(row.get("ICR"), 0),
                 EFF=safe_get_as_float(row.get("EFF"), 0),
                 ATR=safe_get_as_float(row.get("ATR"), 0)
             )
             db.add(metrics)
             db.commit()
         db.commit()
         return {"message": "Data uploaded successfully"}
     except Exception as e:
         db.rollback()
         raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")