from sqlalchemy import Column, String, ForeignKey, Integer, Float, BigInteger
from sqlalchemy.orm import relationship
from Database.databaseconfig import Base
from uuid import uuid4
 
 # Stocks Table
import json
 
 
def ConverStringJsonTo_Array(string):
     try:
         # Convert JSON string to Python list
         return json.loads(string)
     except json.JSONDecodeError:
         # Handle invalid JSON string
         print("Invalid JSON string")
         return []
 
 
class Stock(Base):
 
     __tablename__ = "Stocks"
     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
     Ticker = Column(String, unique=True, index=True)
     CurrentPrice = Column(Integer, nullable=False, default="0")
     marketCap = Column(BigInteger)
     twoHundredDayAverage = Column(Integer)
     fiftyDayAverage = Column(Integer)
     grossProfits = Column(Float)
     sector = Column(String)
     beta = Column(Float)
 
     # Relationships
     earning_metrics = relationship(
         "EarningMetric", back_populates="stock", cascade="all, delete"
     )
     comparables = relationship(
         "Comparables", back_populates="stock", cascade="all, delete"
     )
     expenses = relationship("Expenses", back_populates="stock", cascade="all, delete")
     financials = relationship(
         "Financials", back_populates="stock", cascade="all, delete"
     )
     metrics = relationship(
         "ValuationMetrics", back_populates="stock", cascade="all, delete"
     )
 
 
 # EarningMetrics Table
class EarningMetric(Base):
     __tablename__ = "EarningMetrics"
 
     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
     stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
     OperatingRevenue = Column(String)
     EBIT_cagr = Column(Float)
     EBITDA_cagr = Column(Float)
     OperatingRevenue_Cagr = Column(Float)
     BasicEps_Cagr = Column(Float)
     operatingMargins = Column(Float)
     grossMargins = Column(Float)
     epsTrailingTwelveMonths = Column(Float)
     epsForward = Column(Float)
     FreeCashFlow_cagr = Column(Float)
     NetIncomeFromContinuingOperations_cagr = Column(Float)
     NetIncome_cagr = Column(Float)
     stock = relationship("Stock", back_populates="earning_metrics")
 
 
 # Comparables Table
class Comparables(Base):
     __tablename__ = "Ratios"
 
     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
     stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
     trailingPE = Column(Float)
     forwardPE = Column(Float)
     pricetoBook = Column(Float)
     pricetoFreeCashFlow = Column(Float)
     pricetoSales = Column(Float)
     DebttoEquity = Column(Float)
     trailingAnnualDividendYield = Column(Float)
     dividendYield = Column(Float)
     dividendRate = Column(Float)
     fiveYearAvgDividendYield = Column(Float)
     payoutRatio = Column(Float)
 
     # Relationship to Stock
     stock = relationship("Stock", back_populates="comparables")
 
 
 # Expenses Table
class Expenses(Base):
     __tablename__ = "Expenses"
 
     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
     stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
     # OperatingCashFlow = Column(String)
     CurrentDebt_cagr = Column(Float)
     CapitalExpenditure_cagr = Column(Float)
     # InterestExpense_Cagr = Column(String)
     InterestExpense_cagr = Column(Float)
     Operating_Expense = Column(String)
     Intrest_Expense = Column(String)
     TotalExpenses_cagr = Column(Float)
     WACC = Column(Float, nullable=True)
     InterestExpense_cagr = Column(String, nullable=True)
     # Relationship to Stock
     stock = relationship("Stock", back_populates="expenses")
 
 
 # Financials Table
class Financials(Base):
     __tablename__ = "Financials"
 
     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
     stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
     NetTangibleAssets_cagr = Column(Float)
     InvestedCapital = Column(String)
     InvestedCapital_cagr = Column(Float)
     RetainedEarnings_cagr = Column(Float)
     TotalAssets = Column(String)
     TaxRateForCalcs = Column(String)
 
     stock = relationship("Stock", back_populates="financials")
 
 
class ValuationMetrics(Base):
     __tablename__ = "ValuationMetrics"
 
     id = Column(String, primary_key=True, default=lambda: str(uuid4()))
     stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
     ROE = Column(Float)
     FCFF = Column(String , nullable= True)
     ROA = Column(Float)
     ROIC = Column(Float)
     WACC = Column(Float)
     COD = Column(Float)
     ICR = Column(Float)
     EFF = Column(Float)
     ATR = Column(Float)
     stock = relationship("Stock", back_populates="metrics")