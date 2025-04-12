from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from Database.databaseconfig import get_db
from Database.models import Stock

app = FastAPI()


class EarningMetricSchema(BaseModel):
    id: str
    EBIT_cagr: Optional[float] = None
    EBITDA_cagr: Optional[float] = None
    OperatingRevenue_Cagr: Optional[float] = None
    OperatingRevenue: Optional[str] = None
    BasicEps_Cagr: Optional[float] = None
    operatingMargins: Optional[float] = None
    grossMargins: Optional[float] = None
    epsTrailingTwelveMonths: Optional[float] = None
    epsForward: Optional[float] = None
    FreeCashFlow_cagr: Optional[float] = None
    NetIncomeFromContinuingOperations_cagr: Optional[float] = None
    NetIncome_cagr: Optional[float] = None

class ComparablesSchema(BaseModel):
    id: str
    trailingPE: Optional[float] = None
    forwardPE: Optional[float] = None
    pricetoBook: Optional[float] = None
    pricetoFreeCashFlow: Optional[float] = None
    pricetoSales: Optional[float] = None
    DebttoEquity: Optional[float] = None
    trailingAnnualDividendYield: Optional[float] = None
    dividendYield: Optional[float] = None
    dividendRate: Optional[float] = None
    fiveYearAvgDividendYield: Optional[float] = None
    payoutRatio: Optional[float] = None

class ExpensesSchema(BaseModel):
    id: str
    CurrentDebt_cagr: Optional[float] = None
    CapitalExpenditure_cagr: Optional[float] = None
    InterestExpense_cagr: Optional[float] = None
    TotalExpenses_cagr: Optional[float] = None
    Intrest_Expense: Optional[str] = None
    Operating_Expense: Optional[str] = None
    WACC: Optional[float] = None


class FinancialsSchema(BaseModel):
    id: str
    NetTangibleAssets_cagr: Optional[float] = None
    InvestedCapital: Optional[str] = None
    InvestedCapital_cagr: Optional[float] = None
    RetainedEarnings_cagr: Optional[float] = None
    TotalAssets: Optional[str] = None
    TaxRateForCalcs: Optional[str] = None

class ValuationMetricsSchema(BaseModel):
    id: str
    ROE: Optional[float] = None
    ROA: Optional[float] = None
    ROIC: Optional[float] = None
    WACC: Optional[float] = None
    COD: Optional[float] = None
    ICR: Optional[float] = None
    EFF: Optional[float] = None
    ATR: Optional[float] = None



class StockSchema(BaseModel):
    id: str
    Ticker: str
    CurrentPrice: int
    marketCap: Optional[int] = None
    twoHundredDayAverage: Optional[float] = None
    fiftyDayAverage: Optional[float] = None
    grossProfits: Optional[float] = None
    sector: Optional[str] = None
    beta: Optional[float] = None

    # Change single object to a list
    earning_metrics: List[EarningMetricSchema] = []
    comparables: List[ComparablesSchema] = []
    expenses: List[ExpensesSchema] = []
    financials: List[FinancialsSchema] = []
    metrics: List[ValuationMetricsSchema] = []

    class Config:
        from_attributes = True
        orm_mode = True  # Ensures it converts ORM models correctly