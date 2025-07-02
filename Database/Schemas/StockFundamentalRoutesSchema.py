from pydantic import BaseModel
from typing import List, Optional

class DateValuePair(BaseModel):
    Date: str
    Value: float




class ExpensesSchema(BaseModel):
    id: str
    CapitalExpenditure_cagr: Optional[float]
    dividendPayoutratio: Optional[str]
    TaxRate: Optional[str]
    CapitalExpenditure: Optional[List[DateValuePair]]
    InterestExpense_cagr: Optional[float]
    CurrentDebt_cagr: Optional[float]
    EBIT: Optional[List[DateValuePair]]
    Operating_Expense: Optional[List[DateValuePair]]
    Intrest_Expense: Optional[List[DateValuePair]]
    WACC: Optional[float]
    stock_id: Optional[str]

    class Config:
        orm_mode = True



class DaysSchema(BaseModel):
    id: str
    stock_id: Optional[str]
    InventoryDays: Optional[List[DateValuePair]]
    DebtorDays: Optional[List[DateValuePair]]
    Date: Optional[str]
    WorkingCapitalDays: Optional[List[DateValuePair]]
    DaysPayable: Optional[List[DateValuePair]]
    CashConversionCycle: Optional[List[DateValuePair]]

    class Config:
        orm_mode = True





class FinancialsSchema(BaseModel):
    id: str
    RetainedEarnings_cagr: Optional[float]
    Date_BalanceSheet: Optional[str]
    EquityCapital: Optional[List[DateValuePair]]
    Date_cashflow: Optional[str]
    RetainedEarnings: Optional[List[DateValuePair]]
    UnusualExpense: Optional[List[DateValuePair]]
    DepreciationAmortization: Optional[List[DateValuePair]]
    WorkingCapital: Optional[List[DateValuePair]]
    CashfromFinancingActivities: Optional[List[DateValuePair]]
    CashfromInvestingActivities: Optional[List[DateValuePair]]
    CashFromOperatingActivities: Optional[List[DateValuePair]]
    TotalReceivablesNet: Optional[List[DateValuePair]]
    TotalAssets: Optional[List[DateValuePair]]
    FixedAssets: Optional[List[DateValuePair]]
    TotalLiabilities: Optional[List[DateValuePair]]
    TotalDebt: Optional[List[DateValuePair]]
    ROCE: Optional[List[DateValuePair]]
    stock_id: Optional[str]

    class Config:
        orm_mode = True

class QuaterlyresultSchema(BaseModel):
    id: str
    stock_id: Optional[str]
    ticker: str
    Date: str
    Sales_Quaterly: Optional[List[DateValuePair]]
    Expenses_Quaterly: Optional[List[DateValuePair]]
    OperatingProfit_Quaterly: Optional[List[DateValuePair]]
    EPS_in_Rs_Quaterly: Optional[List[DateValuePair]]
    Profit_before_tax_Quaterly: Optional[List[DateValuePair]]
    NetProfit_Quaterly: Optional[List[DateValuePair]]
    Interest_Quaterly: Optional[List[DateValuePair]]
    OPM_Percent_Quaterly: Optional[List[DateValuePair]]
    Depreciation_Quaterly: Optional[List[DateValuePair]]

    class Config:
        orm_mode = True

class ShareholdingSchema(BaseModel):
    id: str
    stock_id: str
    Date: str
    Promoters: Optional[List[DateValuePair]]
    FIIs: Optional[List[DateValuePair]]
    DIIs: Optional[List[DateValuePair]]
    Public: Optional[List[DateValuePair]]
    Government: Optional[List[DateValuePair]]
    Others: Optional[List[DateValuePair]]
    ShareholdersCount: Optional[List[DateValuePair]]

    class Config:
        orm_mode = True





class EarningMetricSchema(BaseModel):
    id: str
    OperatingRevenue: Optional[List[DateValuePair]]
    EBIT_cagr: Optional[float]
    EBITDA: Optional[List[DateValuePair]]
    EBITDA_cagr: Optional[float]
    OperatingRevenue_Cagr: Optional[float]
    operatingMargins: Optional[List[DateValuePair]]
    OperatingProfit: Optional[List[DateValuePair]]
    epsTrailingTwelveMonths: Optional[List[DateValuePair]]
    epsForward: Optional[float]
    NetIncome_cagr: Optional[float]
    FCFF_Cagr: Optional[float]
    NetIncome: Optional[List[DateValuePair]]

    class Config:
        orm_mode = True
