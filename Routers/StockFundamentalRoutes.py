from datetime import date
import ast
import sys
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import get_db
from Database.models import Stock, User, ReadHistory
from Database.Schemas.StockFundamentalRoutesSchema import (
    EarningMetricSchema,
    ExpensesSchema,
    FinancialsSchema,
    QuaterlyresultSchema,
    ShareholdingSchema,
    DaysSchema,
)
from Routers.UserAccountRoutes import get_current_user

router = APIRouter(prefix="/V2", tags=["Stock Fundamental Data Routes"])



def _get_deep_size(obj, seen: set | None = None) -> int:
    """Recursively calculate the memory footprint of a Python object (in bytes)."""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    if isinstance(obj, dict):
        size += sum(_get_deep_size(k, seen) + _get_deep_size(v, seen) for k, v in obj.items())
    elif hasattr(obj, "__dict__"):
        size += _get_deep_size(vars(obj), seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        size += sum(_get_deep_size(i, seen) for i in obj)
    return size


def _track_read_and_data_usage(db: Session, user_id: str, data_obj, read_inc: int = 1) -> None:
    """Increment today's ReadHistory.reads and data_used (in MB)."""
    today = date.today()
    mb_used = round(_get_deep_size(data_obj) / (1024 * 1024), 4)

    record = db.query(ReadHistory).filter_by(user_id=user_id, date=str(today)).first()
    if record:
        record.reads += read_inc
        record.dataused += mb_used
    else:
        record = ReadHistory(user_id=user_id, reads=read_inc, data_used=mb_used, date=today)
        db.add(record)
    db.commit()



def _parse_metric_with_dates(metric_str: str | None, dates: list[str]):
    try:
        values = ast.literal_eval(metric_str or "[]")
        return [{"Date": d, "Value": float(v)} for d, v in zip(dates, values)]
    except Exception:
        return []


@router.get("/earning-metric/{ticker}", response_model=EarningMetricSchema)
def get_earning_metric(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.earning_metrics:
        raise HTTPException(status_code=404, detail="Earning metric not found")

    em = stock.earning_metrics[0]
    dates = ast.literal_eval(em.Date or "[]") if em.Date else []

    response = {
        "id": em.id,
        "OperatingRevenue": _parse_metric_with_dates(em.OperatingRevenue, dates),
        "EBIT_cagr": em.EBIT_cagr,
        "EBITDA": _parse_metric_with_dates(em.EBITDA, dates),
        "EBITDA_cagr": em.EBITDA_cagr,
        "OperatingRevenue_Cagr": em.OperatingRevenue_Cagr,
        "operatingMargins": _parse_metric_with_dates(em.operatingMargins, dates),
        "OperatingProfit": _parse_metric_with_dates(em.OperatingProfit, dates),
        "epsTrailingTwelveMonths": _parse_metric_with_dates(em.epsTrailingTwelveMonths, dates),
        "epsForward": em.epsForward,
        "NetIncome_cagr": em.NetIncome_cagr,
        "FCFF_Cagr": em.FCFF_Cagr,
        "NetIncome": _parse_metric_with_dates(em.NetIncome, dates),
    }

    _track_read_and_data_usage(db, current_user.id, response)
    return response


@router.get("/expenses/{ticker}", response_model=ExpensesSchema)
def get_expenses(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.expenses:
        raise HTTPException(status_code=404, detail="Expenses not found")

    exp = stock.expenses[0]
    capex_dates = ast.literal_eval(stock.financials[0].Date_BalanceSheet or "[]") if stock.financials else []
    earnings_dates = ast.literal_eval(stock.earning_metrics[0].Date or "[]") if stock.earning_metrics else []

    response = {
        "id": exp.id,
        "CapitalExpenditure_cagr": exp.CapitalExpenditure_cagr,
        "dividendPayoutratio": exp.dividendPayoutratio,
        "TaxRate": exp.TaxRate,
        "CapitalExpenditure": _parse_metric_with_dates(exp.CapitalExpenditure, capex_dates),
        "InterestExpense_cagr": exp.InterestExpense_cagr,
        "CurrentDebt_cagr": exp.CurrentDebt_cagr,
        "EBIT": _parse_metric_with_dates(exp.EBIT, earnings_dates),
        "Operating_Expense": _parse_metric_with_dates(exp.Operating_Expense, earnings_dates),
        "Intrest_Expense": _parse_metric_with_dates(exp.Intrest_Expense, earnings_dates),
        "WACC": exp.WACC,
        "stock_id": exp.stock_id,
    }

    _track_read_and_data_usage(db, current_user.id, response)
    return response


@router.get("/financials/{ticker}", response_model=FinancialsSchema)
def get_financials(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.financials:
        raise HTTPException(status_code=404, detail="Financials not found")

    fin = stock.financials[0]
    balance_dates = ast.literal_eval(fin.Date_BalanceSheet or "[]") if fin.Date_BalanceSheet else []
    cashflow_dates = ast.literal_eval(fin.Date_cashflow or "[]") if fin.Date_cashflow else []
    days_dates = ast.literal_eval(stock.Days[0].Date or "[]") if stock.Days else []

    response = {
        "id": fin.id,
        "RetainedEarnings_cagr": fin.RetainedEarnings_cagr,
        "Date_BalanceSheet": fin.Date_BalanceSheet,
        "EquityCapital": _parse_metric_with_dates(fin.EquityCapital, balance_dates),
        "Date_cashflow": fin.Date_cashflow,
        "RetainedEarnings": _parse_metric_with_dates(fin.RetainedEarnings, balance_dates),
        "UnusualExpense": _parse_metric_with_dates(fin.UnusualExpense, balance_dates),
        "DepreciationAmortization": _parse_metric_with_dates(fin.DepreciationAmortization, balance_dates),
        "WorkingCapital": _parse_metric_with_dates(fin.WorkingCapital, balance_dates),
        "CashfromFinancingActivities": _parse_metric_with_dates(fin.CashfromFinancingActivities, cashflow_dates),
        "CashfromInvestingActivities": _parse_metric_with_dates(fin.CashfromInvestingActivities, cashflow_dates),
        "CashFromOperatingActivities": _parse_metric_with_dates(fin.CashFromOperatingActivities, cashflow_dates),
        "TotalReceivablesNet": _parse_metric_with_dates(fin.TotalReceivablesNet, balance_dates),
        "TotalAssets": _parse_metric_with_dates(fin.TotalAssets, balance_dates),
        "FixedAssets": _parse_metric_with_dates(fin.FixedAssets, balance_dates),
        "TotalLiabilities": _parse_metric_with_dates(fin.TotalLiabilities, balance_dates),
        "TotalDebt": _parse_metric_with_dates(fin.TotalDebt, balance_dates),
        "ROCE": _parse_metric_with_dates(fin.ROCE, days_dates),
        "stock_id": fin.stock_id,
    }

    _track_read_and_data_usage(db, current_user.id, response)
    return response


@router.get("/quaterlyresult/{ticker}", response_model=QuaterlyresultSchema)
def get_quaterlyresult(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.quaterly_results:
        raise HTTPException(status_code=404, detail="Quarterly result not found")

    res = stock.quaterly_results[0]
    dates = ast.literal_eval(res.Date or "[]") if res.Date else []

    response = {
        "id": res.id,
        "stock_id": res.stock_id,
        "ticker": res.ticker,
        "Date": res.Date,
        "Sales_Quaterly": _parse_metric_with_dates(res.Sales_Quaterly, dates),
        "Expenses_Quaterly": _parse_metric_with_dates(res.Expenses_Quaterly, dates),
        "OperatingProfit_Quaterly": _parse_metric_with_dates(res.OperatingProfit_Quaterly, dates),
        "EPS_in_Rs_Quaterly": _parse_metric_with_dates(res.EPS_in_Rs_Quaterly, dates),
        "Profit_before_tax_Quaterly": _parse_metric_with_dates(res.Profit_before_tax_Quaterly, dates),
        "NetProfit_Quaterly": _parse_metric_with_dates(res.NetProfit_Quaterly, dates),
        "Interest_Quaterly": _parse_metric_with_dates(res.Interest_Quaterly, dates),
        "OPM_Percent_Quaterly": _parse_metric_with_dates(res.OPM_Percent_Quaterly, dates),
        "Depreciation_Quaterly": _parse_metric_with_dates(res.Depreciation_Quaterly, dates),
    }

    _track_read_and_data_usage(db, current_user.id, response)
    return response

@router.get("/shareholding/{ticker}", response_model=ShareholdingSchema , )
def get_shareholding(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.shareholdings:
        raise HTTPException(status_code=404, detail="Shareholding not found")

    sh = stock.shareholdings[0]
    dates = ast.literal_eval(sh.Date or "[]") if sh.Date else []

    response = {
        "id": sh.id,
        "stock_id": sh.stock_id,
        "Date": sh.Date,
        "Promoters": _parse_metric_with_dates(sh.Promoters, dates),
        "FIIs": _parse_metric_with_dates(sh.FIIs, dates),
        "DIIs": _parse_metric_with_dates(sh.DIIs, dates),
        "Public": _parse_metric_with_dates(sh.Public, dates),
        "Government": _parse_metric_with_dates(sh.Government, dates),
        "Others": _parse_metric_with_dates(sh.Others, dates),
        "ShareholdersCount": _parse_metric_with_dates(sh.ShareholdersCount, dates),
    }

    _track_read_and_data_usage(db, current_user.id, response)
    return response

@router.get("/days/{ticker}", response_model=DaysSchema)
def get_days(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock or not stock.Days:
        raise HTTPException(status_code=404, detail="Days data not found")

    days = stock.Days[0]
    dates = ast.literal_eval(days.Date or "[]") if days.Date else []

    response = {
        "id": days.id,
        "stock_id": days.stock_id,
        "InventoryDays": _parse_metric_with_dates(days.InventoryDays, dates),
        "DebtorDays": _parse_metric_with_dates(days.DebtorDays, dates),
        "Date": days.Date,
        "WorkingCapitalDays": _parse_metric_with_dates(days.WorkingCapitalDays, dates),
        "DaysPayable": _parse_metric_with_dates(days.DaysPayable, dates),
        "CashConversionCycle": _parse_metric_with_dates(days.CashConversionCycle, dates),
    }

    _track_read_and_data_usage(db, current_user.id, response)
    return response

from Stock.Fundametals.StockScreener import * 
import math

def replace_nan_with_none(obj):
    if isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_nan_with_none(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj

@router.get("/screening-scores/all")
def get_all_screening_scores(
    db: Session = Depends(get_db),
):
    stocks = db.query(Stock).all()
    results = []
    for stock in stocks:
        financial_score = calculate_financial_score(stock)
        technical_scores = calculate_technical_score_periodwise(stock , db)
        results.append({
            "ticker": stock.Ticker,
            "financial_score": financial_score,
            "technical_scores": technical_scores
        })
        stock.FinancialScore = float(financial_score)
        stock.TechnicalIntradayScore = technical_scores.get("1m", 0.0) 
        stock.TechnicalDailyScore = technical_scores.get("1d", 0.0)
        db.commit()
    return replace_nan_with_none(results)
