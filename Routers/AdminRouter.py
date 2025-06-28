from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import *
from typing import List
from Database.Schemas.StockSchema import *
import math
import vectorbt as vbt
from datetime import datetime , timedelta
from fastapi import UploadFile
from Stock.Fundametals.Stock import *
from Stock.Technicals.StockChannels import CreateChannel
import pandas as pd
from Stock.Technicals.Meanreversion import CalculateVolumepeakmaxmin
from Stock.Technicals.rsiStrategy import CalculateRSI
import numpy as np 
from Stock.Technicals.SuppourtResistance import *
from Stock.Technicals.Meanreversion import * 
from datetime import timezone
from Routers.TechnicalRoutes import GetSupportResistance
from Stock.Fundametals.StockMetricCalculation import * 




router = APIRouter(prefix="/Admin", tags=["Admin"])

router = APIRouter()

# Assume get_db, Base, engine, and your models (Stock, EarningMetric, etc.) are already defined elsewhere


def get_scalar(val, ticker):
    if isinstance(val, pd.Series):
        # Try to get by ticker, else just take the first value
        return float(val.get(f"{ticker}.NS", val.get(f"{ticker}.BS", val.iloc[0])))
    return float(val)

def format_with_colon(dt):
        """Format datetime with a colon in the timezone offset and seconds set to 00."""
        return dt.strftime('%Y-%m-%d %H:%M:00%z')[:-2] + ':' + dt.strftime('%Y-%m-%d %H:%M:00%z')[-2:]


def safe_get_as_float(value, default=0.0):
    try:
        if value is None:
            return default
        # If value is list-like string, raise error here explicitly
        if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
            raise ValueError(f"Value looks like a list: {value}")
        return float(value)
    except Exception:
        return default


def safe_get_as_string(value, default=""):
    if value is None:
        return default
    return str(value)


def safe_get_value(value, default=0):
    """
    Safely retrieve a value, replacing NaN, None, or invalid data with a default value.
    """
    if pd.isna(value) or value is None:
        return default
    return value

# Helper functions

@router.post("/upload/")
async def upload_data(file: UploadFile, db: Session = Depends(get_db)):
    # Reset and initialize the database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error reading Excel file: {str(e)}"
        )

    for row_index, row in df.iterrows():
        operating_cashflow = convert_to_list(row.get("Cash from Operating Activity+"))

        interest_expense = convert_to_list(row.get("Interest"))
        
        tax_rate = convert_to_list(row.get("Tax %"))
        fixed_assets = convert_to_list(row.get("Fixed Assets+"))
        working_capital_days = convert_to_list(row.get("Working Capital Days"))
        revenue = convert_to_list(row.get("Sales+" , row.get("Revenue+")))
        print(tax_rate , interest_expense)
        equity_capital = convert_to_list(row.get("Equity Capital"))
        retained_earnings = convert_to_list(row.get("Reserves"))
        net_income = convert_to_list(row.get("Net Profit+"))
        total_assets = convert_to_list(row.get("Total Assets"))
        debt = convert_to_list(row.get("Borrowings+"))
        beta = safe_get_as_float(row.get("beta"), 1)
        roic = convert_to_list(row.get("ROIC %"))
        working_capital = calculate_working_capital_from_days(working_capital_days, revenue)
        capex , fcff = CalculateFCFF(operating_cashflow, interest_expense, tax_rate, fixed_assets, working_capital)
        wacc = CalculateWACC(CalculateCOE(beta), beta, debt, equity_capital, tax_rate)
        roe = CalculateROE(equity_capital, retained_earnings, net_income)
        atr = CalculateATR(total_assets, revenue)
        cod = CalculateCOI(interest_expense, debt)
        roic = CalculateROIC(roic)
        icr = CalculateICR(convert_to_list(row.get("Profit before tax")), interest_expense, tax_rate)
        # Create and add Stock
        print(row.get("Ticker") , fcff, working_capital, wacc, roe, atr, cod, icr)
        
        stock = Stock(
            id=str(uuid4()),
            Ticker=safe_get_as_string(row.get('Ticker')),
            CurrentPrice=safe_get_as_float(row.get("regularMarketPrice"), 0),
            marketCap=safe_get_as_float(row.get("Marketcap"), 0),
            CompanyName=safe_get_as_string(row.get("longName")),
            Description=row.get("longBusinessSummary", "N/A"),
            Industry=row.get("industry", "N/A"),
            FloatShares=row.get("floatShares", 0),
            sharesOutstanding=row.get("sharesOutstanding", 0),
            sector=safe_get_as_string(row.get("sector"), "Unknown"),
            beta=safe_get_as_float(row.get("beta"), 0),
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)

        # Add QuaterlyResults
        quaterly_results = Quaterlyresult(
            id=str(uuid4()),
            stock_id=stock.id,
            Date = row.get("Date_quarterly") ,
            ticker=stock.Ticker,
            Sales_Quaterly=row.get("Sales+_quaterly", row.get('Revenue+_quaterly')),
            Expenses_Quaterly=row.get("Expenses+_quaterly", "0"),
            OperatingProfit_Quaterly=row.get("Operating Profit_quaterly", "0"),
            EPS_in_Rs_Quaterly=row.get("EPS in Rs_quaterly", "0"),
            Profit_before_tax_Quaterly=row.get("Profit before tax_quaterly", "0"),
            NetProfit_Quaterly=row.get("Net Profit+_quaterly", "0"),
            Interest_Quaterly=row.get("Interest_quaterly", "0"),
            OPM_Percent_Quaterly=row.get("OPM %_quaterly", "0"),
            Depreciation_Quaterly=row.get("Depreciation_quaterly", "0"),
        )
        db.add(quaterly_results)

        # Add EarningMetric
        earning_metric = EarningMetric(
            id=str(uuid4()),
            stock_id=stock.id,
            Date = row.get("Date_profit_loss"),
            EBIT_cagr=safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Profit before tax"), 0))),
            EBITDA_cagr=safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Operating Profit"), 0))),
            EBITDA=safe_get_as_string(row.get("Operating Profit")),
            OperatingRevenue_Cagr= safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Sales+")))),
            OperatingRevenue=safe_get_as_string(row.get("Sales+")),
            OperatingProfit=safe_get_as_string(row.get("Operating Profit")),
            operatingMargins=safe_get_as_string(row.get("OPM %")),
            epsTrailingTwelveMonths=safe_get_as_string(
                row.get('EPS in Rs'), "0"
            ),
            epsForward=safe_get_value(calculate_growth_with_rolling(safe_get_as_string(
                row.get('EPS in Rs')
            ))),
            FCFF_Cagr=safe_get_value(calculate_growth_with_rolling(str(fcff))),
            NetIncome=safe_get_as_string(row.get("Net Profit+")),
            NetIncome_cagr= safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Net Profit+")))),
        )
        db.add(earning_metric)

        # Add Expenses
        expenses = Expenses(
            id=str(uuid4()),
            stock_id=stock.id,
            CurrentDebt_cagr=safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Borrowing+")))),
            CapitalExpenditure_cagr=safe_get_value(calculate_growth_with_rolling(capex)),
            CapitalExpenditure=capex,
            dividendPayoutratio=safe_get_as_string(row.get("Dividend Payout %"), 0),
            InterestExpense_cagr=safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Interest")))),
            EBIT=safe_get_as_string(row.get("Profit before tax")),
            TaxRate=safe_get_as_string(row.get("Tax %"), "0"),
            Intrest_Expense=safe_get_as_string(row.get("Interest"), "0"),
            Operating_Expense=safe_get_as_string(row.get("Expenses+"), "0"),
            WACC=safe_get_value(wacc)
        )
        db.add(expenses)

        # Add Financials
        financials = Financials(
            id=str(uuid4()),
            stock_id=stock.id,
            Date_BalanceSheet = row.get("Date_balance_sheet"),
            EquityCapital = safe_get_as_string(row.get("Equity Capital"), "0"),
            RetainedEarnings_cagr=safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Reserves")))) , 
            RetainedEarnings=safe_get_as_string(row.get("Reserves"), "0"),
            UnusualExpense=safe_get_as_string(row.get("Other Income+"), "0"),
            DepreciationAmortization=safe_get_as_string(row.get("Depreciation"), "0"),
            WorkingCapital=str(working_capital),
            Date_cashflow = row.get("Date_cash_flow"),
            CashfromFinancingActivities=safe_get_as_string(row.get("Cash from Financing Activity+"), "0"),
            CashfromInvestingActivities=safe_get_as_string(row.get("Cash from Investing Activity+"), "0"),
            CashFromOperatingActivities=safe_get_as_string(row.get("Cash from Operating Activity+"), "0"),
            TotalAssets=safe_get_as_string(row.get("Total Assets"), "0"),
            TotalReceivablesNet=safe_get_as_string(row.get("TotalLiabilities"), "0"),
            FixedAssets=safe_get_as_string(row.get("Fixed Assets+"), "0"),
            TotalLiabilities=safe_get_as_string(row.get("Total Liabilities"), "0"),
            TotalDebt=safe_get_as_string(row.get("Borrowings+"), "0"),
            ROCE = safe_get_as_string(row.get("ROCE %"), "0"),
        )
        db.add(financials)

        # Add ValuationMetrics
        metrics = ValuationMetrics(
            id=str(uuid4()),
            stock_id=stock.id,
            ROE=safe_get_value(roe),
            ROA=safe_get_value(atr),
            ROIC=safe_get_value(safe_get_as_string(row.get("ROCE %"), "0")),
            WACC=safe_get_value(wacc),
            COD=safe_get_value(cod),
            ICR=safe_get_value(icr),
            FCFF=str(fcff),
        )
        db.add(metrics)

        # Add Days
        days = Days(
            id=str(uuid4()),
            stock_id=stock.id,
            Date = row.get("Date_ratios"),
            InventoryDays=safe_get_as_string(row.get("Inventory Days"), "0"),
            DebtorDays=safe_get_as_string(row.get("Debtor Days"), "0"),
            DaysPayable = safe_get_as_string(row.get("Days Payable"), "0"),
            WorkingCapitalDays=safe_get_as_string(row.get("Working Capital Days"), "0"),
            CashConversionCycle=safe_get_as_string(row.get("Cash Conversion Cycle"), "0"),
        )
        db.add(days)

                # Add Shareholding
        shareholding = Shareholding(
            id=str(uuid4()),
            stock_id=stock.id,
            Date=row.get('Date_shareholding'),
            Promoters=safe_get_as_string(row.get("Promoters+"), 0),
            FIIs=safe_get_as_string(row.get("FIIs+"), 0),
            DIIs=safe_get_as_string(row.get("DIIs+"), 0),
            Public=safe_get_as_string(row.get("Public+"), 0),
            Government=safe_get_as_string(row.get("Government+"), 0),
            Others=safe_get_as_string(row.get('Others+'), 0),
            ShareholdersCount=row.get('No. of Shareholders'),
        )
        db.add(shareholding) 
        db.commit()

    return {"message": "Data uploaded successfully"}



@router.patch("/update_single/{ticker}")
def update_single_ticker(ticker: str, db: Session = Depends(get_db)):
    """
    Download and update price data for a single ticker.
    Only fetches and stores data after the stock's last updated timestamp.
    """
    import vectorbt as vbt
    import pandas as pd
    from datetime import datetime, timezone, timedelta

    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        return {"detail": f"Ticker {ticker} not found."}

    # Parse the updated field if present
    updated_time = None
    if stock.updated:
        try:
            updated_time = datetime.fromisoformat(stock.updated)
        except Exception:
            updated_time = None

    # Try NSE first, fallback to BSE
    data_daily = yf.download(f"{ticker}.NS", period="5y", interval="1d")
    data_min = yf.download(f"{ticker}.NS", period="5d", interval="1m")
    if data_daily.empty and data_min.empty:
        data_daily = yf.download(f"{ticker}.BS", period="5y", interval="1d")
        data_min = yf.download(f"{ticker}.BS", period="5d", interval="1m")
    if data_daily.empty and data_min.empty:
        return {"detail": f"No data available for ticker {ticker} (.NS or .BS)."}

    # Filter data after updated_time if available
    if updated_time:
        updated_time = pd.Timestamp(updated_time)
        # Remove timezone info from updated_time if your index is naive
        if updated_time.tzinfo is not None:
            updated_time = updated_time.tz_convert(None) if hasattr(updated_time, "tz_convert") else updated_time.tz_localize(None)
        # Ensure index is DatetimeIndex and timezone-naive
        if not isinstance(data_daily.index, pd.DatetimeIndex):
            data_daily.index = pd.to_datetime(data_daily.index)
        if not isinstance(data_min.index, pd.DatetimeIndex):
            data_min.index = pd.to_datetime(data_min.index)
        # Remove timezone info from index if present
        if data_daily.index.tz is not None:
            data_daily.index = data_daily.index.tz_localize(None)
        if data_min.index.tz is not None:
            data_min.index = data_min.index.tz_localize(None)
        data_daily = data_daily[data_daily.index > updated_time]
        data_min = data_min[data_min.index > updated_time]

    if data_daily.empty and data_min.empty:
        return {"detail": f"No new data to update for ticker {ticker}."}

    # Calculate indicators
    if not data_daily.empty:
        data_daily['RSI'] = vbt.RSI.run(data_daily['Close'], window=14, ewm=False).rsi
        data_daily['OBV'] = vbt.OBV.run(data_daily['Close'], data_daily['Volume']).obv
        data_daily = data_daily.dropna()
    if not data_min.empty:
        data_min['RSI'] = vbt.RSI.run(data_min['Close'], window=14, ewm=False).rsi
        data_min['OBV'] = vbt.OBV.run(data_min['Close'], data_min['Volume']).obv
        data_min = data_min.dropna()

    # Store daily data
    for date, row in data_daily.iterrows():
        existing_record = (
            db.query(PriceData)
            .filter(
                PriceData.ticker == ticker,
                PriceData.date == str(date),
                PriceData.period == "1d",
            )
            .first()
        )
        if not existing_record:
            db.add(PriceData(
                id=str(uuid4()),
                stock_id=stock.id,
                ticker=ticker,
                date=str(date),
                open_price=get_scalar(row["Open"], ticker),
                high_price=get_scalar(row["High"], ticker),
                low_price=get_scalar(row["Low"], ticker),
                close_price=get_scalar(row["Close"], ticker),
                RSI=get_scalar(row["RSI"], ticker),
                OnbalanceVolume=get_scalar(row["OBV"], ticker),
                volume=get_scalar(row["Volume"], ticker),
                period="1d",
            ))

    # Store minute data
    for timestamp, row in data_min.iterrows():
        existing_record = (
            db.query(PriceData)
            .filter(
                PriceData.ticker == ticker,
                PriceData.date == str(timestamp),
                PriceData.period == "1m",
            )
            .first()
        )
        if not existing_record:
            db.add(PriceData(
                id=str(uuid4()),
                stock_id=stock.id,
                ticker=ticker,
                date=str(timestamp),
                open_price=get_scalar(row["Open"], ticker),
                high_price=get_scalar(row["High"], ticker),
                low_price=get_scalar(row["Low"], ticker),
                close_price=get_scalar(row["Close"], ticker),
                RSI=get_scalar(row["RSI"], ticker),
                OnbalanceVolume=get_scalar(row["OBV"], ticker),
                volume=get_scalar(row["Volume"], ticker),
                period="1m",
            ))

    # Update stock's updated field and current price
    current_time = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    stock.updated = current_time.isoformat()
    if not data_min.empty:
        last_close = data_min["Close"].iloc[-1]
        if hasattr(last_close, "item"):
            stock.CurrentPrice = float(last_close.item())
        else:
            stock.CurrentPrice = float(last_close)
    elif not data_daily.empty:
        last_close = data_daily["Close"].iloc[-1]
        if hasattr(last_close, "item"):
            stock.CurrentPrice = float(last_close.item())
        else:
            stock.CurrentPrice = float(last_close)
    else:
        stock.CurrentPrice = 0

    db.commit()

    return {"detail": f"{ticker} updated successfully."}


@router.patch("/UpdateAllData/{ticker}" , response_model = dict)
def UpdateAllTechnicaldata(ticker ,db: Session = Depends(get_db) , timeinterval : int = 20 ) :
    #   datetime
    # stocks = db.query(Stock).all()[:]
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        # update  the current price as well  
        update_single_ticker(ticker , db)
        c1 = CreateVolumeChannel(db , stock.Ticker , period="1m") 
        c2 = CreateVolumeChannel(db , stock.Ticker , period="1d") 
    
        data_1d = GetSupportResistance(stock.Ticker , db , period = "1d")
        print(data_1d)
        data_1m = GetSupportResistance(stock.Ticker , db , period = "1m")

        technicals_1m = db.query(StockTechnicals).filter(StockTechnicals.ticker == stock.Ticker , StockTechnicals.period == "1m").first()
             
        technicals_1m.CurrentSupport = data_1m["Support"]
        technicals_1m.CurrentResistance = data_1m["Resistance"]


        technicals_1d = db.query(StockTechnicals).filter(StockTechnicals.ticker == stock.Ticker , StockTechnicals.period == "1d").first()
        technicals_1d.CurrentSupport = data_1d["Support"]
        technicals_1d.CurrentResistance = data_1d["Resistance"]

        channeldata = CreateChannel(db, stock.Ticker,timeinterval ,period="1m")             
        channeldata = CreateChannel(db, stock.Ticker,timeinterval ,period="1d")             
        
        Rsidata = CalculateRSI( stock.Ticker,db , period = "1m")
        Rsidata = CalculateRSI( stock.Ticker,db , period = "1d")


        return { "data1m" : data_1m  , 
            "data1d" : data_1d}



@router.post("/CreateCahnnels/{ticker}")
def CreateChannels(ticker: str, db: Session = Depends(get_db)):
    """
    Create channels, RSI, and volume channels for a single ticker.
    """
    print(ticker)
    channel_1m = CreateChannel(db, ticker, period="1m")
    channel_1d = CreateChannel(db, ticker, period="1d")

    CalculateRSI(ticker, db, period="1m")
    CalculateRSI(ticker, db, period="1d")

    CreateVolumeChannel(db, ticker, period="1m")
    CreateVolumeChannel(db, ticker, period="1d")
    return {"data_1m": channel_1m, "data_1d": channel_1d    }


@router.post("/AdminSuppourtResistance/{ticker}", response_model=dict)
def CreateSuppourtResistances(ticker: str, db: Session = Depends(get_db)):
    """
    Create strong support and resistance for a single ticker.
    """
    print(ticker)
    data_1d = MakeStrongSupportResistance(ticker, db, "1d")
    data_1m = MakeStrongSupportResistance(ticker, db, "1m")

    return {
        "data_1d": data_1d,
        "data_1m": data_1m
    }



@router.patch("/CreateSuppourtResistances/{ticker}")
def CreateNewLevels(ticker: str, db: Session = Depends(get_db)):
    print(ticker)

    # Create support and resistance for the 1d period
    data_1d = CreatepatternSuppourt(ticker, db, "1d")
    print(data_1d)
    technicaldata_1d = db.query(StockTechnicals).join(Stock).filter(
        Stock.Ticker == ticker, 
        StockTechnicals.period == "1d"
    ).first()

    if technicaldata_1d:
        technicaldata_1d.CurrentSupport = data_1d.get("Suppourt", None)
        technicaldata_1d.CurrentResistance = data_1d.get("Resistance", None)
    else:
        # Create a new record if it doesn't exist
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if stock:
            technicaldata_1d = StockTechnicals(
                stock_id=stock.id,
                ticker=ticker,
                period="1d",
                CurrentSupport=data_1d.get("Suppourt", None),
                CurrentResistance=data_1d.get("Resistance", None)
            )
            db.add(technicaldata_1d)

    # Create support and resistance for the 1m period
    data_1m = CreatepatternSuppourt(ticker, db, "1m")
    technicaldata_1m = db.query(StockTechnicals).join(Stock).filter(
        Stock.Ticker == ticker, 
        StockTechnicals.period == "1m"
    ).first()

    if technicaldata_1m:
        technicaldata_1m.CurrentSupport = data_1m.get("Suppourt", None)
        technicaldata_1m.CurrentResistance = data_1m.get("Resistance", None)
    else:
        # Create a new record if it doesn't exist
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if stock:
            technicaldata_1m = StockTechnicals(
                stock_id=stock.id,
                ticker=ticker,
                period="1m",
                CurrentSupport=data_1m.get("Suppourt", None),
                CurrentResistance=data_1m.get("Resistance", None)
            )
            db.add(technicaldata_1m)

    db.commit()

    CreateVolumeChannel(db, ticker, period="1m")
    CreateVolumeChannel(db, ticker, period="1d")

    return {
        "status": "Success",
        "message": f"Support and Resistance levels updated for {ticker}."
    }

     
     
