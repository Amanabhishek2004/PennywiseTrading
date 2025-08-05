from pydantic import BaseModel , validator
from typing import List, Optional
import math


class ChannelSchema(BaseModel):
    id: str
    ticker: Optional[str]
    upper_channel_slope: Optional[float]
    upper_channel_intercept: Optional[float]
    lower_channel_slope: Optional[float]
    lower_channel_intercept: Optional[float]
    period: Optional[str]

    class Config:
        orm_mode = True


class StockTechnicalsSchema(BaseModel):
    id: str
    ticker: Optional[str]
    period: Optional[str]
    RsiSlope: Optional[float]
    CurrentSupport: Optional[float]
    CurrentResistance: Optional[float]
    VolumeUpperChannelSlope: Optional[float]
    VolumeLowerChannelSlope: Optional[float]
    CurrentRsi: Optional[float]

    class Config:
        orm_mode = True


class EarningMetricSchema(BaseModel):
    id: str
    OperatingRevenue: Optional[str]
    EBIT_cagr: Optional[float]
    EBITDA: Optional[str]
    EBITDA_cagr: Optional[float]
    OperatingRevenue_Cagr: Optional[float]
    operatingMargins: Optional[str]
    OperatingProfit: Optional[str]
    epsTrailingTwelveMonths: Optional[str]
    epsForward: Optional[float]
    NetIncome_cagr: Optional[float]
    FCFF_Cagr: Optional[float]
    NetIncome: Optional[str]

    class Config:
        orm_mode = True


class ComparablesSchema(BaseModel):
    id: Optional[str]
    trailingPE: Optional[float] = 0.0
    forwardPE: Optional[float] = 0.0
    pricetoBook: Optional[float] = 0.0
    pricetoFreeCashFlow: Optional[float] = 0.0
    FCFF_Yield: Optional[float] = 0.0
    pricetoSales: Optional[float] = 0.0
    DebttoEquity: Optional[float] = 0.0
    trailingAnnualDividendYield: Optional[float] = 0.0
    dividendYield: Optional[float] = 0.0
    dividendRate: Optional[float] = 0.0
    fiveYearAvgDividendYield: Optional[float] = 0.0
    payoutRatio: Optional[float] = 0.0
    medianpe: Optional[float] = 0.0
    EV: Optional[float] = 0.0
    EVEBITDA: Optional[float] = 0.0
    CurrentRatio: Optional[float] = 0.0
    peg: Optional[float] = 0.0
    Avg_Sales_QoQ_Growth_Percent: Optional[float] = 0.0
    Avg_NetProfit_QoQ_Growth_Percent: Optional[float] = 0.0
    Avg_OperatingProfit_QoQ_Growth_Percent: Optional[float] = 0.0
    Avg_EPS_QoQ_Growth_Percent: Optional[float] = 0.0

    @validator('*', pre=True)
    def replace_nan_with_zero(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return 0.0
        return v

    class Config:
        orm_mode = True


class ExpensesSchema(BaseModel):
    id: str
    CapitalExpenditure_cagr: Optional[float]
    dividendPayoutratio: Optional[str]
    CapitalExpenditure: Optional[str]
    InterestExpense_cagr: Optional[float]
    CurrentDebt_cagr: Optional[float]
    EBIT: Optional[str]
    Operating_Expense: Optional[str]
    Intrest_Expense: Optional[str]
    WACC: Optional[float]

    class Config:
        orm_mode = True


class FinancialsSchema(BaseModel):
    id: str
    RetainedEarnings_cagr: Optional[float]
    RetainedEarnings: Optional[str]
    EquityCapital :Optional[str]
    UnusualExpense: Optional[str]
    DepreciationAmortization: Optional[str]
    WorkingCapital: Optional[str]
    CashfromFinancingActivities: Optional[str]
    CashfromInvestingActivities: Optional[str]
    CashFromOperatingActivities: Optional[str]
    TotalReceivablesNet: Optional[str]
    TotalAssets: Optional[str]
    FixedAssets: Optional[str]
    TotalLiabilities: Optional[str]
    TotalDebt: Optional[str]

    class Config:
        orm_mode = True


class ValuationMetricsSchema(BaseModel):
    id: str
    ROE: Optional[float]
    FCFF: Optional[str]
    ROA: Optional[float]
    ROIC: Optional[str]
    WACC: Optional[float]
    COD: Optional[float]
    ICR: Optional[float]

    class Config:
        orm_mode = True


class DaysSchema(BaseModel):
    id: str
    InventoryDays: Optional[str]
    DebtorDays: Optional[str]
    WorkingCapitalDays: Optional[str]
    CashConversionCycle: Optional[str]

    class Config:
        orm_mode = True


class PriceDataSchema(BaseModel):
    id: str
    ticker: Optional[str]
    date: Optional[str]
    open_price: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    close_price: Optional[float]
    volume: Optional[int]
    RSI: Optional[float]
    OnbalanceVolume: Optional[float]

    class Config:
        orm_mode = True


class SupportDataSchema(BaseModel):
    id: str
    Price: Optional[float]
    timestamp: Optional[str]
    Pattern: Optional[str]
    retests: Optional[int]
    period: Optional[str]

    class Config:
        orm_mode = True


class QuaterlyResultSchema(BaseModel):
    id: str
    ticker: str
    Date: str
    Sales_Quaterly: Optional[str]
    Expenses_Quaterly: Optional[str]
    OperatingProfit_Quaterly: Optional[str]
    EPS_in_Rs_Quaterly: Optional[str]
    Profit_before_tax_Quaterly: Optional[str]
    NetProfit_Quaterly: Optional[str]
    Interest_Quaterly: Optional[str]
    OPM_Percent_Quaterly: Optional[str]
    Depreciation_Quaterly: Optional[str]

    class Config:
        orm_mode = True


class ShareholdingSchema(BaseModel):
    id: str
    Date: str
    Promoters: Optional[str]
    FIIs: Optional[str]
    DIIs: Optional[str]
    Public: Optional[str]
    Government: Optional[str]
    Others: Optional[str]
    ShareholdersCount: Optional[str]

    class Config:
        orm_mode = True


class StockSchema(BaseModel):
    id: str
    Ticker: str
    CurrentPrice: int
    marketCap: Optional[float]
    Description: Optional[str]
    CompanyName: Optional[str]
    sector: Optional[str]
    beta: Optional[float]
    Industry: Optional[str]
    updated: Optional[str]
    FloatShares: Optional[float]
    sharesOutstanding: Optional[float]
    channels: List[ChannelSchema] = []
    technicals: List[StockTechnicalsSchema] = []
    earning_metrics: List[EarningMetricSchema] = []
    comparables: List[ComparablesSchema] = []
    expenses: List[ExpensesSchema] = []
    financials: List[FinancialsSchema] = []
    metrics: List[ValuationMetricsSchema] = []
    Days: List[DaysSchema] = []
    support: List[SupportDataSchema] = []
    quaterly_results: List[QuaterlyResultSchema] = []
    shareholdings: List[ShareholdingSchema] = []

    class Config:
        orm_mode = True


class StockSearchschema(BaseModel):
    id: str 
    CompanyName: Optional[str]
    Ticker: str
    Industry: Optional[str]
    TechnicalIntradayScore  : Optional[float] = 0.0 
    FinancialScore : Optional[float] = 0.0
    TechnicalDailyScore : Optional[float]
    updated: Optional[str]
    
    class Config:
        orm_mode = True