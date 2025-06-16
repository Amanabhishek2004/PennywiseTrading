from sqlalchemy import Column, String, ForeignKey, Integer, Float, BigInteger
from sqlalchemy.orm import relationship
from Database.databaseconfig import Base
from uuid import uuid4
import json

# Utility function
def ConvertStringJsonTo_Array(string):
    try:
        return json.loads(string)
    except json.JSONDecodeError:
        print("Invalid JSON string")
        return []

# Stocks Table
class Stock(Base):
    __tablename__ = "Stocks"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    Ticker = Column(String, unique=True, index=True)
    CurrentPrice = Column(Integer, nullable=False, default=0)
    marketCap = Column(Float)
    Description = Column(String)
    CompanyName = Column(String)
    sector = Column(String)
    beta = Column(Float)
    Industry = Column(String)
    updated = Column(String)
    FloatShares = Column(Float)
    sharesOutstanding = Column(Float)
    channels = relationship("Channel", back_populates="stock", cascade="all, delete")
    technicals = relationship("StockTechnicals", back_populates="stock", cascade="all, delete")
    earning_metrics = relationship("EarningMetric", back_populates="stock", cascade="all, delete")
    comparables = relationship("Comparables", back_populates="stock", cascade="all, delete")
    expenses = relationship("Expenses", back_populates="stock", cascade="all, delete")
    financials = relationship("Financials", back_populates="stock", cascade="all, delete")
    metrics = relationship("ValuationMetrics", back_populates="stock", cascade="all, delete")
    pricedata = relationship("PriceData", back_populates="stock", cascade="all, delete")
    Days = relationship("Days", back_populates="stock", cascade="all, delete")
    support = relationship("SupportData", back_populates="stock")
    quaterly_results = relationship("Quaterlyresult", back_populates="stock", cascade="all, delete")
    shareholdings = relationship("Shareholding", back_populates="stock", cascade="all, delete")
    
# EarningMetrics Table
class EarningMetric(Base):
    __tablename__ = "EarningMetrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    OperatingRevenue = Column(String)
    EBIT_cagr = Column(Float)
    EBITDA = Column(String)
    EBITDA_cagr = Column(Float)
    OperatingRevenue_Cagr = Column(Float)
    operatingMargins = Column(String)
    OperatingProfit = Column(String)
    epsTrailingTwelveMonths = Column(String)
    epsForward = Column(Float)
    NetIncome_cagr = Column(Float)
    FCFF_Cagr = Column(Float)
    NetIncome = Column(String)
    stock = relationship("Stock", back_populates="earning_metrics")

# Comparables Table
class Comparables(Base):
    __tablename__ = "Ratios"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    trailingPE = Column(Float)
    forwardPE = Column(Float)
    pricetoBook = Column(Float)
    TotalCommonSharesOutstanding = Column(String)
    pricetoFreeCashFlow = Column(Float)
    pricetoSales = Column(Float)
    DebttoEquity = Column(Float)
    trailingAnnualDividendYield = Column(Float)
    dividendYield = Column(Float)
    dividendRate = Column(Float)
    fiveYearAvgDividendYield = Column(Float)
    payoutRatio = Column(Float)
    stock = relationship("Stock", back_populates="comparables")

# Expenses Table
class Expenses(Base):
    __tablename__ = "Expenses"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    CapitalExpenditure_cagr = Column(Float)
    dividendPayoutratio = Column(Float)
    CapitalExpenditure = Column(String)
    InterestExpense_cagr = Column(Float)
    OperatingMargin = Column(String)
    CurrentDebt_cagr = Column(Float)
    EBIT = Column(String)
    Operating_Expense = Column(String)
    Intrest_Expense = Column(String)
    WACC = Column(Float, nullable=True)
    stock = relationship("Stock", back_populates="expenses")

# Financials Table
class Financials(Base):
    __tablename__ = "Financials"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    RetainedEarnings_cagr = Column(Float)
    RetainedEarnings = Column(String)
    UnusualExpense = Column(String)
    DepreciationAmortization = Column(String)
    WorkingCapital = Column(String)
    CashfromFinancingActivities = Column(String)
    CashfromInvestingActivities = Column(String)
    CashFromOperatingActivities = Column(String)
    TotalReceivablesNet = Column(String)
    TotalAssets = Column(String)
    FixedAssets = Column(String)
    TotalLiabilities = Column(String)
    TotalDebt = Column(String)
    stock = relationship("Stock", back_populates="financials")

# ValuationMetrics Table
class ValuationMetrics(Base):
    __tablename__ = "ValuationMetrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    ROE = Column(Float)
    FCFF = Column(String, nullable=True)
    ROA = Column(Float)
    ROIC = Column(Float)
    WACC = Column(Float)
    COD = Column(Float)
    ICR = Column(Float)
    stock = relationship("Stock", back_populates="metrics")

# Days Table
class Days(Base):
    __tablename__ = "Days"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    InventoryDays = Column(String)
    DebtorDays = Column(String)
    WorkingCapitalDays = Column(String)
    CashConversionCycle = Column(String)
    stock = relationship("Stock", back_populates="Days")

# Channels Table
class Channel(Base):
    __tablename__ = "Channels"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    ticker = Column(String, index=True)
    upper_channel_slope = Column(Float)
    upper_channel_intercept = Column(Float)
    period = Column(String, index=True)
    lower_channel_slope = Column(Float)
    lower_channel_intercept = Column(Float)
    stock = relationship("Stock", back_populates="channels")

# StockTechnicals Table
class StockTechnicals(Base):
    __tablename__ = "StockTechnicals"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    ticker = Column(String, index=True)
    period = Column(String, index=True)
    RsiSlope = Column(Float)
    CurrentSupport = Column(Float, nullable=True)
    CurrentResistance = Column(Float, nullable=True)
    VolumeUpperChannelSlope = Column(Float)
    VolumeLowerChannelSlope = Column(Float)
    VolumeUpperChannelIntercept = Column(Float)
    VolumeLowerChannelIntercept = Column(Float)
    CurrentRsi = Column(Float)
    Rsiintercept = Column(Float)
    stock = relationship("Stock", back_populates="technicals")

# PriceData Table
class PriceData(Base):
    __tablename__ = "PriceData"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    ticker = Column(String, index=True)
    date = Column(String, index=True)
    open_price = Column(Float)
    period = Column(String)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    RSI = Column(Float)
    OnbalanceVolume = Column(Float)
    stock = relationship("Stock", back_populates="pricedata")

# SupportData Table
class SupportData(Base):
    __tablename__ = "SupportData"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    Price = Column(Float)
    timestamp = Column(String)
    Pattern = Column(String)
    retests = Column(Integer)
    period = Column(String)
    stock = relationship("Stock", back_populates="support")



class Quaterlyresult(Base):
    __tablename__ = "QuaterlyResults"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    Date = Column(String, nullable=False, index=True)
    # Quarterly Columns
    Sales_Quaterly = Column(String, nullable=True)
    Expenses_Quaterly = Column(String, nullable=True)
    OperatingProfit_Quaterly = Column(String, nullable=True)
    EPS_in_Rs_Quaterly = Column(String, nullable=True)
    Profit_before_tax_Quaterly = Column(String, nullable=True)
    NetProfit_Quaterly = Column(String, nullable=True)
    Interest_Quaterly = Column(String, nullable=True)
    OPM_Percent_Quaterly = Column(String, nullable=True)
    Depreciation_Quaterly = Column(String, nullable=True)

    # Relationship with Stocks
    stock = relationship("Stock", back_populates="quaterly_results")


class Shareholding(Base):
    __tablename__ = "Shareholdings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
    Date = Column(String, nullable=False)  # The date when the data was updated
    Promoters = Column(String, nullable=True)  # Promoters' shareholding in percentage
    FIIs = Column(String, nullable=True)  # Foreign Institutional Investors' shareholding in percentage
    DIIs = Column(String, nullable=True)  # Domestic Institutional Investors' shareholding in percentage
    Public = Column(String, nullable=True)  # Public shareholding in percentage
    Government = Column(String, nullable=True)  # Government shareholding in percentage
    Others = Column(String, nullable=True)  # Other entities' shareholding in percentage
    ShareholdersCount = Column(String, nullable=True)  # Number of shareholders
    
    # Relationship back to Stock
    stock = relationship("Stock", back_populates="shareholdings")


# class Watchlist(Base):  
#     __tablename__ = "Watchlist"
#     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
#     user_id = Column(String, ForeignKey("Users.id"), nullable=False)
#     stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
#     stock = relationship("Stock", back_populates="watchlist")
#     user = relationship("User", back_populates="watchlist")


# class User(Base):
#     __tablename__ = "Users"
#     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
#     username = Column(String, unique=True, index=True)
#     password = Column(String)
#     name = Column(String, index=True)
#     email = Column(String, unique=True, index=True)
#     phonenumber = Column(String, unique=True, index=True)
#     watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete")
