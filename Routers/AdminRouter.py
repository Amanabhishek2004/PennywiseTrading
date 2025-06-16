from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import *
from typing import List
from Database.Schemas.StockSchema import *
import math
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



router = APIRouter(prefix="/Admin", tags=["Admin"])

router = APIRouter()

# Assume get_db, Base, engine, and your models (Stock, EarningMetric, etc.) are already defined elsewhere

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
        # Create and add Stock
        stock = Stock(
            id=str(uuid4()),
            Ticker=safe_get_as_string(row.get("ticker")),
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
            Date = row.get("Date_Quaterly", "0") ,
            ticker=stock.Ticker,
            Sales_Quaterly=row.get("Sales+_Quaterly", "0"),
            Expenses_Quaterly=row.get("Expenses+_Quaterly", "0"),
            OperatingProfit_Quaterly=row.get("Operating Profit_Quaterly", "0"),
            EPS_in_Rs_Quaterly=row.get("EPS in Rs_Quaterly", "0"),
            Profit_before_tax_Quaterly=row.get("Profit before tax_Quaterly", "0"),
            NetProfit_Quaterly=row.get("Net Profit+_Quaterly", "0"),
            Interest_Quaterly=row.get("Interest_Quaterly", "0"),
            OPM_Percent_Quaterly=row.get("OPM %_Quaterly", "0"),
            Depreciation_Quaterly=row.get("Depreciation_Quaterly", "0"),
        )
        db.add(quaterly_results)

        # Add EarningMetric
        earning_metric = EarningMetric(
            id=str(uuid4()),
            stock_id=stock.id,
            EBIT_cagr=safe_get_as_float(row.get("EBIT_growth"), 0),
            EBITDA_cagr=safe_get_as_float(row.get("EBITDA_growth"), 0),
            EBITDA=safe_get_as_string(row.get("EBITDA")),
            OperatingRevenue_Cagr=safe_get_as_float(row.get("OperatingRevenue_growth"), 0),
            OperatingRevenue=safe_get_as_string(row.get("OperatingRevenue")),
            OperatingProfit=safe_get_as_string(row.get("OperatingProfit")),
            operatingMargins=safe_get_as_string(row.get("OperatingMargin")),
            epsTrailingTwelveMonths=safe_get_as_string(
                row.get("epsTrailingTwelveMonths"), "0"
            ),
            epsForward=safe_get_as_float(row.get("epsTrailingTwelveMonths_growth"), 0),
            FCFF_Cagr=safe_get_as_float(row.get("FCFF_growth"), 0),
            NetIncome=safe_get_as_string(row.get("NetIncome")),
            NetIncome_cagr=safe_get_as_float(row.get("NetIncome_growth"), 0),
        )
        db.add(earning_metric)

        # Add Expenses
        expenses = Expenses(
            id=str(uuid4()),
            stock_id=stock.id,
            CurrentDebt_cagr=safe_get_as_float(row.get("TotalDebt_growth"), 0),
            CapitalExpenditure_cagr=safe_get_as_float(row.get("CAPEX_growth"), 0),
            CapitalExpenditure=safe_get_as_string(row.get("CAPEX")),
            dividendPayoutratio=safe_get_as_float(row.get("DividendPayoutratio"), 0),
            InterestExpense_cagr=safe_get_as_float(row.get("Interest_Expense_growth"), 0),
            EBIT=safe_get_as_string(row.get("EBIT"), "0"),
            Intrest_Expense=safe_get_as_string(row.get("Interest_Expense"), "0"),
            Operating_Expense=safe_get_as_string(row.get("Operating_Expense"), "0"),
            WACC=safe_get_as_float(row.get("COD"), 0),
        )
        db.add(expenses)

        # Add Financials
        financials = Financials(
            id=str(uuid4()),
            stock_id=stock.id,
            RetainedEarnings_cagr=safe_get_as_float(row.get("RetainedEarnings_growth"), 0),
            RetainedEarnings=safe_get_as_string(row.get("RetainedEarnings"), "0"),
            UnusualExpense=safe_get_as_string(row.get("UnusualExpense"), "0"),
            DepreciationAmortization=safe_get_as_string(row.get("DepreciationAmortization"), "0"),
            WorkingCapital=safe_get_as_string(row.get("WorkingCapital"), "0"),
            CashfromFinancingActivities=safe_get_as_string(row.get("CashfromFinancingActivities"), "0"),
            CashfromInvestingActivities=safe_get_as_string(row.get("CashfromInvestingActivityies"), "0"),
            CashFromOperatingActivities=safe_get_as_string(row.get("CashFromOperatingActivities"), "0"),
            TotalAssets=safe_get_as_string(row.get("TotalAssets"), "0"),
            TotalReceivablesNet=safe_get_as_string(row.get("TotalLiabilities"), "0"),
            FixedAssets=safe_get_as_string(row.get("FixedAssets"), "0"),
            TotalLiabilities=safe_get_as_string(row.get("TotalLiabilities"), "0"),
            TotalDebt=safe_get_as_string(row.get("TotalDebt"), "0"),
        )
        db.add(financials)

        # Add ValuationMetrics
        metrics = ValuationMetrics(
            id=str(uuid4()),
            stock_id=stock.id,
            ROE=safe_get_as_float(row.get("ROE"), 0),
            ROA=safe_get_as_float(row.get("ROA"), 0),
            ROIC=safe_get_as_float(row.get("ReturnOnCapitalEmployed"), 0),
            WACC=safe_get_as_float(row.get("COD"), 0),
            COD=safe_get_as_float(row.get("COD"), 0),
            ICR=safe_get_as_float(row.get("ICR"), 0),
            FCFF=safe_get_as_string(row.get("FCFF"), "0"),
        )
        db.add(metrics)

        # Add Days
        days = Days(
            id=str(uuid4()),
            stock_id=stock.id,
            InventoryDays=safe_get_as_string(row.get("InventoryDays"), "0"),
            DebtorDays=safe_get_as_string(row.get("DebtorDays"), "0"),
            WorkingCapitalDays=safe_get_as_string(row.get("WorkingCapitalDays"), "0"),
            CashConversionCycle=safe_get_as_string(row.get("CashConversionCycle"), "0"),
        )
        db.add(days)

                # Add Shareholding
        shareholding = Shareholding(
            id=str(uuid4()),
            stock_id=stock.id,
            Date=row.get("Date"),
            Promoters=safe_get_as_string(row.get("Promoters+"), 0),
            FIIs=safe_get_as_string(row.get("FIIs+"), 0),
            DIIs=safe_get_as_string(row.get("DIIs+"), 0),
            Public=safe_get_as_string(row.get("Public+"), 0),
            Government=safe_get_as_string(row.get("Government+"), 0),
            Others=safe_get_as_string(row.get('Others+'), 0),
            ShareholdersCount=(row.get('No. of Shareholders'), 0),
        )
        db.add(shareholding) 
        db.commit()

    return {"message": "Data uploaded successfully"}



import yfinance as yf


from datetime import datetime, timezone, timedelta

@router.patch("/update/")
def update_data(db: Session = Depends(get_db)):
    """
    Update the technicals and price data for the given tickers, including RSI and OBV.
    """
    stocks = db.query(Stock).all()
    count = 0
    for stock in stocks:
        ticker = stock.Ticker
        count += 1
        try:
            # Parse stock.updated string into a datetime object
            updated_time = datetime.fromisoformat(stock.updated) if stock.updated else None

            # Get the current time in the desired timezone (IST)
            current_time = datetime.now(timezone(timedelta(hours=5, minutes=30)))

            # Fetch stock data from yfinance
            data_daily = yf.Ticker(f"{ticker}.NS").history(period="5y", interval="1d")
            data_min = yf.Ticker(f"{ticker}.NS").history(period="5d", interval="1m")
            if data_daily.empty and data_min.empty:
                print(f"No data available for ticker {ticker}, skipping...")
                continue

            # Filter data if updated_time is available
            if updated_time:
                data_daily = data_daily[data_daily.index > updated_time]
                data_min = data_min[data_min.index > updated_time]

            if data_daily.empty and data_min.empty:
                print(f"No new data to update for ticker {ticker}")
                continue

            # Calculate RSI and OBV
            data_daily["RSI"] = (
                    (data_daily["Close"])
                    .rolling(window=14)
                    .apply(
                        lambda x: (
                            100
                            - (100 / (1 + (x.diff().where(x > 0).mean() /
                                        abs(x.diff().where(x < 0).mean()))))
                        )
                    )
                )

            data_min["RSI"] = (
                    (data_daily["Close"])
                    .rolling(window=14)
                    .apply(
                        lambda x: (
                            100
                            - (100 / (1 + (x.diff().where(x > 0).mean() /
                                        abs(x.diff().where(x < 0).mean()))))
                        )
                    )
                )

            data_daily["OBV"] = np.cumsum(
                np.where(
                    data_daily["Open"] > data_daily["Close"],
                    data_daily["Volume"] , 
                    -data_daily["Volume"]
                )
            )
            data_min["OBV"] = np.cumsum(
                np.where(
                    data_min["Open"] > data_min["Close"],
                    data_min["Volume"] , 
                    -data_min["Volume"]
                )
            )

            data_daily.dropna(inplace=True)
            data_min.dropna(inplace=True)

            # Update or create records...
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
                    new_price_data = PriceData(
                        id=str(uuid4()),
                        stock_id=stock.id,
                        ticker=ticker,
                        date=str(date),
                        open_price=row["Open"],
                        high_price=row["High"],
                        low_price=row["Low"],
                        close_price=row["Close"],
                        RSI=row["RSI"],
                        OnbalanceVolume=row["OBV"],
                        volume=row["Volume"],
                        period="1d",
                    )
                    db.add(new_price_data)

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
                    new_price_data = PriceData(
                        id=str(uuid4()),
                        stock_id=stock.id,
                        ticker=ticker,
                        date=str(timestamp),
                        open_price=row["Open"],
                        high_price=row["High"],
                        low_price=row["Low"],
                        close_price=row["Close"],
                        RSI=row["RSI"],
                        OnbalanceVolume=row["OBV"],
                        volume=row["Volume"],
                        period="1m",
                    )
                    db.add(new_price_data)

            # Update stock's updated field and current price
            stock.updated = current_time.isoformat()
            stock.CurrentPrice = data_daily.iloc[-1]["Close"] if not data_daily.empty else None

            db.commit()

        except Exception as e:
            db.rollback()
            print(f"Error updating data for ticker {ticker}: {str(e)}")
            continue

    return {"detail": "Data updated successfully"}




@router.patch("/UpdateAllData/" , response_model = dict)
def UpdateAllTechnicaldata(db: Session = Depends(get_db) , timeinterval : int = 20 ) :
    #   datetime
    # stocks = db.query(Stock).all()[:]
    stocks = db.query(Stock)
    for stock in stocks :
         
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

        channeldata = CreateChannel(stock.Ticker , db ,timeinterval ,period="1m")             

        Rsidata = CalculateRSI(stock.Ticker , db , period = "1m")

    return { "data1m" : data_1m  , 
            "data1d" : data_1d}




@router.post("/CreateCahnnels/")
def CreateChannels(db: Session = Depends(get_db) ) :
    Tickers = ["THOMASCOOK"]
    for ticker in Tickers:
        # ticker = ticker[0]
        print(ticker)
        CreateChannel(db ,ticker , period="1m" )
        CreateChannel(db , ticker , period="1d")
 
        CalculateRSI(ticker , db , period="1m" )
        CalculateRSI(ticker ,db , period="1d" )
        
        CreateVolumeChannel(db , ticker , period="1m")
        CreateVolumeChannel(db , ticker , period="1d")
    return {"Detail" : "Success"}  



@router.post("/AdminSuppourtResistance" , response_model=dict )
def CreateSuppourtResistances( db: Session = Depends(get_db) ):
    Tickers =["THOMASCOOK"]
    for ticker in Tickers:
        # ticker = ticker[0]
        print(ticker)
        data_1d = MakeStrongSupportResistance(ticker , db , "1d")
        data_1m = MakeStrongSupportResistance(ticker , db , "1m")

    return {"data_1d" : data_1d ,  
            "data_1m" : data_1m}



@router.patch("/CreateSuppourtResistances/")
def CreateNewLevels(db: Session = Depends(get_db)):
    # Tickers = db.query(Stock.Ticker).all()[:1]
    Tickers =["THOMASCOOK"]
    
    print(Tickers)
    for ticker in Tickers:
        # ticker = ticker[0]
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

        CreateVolumeChannel(db , ticker , period="1m")
        CreateVolumeChannel(db , ticker , period="1d")


    return {
        "status": "Success",
        "message": "Support and Resistance levels updated for all tickers."
    }

     
     
