from pydantic import BaseModel
from typing import List, Optional


class StockFinancialScoreSchema(BaseModel):
    id: str
    stock_id: str
    trailingPE_score: Optional[float]
    forwardPE_score: Optional[float]
    peg_score: Optional[float]
    EVEBITDA_score: Optional[float]
    medianpe_score: Optional[float]
    pricetoSales_score: Optional[float]
    pricetoFreeCashFlow_score: Optional[float]
    FCFF_Yield_score: Optional[float]
    CurrentRatio_score: Optional[float]
    DebttoEquity_score: Optional[float]
    Avg_Sales_QoQ_Growth_Percent_score: Optional[float]
    Avg_NetProfit_QoQ_Growth_Percent_score: Optional[float]
    Avg_OperatingProfit_QoQ_Growth_Percent_score: Optional[float]
    Avg_EPS_QoQ_Growth_Percent_score: Optional[float]
    EBIT_cagr_score: Optional[float]
    EBITDA_cagr_score: Optional[float]
    OperatingRevenue_Cagr_score: Optional[float]
    NetIncome_cagr_score: Optional[float]
    FCFF_Cagr_score: Optional[float]
    operatingMargins_score: Optional[float]
    epsTrailingTwelveMonths_score: Optional[float]
    epsForward_score: Optional[float]
    ROE_score: Optional[float]
    ROA_score: Optional[float]
    ROIC_score: Optional[float]
    WACC_score: Optional[float]
    COD_score: Optional[float]
    ICR_score: Optional[float]
    operatingExpense_score: Optional[float]
    Intrest_Expense_score: Optional[float]
    CurrentDebt_cagr_score: Optional[float]
    total_score: Optional[float]

    class Config:
       from_attributes = True


class StockTechnicalScoreSchema(BaseModel):
    id: str
    stock_id: str
    period: str
    CurrentRsi_score: Optional[float]
    RsiSlope_score: Optional[float]
    ResistanceProximity_score: Optional[float]
    SupportProximity_score: Optional[float]
    VolumeUpperChannelSlope_score: Optional[float]
    VolumeLowerChannelSlope_score: Optional[float]
    ChannelUpperSlope_score: Optional[float]
    ChannelLowerSlope_score: Optional[float]
    total_score: Optional[float]

    class Config:
         from_attributes = True


class StockScoresResponse(BaseModel):
    ticker: str
    financial_score: Optional[StockFinancialScoreSchema]
    technical_scores: List[StockTechnicalScoreSchema]

    class Config:
         from_attributes = True
