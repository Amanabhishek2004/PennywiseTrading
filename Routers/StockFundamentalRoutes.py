from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from Database.databaseconfig import get_db
from Database.models import Stock
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from Database.Schemas.StockFundamentalRoutesSchema import * 

import ast

router = APIRouter(prefix="/V2", tags=["Stock Fundamental Data Routes"])
def parse_metric_with_dates(metric_str, dates):
    try:
        values = ast.literal_eval(metric_str)
        return [
            {"Date": date, "Value": float(val)}
            for date, val in zip(dates, values)
        ]
    except Exception:
        return []       
    

@router.get("/earning-metric/{ticker}", response_model=EarningMetricSchema)
def get_earning_metric(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    earning_metric = stock.earning_metrics[0] if stock.earning_metrics else None
    if not earning_metric:
        raise HTTPException(status_code=404, detail="Earning metric not found")

    if stock.earning_metrics:
        date_str = stock.earning_metrics[0].Date  
        try:
            dates = ast.literal_eval(date_str)
        except Exception:
            dates = []
    else:
        dates = []

    # Build the response in the required format
    return {
        "id": earning_metric.id,
        "OperatingRevenue": parse_metric_with_dates(earning_metric.OperatingRevenue, dates),
        "EBIT_cagr": earning_metric.EBIT_cagr,
        "EBITDA": parse_metric_with_dates(earning_metric.EBITDA, dates),
        "EBITDA_cagr": earning_metric.EBITDA_cagr,
        "OperatingRevenue_Cagr": earning_metric.OperatingRevenue_Cagr,
        "operatingMargins": parse_metric_with_dates(earning_metric.operatingMargins, dates),
        "OperatingProfit": parse_metric_with_dates(earning_metric.OperatingProfit, dates),
        "epsTrailingTwelveMonths": parse_metric_with_dates(earning_metric.epsTrailingTwelveMonths, dates),
        "epsForward": earning_metric.epsForward,
        "NetIncome_cagr": earning_metric.NetIncome_cagr,
        "FCFF_Cagr": earning_metric.FCFF_Cagr,
        "NetIncome": parse_metric_with_dates(earning_metric.NetIncome, dates),
    }



@router.get("/expenses/{ticker}", response_model=ExpensesSchema)
def get_expenses(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.expenses:
        raise HTTPException(status_code=404, detail="Expenses not found")
    expenses = stock.expenses[0]

    # Extract dates for each metric
    capex_dates = []
    earnings_dates = []
    if stock.financials and stock.financials[0].Date_BalanceSheet:
        try:
            capex_dates = ast.literal_eval(stock.financials[0].Date_BalanceSheet)
        except Exception:
            capex_dates = []
    if stock.earning_metrics and stock.earning_metrics[0].Date:
        try:
            earnings_dates = ast.literal_eval(stock.earning_metrics[0].Date)
        except Exception:
            earnings_dates = []

    return {
        "id": expenses.id,
        "CapitalExpenditure_cagr": expenses.CapitalExpenditure_cagr,
        "dividendPayoutratio": expenses.dividendPayoutratio,
        "TaxRate": expenses.TaxRate,
        "CapitalExpenditure": parse_metric_with_dates(expenses.CapitalExpenditure, capex_dates),
        "InterestExpense_cagr": expenses.InterestExpense_cagr,
        "CurrentDebt_cagr": expenses.CurrentDebt_cagr,
        "EBIT": parse_metric_with_dates(expenses.EBIT, earnings_dates),
        "Operating_Expense": parse_metric_with_dates(expenses.Operating_Expense, earnings_dates),
        "Intrest_Expense": parse_metric_with_dates(expenses.Intrest_Expense, earnings_dates),
        "WACC": expenses.WACC,
        "stock_id": expenses.stock_id,
    }

@router.get("/financials/{ticker}", response_model=FinancialsSchema)
def get_financials(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.financials:
        raise HTTPException(status_code=404, detail="Financials not found")
    financials = stock.financials[0]

    # Extract dates for each metric
    balance_dates = []
    cashflow_dates = []
    days_dates = []
    try:
        if financials.Date_BalanceSheet:
            balance_dates = ast.literal_eval(financials.Date_BalanceSheet)
    except Exception:
        balance_dates = []
    try:
        if financials.Date_cashflow:
            cashflow_dates = ast.literal_eval(financials.Date_cashflow)
    except Exception:
        cashflow_dates = []
    try:
        if hasattr(stock, "Days") and stock.Days and stock.Days[0].Date:
            days_dates = ast.literal_eval(stock.Days[0].Date)
    except Exception:
        days_dates = []

    return {
        "id": financials.id,
        "RetainedEarnings_cagr": financials.RetainedEarnings_cagr,
        "Date_BalanceSheet": financials.Date_BalanceSheet,
        "EquityCapital": parse_metric_with_dates(financials.EquityCapital, balance_dates),
        "Date_cashflow": financials.Date_cashflow,
        "RetainedEarnings": parse_metric_with_dates(financials.RetainedEarnings, balance_dates),
        "UnusualExpense": parse_metric_with_dates(financials.UnusualExpense, balance_dates),
        "DepreciationAmortization": parse_metric_with_dates(financials.DepreciationAmortization, balance_dates),
        "WorkingCapital": parse_metric_with_dates(financials.WorkingCapital, balance_dates),
        "CashfromFinancingActivities": parse_metric_with_dates(financials.CashfromFinancingActivities, cashflow_dates),
        "CashfromInvestingActivities": parse_metric_with_dates(financials.CashfromInvestingActivities, cashflow_dates),
        "CashFromOperatingActivities": parse_metric_with_dates(financials.CashFromOperatingActivities, cashflow_dates),
        "TotalReceivablesNet": parse_metric_with_dates(financials.TotalReceivablesNet, balance_dates),
        "TotalAssets": parse_metric_with_dates(financials.TotalAssets, balance_dates),
        "FixedAssets": parse_metric_with_dates(financials.FixedAssets, balance_dates),
        "TotalLiabilities": parse_metric_with_dates(financials.TotalLiabilities, balance_dates),
        "TotalDebt": parse_metric_with_dates(financials.TotalDebt, balance_dates),
        "ROCE": parse_metric_with_dates(financials.ROCE, days_dates),
        "stock_id": financials.stock_id,
    }

@router.get("/quaterlyresult/{ticker}", response_model=QuaterlyresultSchema)
def get_quaterlyresult(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.quaterly_results:
        raise HTTPException(status_code=404, detail="Quaterly result not found")
    result = stock.quaterly_results[0]
    try:
        dates = ast.literal_eval(result.Date)
    except Exception:
        dates = []

    return {
        "id": result.id,
        "stock_id": result.stock_id,
        "ticker": result.ticker,
        "Date": result.Date,
        "Sales_Quaterly": parse_metric_with_dates(result.Sales_Quaterly, dates),
        "Expenses_Quaterly": parse_metric_with_dates(result.Expenses_Quaterly, dates),
        "OperatingProfit_Quaterly": parse_metric_with_dates(result.OperatingProfit_Quaterly, dates),
        "EPS_in_Rs_Quaterly": parse_metric_with_dates(result.EPS_in_Rs_Quaterly, dates),
        "Profit_before_tax_Quaterly": parse_metric_with_dates(result.Profit_before_tax_Quaterly, dates),
        "NetProfit_Quaterly": parse_metric_with_dates(result.NetProfit_Quaterly, dates),
        "Interest_Quaterly": parse_metric_with_dates(result.Interest_Quaterly, dates),
        "OPM_Percent_Quaterly": parse_metric_with_dates(result.OPM_Percent_Quaterly, dates),
        "Depreciation_Quaterly": parse_metric_with_dates(result.Depreciation_Quaterly, dates),
    }

@router.get("/shareholding/{ticker}", response_model=ShareholdingSchema)
def get_shareholding(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.shareholdings:
        raise HTTPException(status_code=404, detail="Shareholding not found")
    shareholding = stock.shareholdings[0]
    try:
        dates = ast.literal_eval(shareholding.Date)
    except Exception:
        dates = []

    return {
        "id": shareholding.id,
        "stock_id": shareholding.stock_id,
        "Date": shareholding.Date,
        "Promoters": parse_metric_with_dates(shareholding.Promoters, dates),
        "FIIs": parse_metric_with_dates(shareholding.FIIs, dates),
        "DIIs": parse_metric_with_dates(shareholding.DIIs, dates),
        "Public": parse_metric_with_dates(shareholding.Public, dates),
        "Government": parse_metric_with_dates(shareholding.Government, dates),
        "Others": parse_metric_with_dates(shareholding.Others, dates),
        "ShareholdersCount": parse_metric_with_dates(shareholding.ShareholdersCount, dates),
    }

def parse_metric_with_dates(metric_str, dates):
    try:
        values = ast.literal_eval(metric_str)
        return [
            {"Date": date, "Value": float(val)}
            for date, val in zip(dates, values)
        ]
    except Exception:
        return []

@router.get("/days/{ticker}", response_model=DaysSchema)
def get_days(ticker: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.Days:
        raise HTTPException(status_code=404, detail="Days data not found")
    days = stock.Days[0]
    try:
        dates = ast.literal_eval(days.Date)
    except Exception:
        dates = []

    return {
        "id": days.id,
        "stock_id": days.stock_id,
        "InventoryDays": parse_metric_with_dates(days.InventoryDays, dates),
        "DebtorDays": parse_metric_with_dates(days.DebtorDays, dates),
        "Date": days.Date,
        "WorkingCapitalDays": parse_metric_with_dates(days.WorkingCapitalDays, dates),
        "DaysPayable": parse_metric_with_dates(days.DaysPayable, dates),
        "CashConversionCycle": parse_metric_with_dates(days.CashConversionCycle, dates),
    }