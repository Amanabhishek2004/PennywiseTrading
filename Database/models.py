from sqlalchemy import Column, String, ForeignKey, Integer, Float, BigInteger, Table , Boolean
from sqlalchemy.orm import relationship , backref
from Database.databaseconfig import *
from uuid import uuid4
import json
from sqlalchemy import event , text
from Stock.Technicals.SignalGenerator import * 
from datetime import datetime
from Stock.Technicals.SignalGenerator import GenrateSignals
from sqlalchemy import UniqueConstraint
# from Database.DataBaseSingnals.AlertSignal import create_alert_on_stock_update  # adjust import path as needed
# from .models import StockTechnicals  # or the model you want to listen to

# Register the event listener
# Utility function
def ConvertStringJsonTo_Array(string):
    try:
        return json.loads(string)
    except json.JSONDecodeError:
        print("Invalid JSON string")
        return []
# Association table for many-to-many relationship between User and Stock
watchlist_table = Table(
    "Watchlist",
    Base.metadata,
    Column("user_id", String, ForeignKey("Users.id", ondelete="CASCADE"), primary_key=True),
    Column("stock_id", String, ForeignKey("Stocks.id", ondelete="CASCADE"), primary_key=True), 
    Column("created_at", String, nullable=False, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
)

# Stocks Table
class Stock(Base):
    __tablename__ = "Stocks"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    Ticker = Column(String, unique=True, index=True)
    CurrentPrice = Column(Float, nullable=False, default=0)
    marketCap = Column(Float)
    pctChange = Column(Float , nullable=True )
    Description = Column(String)
    CompanyName = Column(String)
    FinancialScore = Column(Float, default=0.0) 
    TechnicalIntradayScore = Column(Float, default=0.0)
    TechnicalDailyScore = Column(Float, default=0.0)     
    sector = Column(String)
    beta = Column(Float)
    Industry = Column(String)
    updated = Column(String)
    FloatShares = Column(Float)
    sharesOutstanding = Column(Float)
    swingpoints = relationship("SwingPoints", back_populates="stock", cascade="all, delete")
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
    financial_scores = relationship("StockFinancialScore", back_populates="stock", cascade="all, delete")
    technical_scores = relationship("StockTechnicalScore", back_populates="stock", cascade="all, delete")
    
    users = relationship(
        "User",
        secondary=watchlist_table,
        back_populates="watchlist"
    )


class StockTechnicalScore(Base):
    __tablename__ = "StockTechnicalScores"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="CASCADE"), nullable=False)
    period = Column(String, nullable=False)  # e.g. '1d', '1m'
    CurrentRsi_score = Column(Float)
    RsiSlope_score = Column(Float)
    ResistanceProximity_score = Column(Float)
    SupportProximity_score = Column(Float)
    VolumeUpperChannelSlope_score = Column(Float)
    VolumeLowerChannelSlope_score = Column(Float)
    ChannelUpperSlope_score = Column(Float)
    ChannelLowerSlope_score = Column(Float)
    total_score = Column(Float)
    stock = relationship("Stock", back_populates="technical_scores")

class Subscription(Base):
    __tablename__ = "Subscription"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    subscriptiontype = Column(String, unique=True, nullable=False) 
    amount = Column(Integer, nullable=True)
    customertype = Column(String)
    description = Column(String, nullable=True)
    duration = Column(Integer)
    plans = relationship("Plan", back_populates="subscription")

class User(Base):
    __tablename__ = "Users"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    username = Column(String, unique=True, index=True)
    password = Column(String)
    reads = Column(Integer)
    referralCode = Column(String)
    points = Column(Integer , default= 0.0 )
    referred_by_id = Column(String, ForeignKey("Users.id"), nullable=True)    
    referredusers = relationship(
        "User",
        backref=backref("referred_by", remote_side=[id])
    )
    Dataused = Column(Float)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phonenumber = Column(String, unique=True, index=True)
    AuthToken = Column(String, unique=True, index=True)
    lastloggedin = Column(String , nullable = True) 
    Status = Column(Integer , default=0) 
    emailotp = Column(Integer)
    mobile_otp = Column(Integer , default = 0)
    watchlist = relationship(
        "Stock",
        secondary=watchlist_table,
        back_populates="users"
    )
    invoices = relationship("Invoices", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", cascade="all, delete-orphan")
    read_history = relationship("ReadHistory", back_populates="user", cascade="all, delete-orphan")
    apikey_usage = relationship("ApiKeyUsage", back_populates="user", cascade="all, delete-orphan")

class Plan(Base):
    __tablename__ = "Plans"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    plan_type = Column(String, ForeignKey("Subscription.subscriptiontype", ondelete="SET NULL"), nullable=True)
    timeperiod = Column(String)
    Price = Column(Integer)
    user_id = Column(String, ForeignKey("Users.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User", back_populates="plans")
    invoices = relationship("Invoices", back_populates="plan", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="plans")
    Expiry = Column(String , nullable = True) 

class Invoices(Base):
    __tablename__ = "Invoices"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("Users.id", ondelete="CASCADE"), nullable=True)
    plan_id = Column(String, ForeignKey("Plans.id", ondelete="SET NULL"), nullable=True)
    transaction_id = Column(String)
    user = relationship("User", back_populates="invoices")
    plan = relationship("Plan", back_populates="invoices")
    created_at = Column(String , nullable = True)

class ReadHistory(Base):
    __tablename__ = "ReadHistory"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("Users.id", ondelete="CASCADE"))
    reads = Column(Integer, default=0)
    date = Column(String, index=True)
    dataused = Column(Float, default=0.0)
    user = relationship("User", back_populates="read_history")

class ApiKeyUsage(Base):
    __tablename__ = "ApiKeyUsage"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("Users.id", ondelete="CASCADE"))
    apikey = Column(String, nullable=False)
    date = Column(String, index=True)
    purpose = Column(String)
    user = relationship("User", back_populates="apikey_usage")

class Alert(Base):
    __tablename__ = "Alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("Users.id", ondelete="CASCADE"), nullable=True)
    rsiPeakdivergence = Column(Boolean)
    Ticker = Column(String)
    Macross = Column(Float)
    lowerchannelSlope = Column(Float)
    upperchannelSlope = Column(Float)
    RsiSlope = Column(Float)
    time = Column(String)
    period = Column(String)
    tag = Column(String)
    user = relationship("User", back_populates="alerts")


class EarningMetric(Base):
    __tablename__ = "EarningMetrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    Date = Column(String)
    OperatingRevenue = Column(String)
    EBIT_cagr = Column(Float)
    RoeYearly = Column(String , nullable=True)
    EBITDA = Column(String)
    EBITDA_cagr = Column(Float)
    OperatingRevenue_Cagr = Column(Float)
    GrossProfit = Column(String , nullable=True)
    operatingMargins = Column(String)
    NetProfitMargin = Column(String , nullable=True)
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
    pricetoBook = Column(Float , default=0.0)
    pricetoFreeCashFlow = Column(Float)
    pricetoSales = Column(Float)
    DebttoEquity = Column(Float)
    dividendYield = Column(Float , default = 0.0)
    payoutRatio = Column(Float)
    medianpe = Column(Float) 
    FCFF_Yield = Column(Float)
    EV = Column(Float)
    EVEBITDA = Column(Float) 
    CurrentRatio = Column(Float)
    peg = Column(Float) 
    Avg_Sales_QoQ_Growth_Percent = Column(Float) 
    Avg_NetProfit_QoQ_Growth_Percent = Column(Float) 
    Avg_OperatingProfit_QoQ_Growth_Percent = Column(Float)
    Avg_EPS_QoQ_Growth_Percent = Column(Float) 
    stock = relationship("Stock", back_populates="comparables")
    
# Expenses Table
class Expenses(Base):
    __tablename__ = "Expenses"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    CapitalExpenditure_cagr = Column(Float)
    dividendPayoutratio = Column(String)
    TaxRate = Column(String)
    CapitalExpenditure = Column(String)
    InterestExpense_cagr = Column(Float)
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
    Date_BalanceSheet = Column(String)
    EquityCapital = Column(String)
    Date_cashflow = Column(String)
    RetainedEarnings = Column(String)
    UnusualExpense = Column(String)
    DepreciationAmortization = Column(String)
    OtherAssets = Column(String , nullable=True)
    OtherLiabilities = Column(String , nullable=True)
    WorkingCapital = Column(String)
    CashfromFinancingActivities = Column(String)
    CashfromInvestingActivities = Column(String)
    CashFromOperatingActivities = Column(String)
    TotalReceivablesNet = Column(String)
    TotalAssets = Column(String)
    FixedAssets = Column(String)
    TotalLiabilities = Column(String)
    TotalDebt = Column(String)
    ROCE = Column(String)
    stock = relationship("Stock", back_populates="financials")


class StockFinancialScore(Base):
    __tablename__ = "StockFinancialScores"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="CASCADE"), nullable=False)
    trailingPE_score = Column(Float)
    forwardPE_score = Column(Float)
    peg_score = Column(Float)
    EVEBITDA_score = Column(Float)
    medianpe_score = Column(Float)
    pricetoSales_score = Column(Float)
    pricetoFreeCashFlow_score = Column(Float)
    FCFF_Yield_score = Column(Float)
    CurrentRatio_score = Column(Float)
    DebttoEquity_score = Column(Float)
    Avg_Sales_QoQ_Growth_Percent_score = Column(Float)
    Avg_NetProfit_QoQ_Growth_Percent_score = Column(Float)
    Avg_OperatingProfit_QoQ_Growth_Percent_score = Column(Float)
    Avg_EPS_QoQ_Growth_Percent_score = Column(Float)
    EBIT_cagr_score = Column(Float)
    EBITDA_cagr_score = Column(Float)
    OperatingRevenue_Cagr_score = Column(Float)
    NetIncome_cagr_score = Column(Float)
    FCFF_Cagr_score = Column(Float)
    operatingMargins_score = Column(Float)
    epsTrailingTwelveMonths_score = Column(Float)
    epsForward_score = Column(Float)
    ROE_score = Column(Float)
    ROA_score = Column(Float)
    ROIC_score = Column(Float)
    WACC_score = Column(Float)
    COD_score = Column(Float)
    ICR_score = Column(Float)
    operatingExpense_score = Column(Float)
    Intrest_Expense_score = Column(Float)
    CurrentDebt_cagr_score = Column(Float)
    total_score = Column(Float)

    stock = relationship("Stock", back_populates="financial_scores")

# ValuationMetrics Table
class ValuationMetrics(Base):
    __tablename__ = "ValuationMetrics"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    ROE = Column(Float)
    FCFF = Column(String, nullable=True)
    ROA = Column(Float)
    ROIC = Column(String)
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
    Date = Column(String)
    WorkingCapitalDays = Column(String)
    DaysPayable  = Column(String)
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
    period = Column(String, index=True)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    RSI = Column(Float)
    OnbalanceVolume = Column(Float)
    stock = relationship("Stock", back_populates="pricedata")
    
    __table_args__ = (
        UniqueConstraint("ticker", "date", "period", name="unique_price_data"),
    )

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
    Sales_Quaterly = Column(String, nullable=True)
    Expenses_Quaterly = Column(String, nullable=True)
    OperatingProfit_Quaterly = Column(String, nullable=True)
    EPS_in_Rs_Quaterly = Column(String, nullable=True)
    Profit_before_tax_Quaterly = Column(String, nullable=True)
    NetProfit_Quaterly = Column(String, nullable=True)
    Interest_Quaterly = Column(String, nullable=True)
    OPM_Percent_Quaterly = Column(String, nullable=True)
    Depreciation_Quaterly = Column(String, nullable=True)
    stock = relationship("Stock", back_populates="quaterly_results")

class Shareholding(Base):
    __tablename__ = "Shareholdings"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    stock_id = Column(String, ForeignKey("Stocks.id"), nullable=False)
    Date = Column(String, nullable=False)
    Promoters = Column(String, nullable=True)
    FIIs = Column(String, nullable=True)
    DIIs = Column(String, nullable=True)
    Public = Column(String, nullable=True)
    Government = Column(String, nullable=True)
    Others = Column(String, nullable=True)
    ShareholdersCount = Column(String, nullable=True)
    stock = relationship("Stock", back_populates="shareholdings")

from sqlalchemy import Boolean



class SwingPoints(Base):
    __tablename__ = "SwingPoints"
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    pattern = Column(String)
    period = Column(String, index=True , nullable=True)
    time = Column(String)
    tag = Column(String)
    stock_id = Column(String, ForeignKey("Stocks.id", ondelete="SET NULL"), nullable=True)
    stock = relationship("Stock", back_populates="swingpoints")


def create_alert_on_stock_update(mapper, connection, target):
    if target.RsiSlope is None or target.CurrentRsi is None:
        return  # Skip if RSI values are missing

    session = SessionLocal()
    period = target.period

    channel = session.query(Channel).filter(Channel.stock_id == target.stock_id, Channel.period == period).first()
    signal = GenrateSignals(target.ticker, session, period)

    if not channel or not signal or "RSI Signal" not in signal or "RSI" not in signal["RSI Signal"]:
        session.close()
        return

    alert_cases = []

    # Strongbear
    if target.RsiSlope < 0  and target.CurrentRsi> 70 and channel.upper_channel_slope > 0:
        alert_cases.append({"tag": "Strongbear", "rsiPeakdivergence": True})

    # Strongbull
    if target.RsiSlope > 0 and signal["RSI Signal"].get("Rsi", 100) < 35 and channel.lower_channel_slope > 0:
        alert_cases.append({"tag": "Strongbull", "rsiPeakdivergence": True})

    # Bull
    if target.RsiSlope > 0 and channel.lower_channel_slope < 0:
        alert_cases.append({"tag": "bull", "rsiPeakdivergence": False})

    # Bearish
    if target.RsiSlope < 0 and channel.lower_channel_slope > 0:
        alert_cases.append({"tag": "bearish", "rsiPeakdivergence": False})

    price_data = session.query(PriceData).filter_by(stock_id=target.stock_id, period=period).order_by(PriceData.timestamp.desc()).first()
    if price_data:
        current_price = price_data.close
        # Threshold for proximity (e.g., 2% of support/resistance level)
        threshold = 0.002
        
        if (
            target.CurrentSupport
            and target.CurrentRsi <= 20
            and abs(current_price - target.CurrentSupport) / target.CurrentSupport <= threshold
        ):
            alert_cases.append({"tag": "Support Touch", "rsiPeakdivergence": False})
        
        if (
            target.CurrentResistance
            and target.CurrentRsi > 80
            and abs(current_price - target.CurrentResistance) / target.CurrentResistance <= threshold
        ):
            alert_cases.append({"tag": "Resistance Touch", "rsiPeakdivergence": False})


    for case in alert_cases:
        sql = text("""
            INSERT INTO "Alerts" (
                id, user_id, "Ticker", time, "RsiSlope", "lowerchannelSlope", "upperchannelSlope",
                "rsiPeakdivergence", tag, period
            )
            SELECT
                :id, w.user_id, :ticker, :time, :rsislope, :lower, :upper, :peak, :tag, :period
            FROM "Watchlist" w
            WHERE w.stock_id = :stock_id
            AND NOT EXISTS (
                SELECT 1 FROM "Alerts" a
                WHERE a.user_id = w.user_id
                AND a."Ticker" = :ticker
                AND a."lowerchannelSlope" = :lower
                AND a."upperchannelSlope" = :upper
                AND a."rsiPeakdivergence" = :peak
                AND a.tag = :tag
                AND a.period = :period
                AND a.time::date = :date
            )
        """)
        session.execute(
            sql,
            {
                "id": str(uuid4()),
                "ticker": target.ticker,
                "time": str(datetime.now()),
                "rsislope": target.RsiSlope,
                "lower": channel.lower_channel_slope,
                "upper": channel.upper_channel_slope,
                "peak": case["rsiPeakdivergence"],
                "stock_id": target.stock_id,
                "date": str(datetime.today().date()),
                "tag": case["tag"],
                "period": period
            }
        )

    session.commit()
    session.close()

event.listen(StockTechnicals, "after_update", create_alert_on_stock_update)


from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import event
from sqlalchemy.orm import Session

def schedule_channel_updates(session, flush_context):
    for obj in session.new:
        if isinstance(obj, PriceData):
            print("New PriceData detected:", obj.ticker, flush=True)
             
            from Backend.Stock.Technicals.StockChannels import CreateChannel
            from Stock.Technicals.SuppourtResistance import MakeStrongSupportResistance, CreatepatternSuppourt

            def run_tasks():
                print("running updates...", flush=True)
                with SessionLocal() as async_session:
                    with ThreadPoolExecutor(max_workers=6) as executor:
                        executor.submit(CreateVolumeChannel, obj.ticker, "1m")
                        executor.submit(CreateVolumeChannel, obj.ticker, "1d")
                        executor.submit(MakeStrongSupportResistance, obj.ticker, async_session, "1d")
                        executor.submit(MakeStrongSupportResistance, obj.ticker, async_session, "1m")
                        executor.submit(CreatepatternSuppourt, obj.ticker, async_session, "1d")
                        executor.submit(CreatepatternSuppourt, obj.ticker, async_session, "1m")
                        executor.submit(CreateChannel, async_session, obj.ticker, 20, "1m")
                        executor.submit(CreateChannel, async_session, obj.ticker, 20, "1d")
                        executor.submit(CalculateRSI, obj.ticker, async_session, "1m")
                        executor.submit(CalculateRSI, obj.ticker, async_session, "1d")

            session.info.setdefault("after_commit_tasks", []).append(run_tasks)

def run_after_commit(session):
    tasks = session.info.pop("after_commit_tasks", [])
    for task in tasks:
        task()

# Attach listeners to SessionLocal
event.listen(SessionLocal, "after_flush", schedule_channel_updates)
event.listen(SessionLocal, "after_commit", run_after_commit)





def create_alert_on_swingpoint_insert(mapper, connection, target):
    session = SessionLocal()

    try:
        # Only trigger for divergence patterns
        if target.pattern not in ["BearishDivergencePattern", "BullishDivergencePattern"]:
            return

        stock = session.query(Stock).filter(Stock.id == target.stock_id).first()
        if not stock:
            return

        technical_data = session.query(StockTechnicals).filter(
            StockTechnicals.period == target.period, 
            StockTechnicals.stock_id == stock.id
        ).first()

        channel_data = session.query(Channel).filter(
            Channel.stock_id == stock.id,
            Channel.period == target.period
        ).first()

        sql = text("""
            INSERT INTO "Alerts" (
                id,
                user_id,
                "Ticker",
                time,
                tag,
                "rsiPeakdivergence",
                "RsiSlope",
                "lowerchannelSlope",
                "upperchannelSlope",
                period
            )
            SELECT
                :id,
                w.user_id,
                :ticker,
                :time,
                :tag,
                :rsiPeakdivergence,
                :RsiSlope,
                :lowerchannelSlope,
                :upperchannelSlope,
                :period
            FROM "Watchlist" w
            WHERE w.stock_id = :stock_id
              AND NOT EXISTS (
                SELECT 1 FROM "Alerts" a
                WHERE a.user_id = w.user_id
                  AND a."Ticker" = :ticker
                  AND a.tag = :tag
                  AND a."rsiPeakdivergence" = :rsiPeakdivergence
                  AND a."RsiSlope" IS NOT DISTINCT FROM :RsiSlope
                  AND a."lowerchannelSlope" IS NOT DISTINCT FROM :lowerchannelSlope
                  AND a."upperchannelSlope" IS NOT DISTINCT FROM :upperchannelSlope
                  AND a.period = :period
                  AND a.time::date = :date
              )
        """)

        session.execute(sql, {
            "id": str(uuid4()),
            "ticker": stock.Ticker,
            "time": str(target.time),
            "tag": target.pattern,
            "rsiPeakdivergence": (
                technical_data.RsiSlope * channel_data.lower_channel_slope < 0
                if technical_data and channel_data else False
            ),
            "RsiSlope": technical_data.RsiSlope if technical_data else None,
            "lowerchannelSlope": channel_data.lower_channel_slope if channel_data else None,
            "upperchannelSlope": channel_data.upper_channel_slope if channel_data else None,
            "period": target.period if hasattr(target, "period") else "30m",
            "stock_id": target.stock_id,
            "date": str(datetime.now())
        })

        session.commit()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()



# Attach listener
event.listen(SwingPoints, "after_insert", create_alert_on_swingpoint_insert)


