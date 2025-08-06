from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import *
from typing import List
from Database.Schemas.StockSchema import *
from fastapi import UploadFile
from Stock.Technicals.StockChannels import CreateChannel
import pandas as pd
from Stock.Technicals.Meanreversion import CalculateVolumepeakmaxmin
from Stock.Technicals.rsiStrategy import CalculateRSI
import numpy as np 
from Stock.Technicals.SuppourtResistance import *
from Stock.Technicals.Meanreversion import * 
from datetime import timezone

from Stock.Fundametals.StockMetricCalculation import * 
from Routers.UserAccountRoutes import get_current_user , verify_premium_access
from Stock.Fundametals.StockComparables import * 
from Stock.Fundametals.StockForwardRatios import  *



router = APIRouter(prefix="/Admin", tags=["Admin"] , dependencies= [Depends(verify_premium_access)])


# Assume get_db, Base, engine, and your models (Stock, EarningMetric, etc.) are already defined elsewhere


def get_scalar(val, ticker):
    if isinstance(val, pd.Series):
        # Try to get by ticker, else just take the first value
        return float(val.get(f"{ticker}.NS", val.get(f"{ticker}.BS", val.iloc[0])))
    return float(val)

def format_with_colon(dt):
    import pandas as pd
    dt = pd.Timestamp(dt)
    if dt.tzinfo is None:
        dt = dt.tz_localize("Asia/Kolkata")
    else:
        dt = dt.tz_convert("Asia/Kolkata")
    # Format with colon in offset
    s = dt.strftime('%Y-%m-%d %H:%M:00%z')
    return s[:-2] + ':' + s[-2:]

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
# 260 , 901
# 890 

import math
from uuid import uuid4
from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd


def safe_column(row, primary_key: str, fallback_key: str):
    val = row.get(primary_key)
    if val is not None and not (isinstance(val, float) and math.isnan(val)):
        return val
    return row.get(fallback_key)


@router.post("/upload/")
async def upload_data(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading Excel file: {str(e)}")

    for row_index, row in df[1400 : ].iterrows():
        banking = row.get("industry") == "Banks - Regional" or row.get("sector") == "Financial Services"
        ticker = safe_get_as_string(row.get('Ticker'))

        existing_stock = db.query(Stock).filter(Stock.Ticker == ticker).first()

        if existing_stock:
            stock = existing_stock
        else:
            stock = Stock(id=str(uuid4()), Ticker=ticker)
            db.add(stock)

        # Update stock fields
        stock.CurrentPrice = safe_get_as_float(row.get("regularMarketPrice"), 0)
        stock.marketCap = safe_get_as_float(row.get("regularMarketPrice") * row.get("sharesOutstanding", 0), 0)
        stock.CompanyName = safe_get_as_string(row.get("longName"))
        stock.Description = row.get("longBusinessSummary", "N/A")
        stock.Industry = row.get("industry", "N/A")
        stock.FloatShares = row.get("floatShares", 0)
        stock.sharesOutstanding = row.get("sharesOutstanding", 0)
        stock.sector = safe_get_as_string(row.get("sector"), "Unknown")
        stock.beta = safe_get_as_float(row.get("beta"), 0)

        db.commit()
        db.refresh(stock)

        # Delete existing related records
        db.query(Quaterlyresult).filter_by(stock_id=stock.id).delete()
        db.query(EarningMetric).filter_by(stock_id=stock.id).delete()
        db.query(Expenses).filter_by(stock_id=stock.id).delete()
        db.query(Financials).filter_by(stock_id=stock.id).delete()
        db.query(ValuationMetrics).filter_by(stock_id=stock.id).delete()
        db.query(Days).filter_by(stock_id=stock.id).delete()
        db.query(Shareholding).filter_by(stock_id=stock.id).delete()
        db.commit()

        operating_cashflow = convert_to_list(safe_column(row, "Cash from Operating Activity+", "Cash from Operating Activity"))
        interest_expense = convert_to_list(safe_column(row, "Interest", "Interest"))
        tax_rate = convert_to_list(safe_column(row, "Tax %", "Tax %"))
        fixed_assets = convert_to_list(safe_column(row, "Fixed Assets+", "Fixed Assets"))
        working_capital_days = convert_to_list(safe_column(row, "Working Capital Days", "Working Capital Days"))
        revenue = convert_to_list(safe_column(row, "Sales+", "Sales")) if not banking else convert_to_list(safe_column(row, "Revenue+", "Revenue"))
        equity_capital = convert_to_list(safe_column(row, "Equity Capital", "Equity Capital"))
        retained_earnings = convert_to_list(safe_column(row, "Reserves+", "Reserves"))
        net_income = convert_to_list(safe_column(row, "Net Profit+", "Net Profit"))
        total_assets = convert_to_list(safe_column(row, "Total Assets", "Total Assets"))
        debt = convert_to_list(safe_column(row, "Borrowings+", "Borrowings"))

        beta = safe_get_as_float(row.get("beta"), 1)
        roic_list = convert_to_list(safe_column(row, "ROIC %", "ROIC %"))

        working_capital = calculate_working_capital_from_days(working_capital_days, revenue)
        capex, fcff = CalculateFCFF(operating_cashflow, interest_expense, tax_rate, fixed_assets, working_capital)
        wacc = CalculateWACC(CalculateCOE(beta), beta, debt, equity_capital, tax_rate)
        roe = CalculateROE(equity_capital, retained_earnings, net_income)
        atr = CalculateATR(total_assets, revenue)
        cod = CalculateCOI(interest_expense, debt)
        roic = CalculateROIC(roic_list)
        icr = CalculateICR(convert_to_list(safe_column(row, "Profit before tax", "Profit before tax")), interest_expense)

        db.add(Quaterlyresult(
            id=str(uuid4()),
            stock_id=stock.id,
            Date=row.get("Date_quarterly"),
            ticker=stock.Ticker,
            Sales_Quaterly=safe_column(row, "Sales+_quaterly", "Sales_quaterly") if not banking else safe_column(row, 'Revenue+_quaterly', 'Revenue_quaterly'),
            Expenses_Quaterly=safe_column(row, "Expenses+_quaterly", "Expenses_quaterly"),
            OperatingProfit_Quaterly=safe_column(row, "Operating Profit_quaterly", "Operating Profit_quaterly") if not banking else safe_column(row, 'Financing Profit_quaterly', 'Financing Profit_quaterly'),
            EPS_in_Rs_Quaterly=row.get("EPS in Rs_quaterly", "0"),
            Profit_before_tax_Quaterly=row.get("Profit before tax_quaterly", "0"),
            NetProfit_Quaterly=safe_column(row, "Net Profit+_quaterly", "Net Profit_quaterly"),
            Interest_Quaterly=row.get("Interest_quaterly", "0"),
            OPM_Percent_Quaterly=row.get("OPM %_quaterly", "0") if not banking else row.get("Financing Margin %_quaterly"),
            Depreciation_Quaterly=row.get("Depreciation_quaterly", "0"),
        ))

        db.add(EarningMetric(
            id=str(uuid4()),
            stock_id=stock.id,
            Date=str(row.get("Date_profit_loss")),
            EBIT_cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Profit before tax"), 0)))),
            EBITDA_cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(safe_column(row, "Operating Profit", "Operating Profit"), 0)))),
            EBITDA=safe_get_as_string(safe_column(row, "Operating Profit", "Operating Profit") if not banking else safe_column(row, "Financing Profit", "Financing Profit")),
            OperatingRevenue_Cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(safe_column(row, "Sales+", "Sales") if not banking else safe_column(row, "Revenue+", "Revenue"))))),
            OperatingRevenue=safe_get_as_string(safe_column(row, "Sales+", "Sales") if not banking else safe_column(row, "Revenue+", "Revenue")),
            OperatingProfit=safe_get_as_string(safe_column(row, "Operating Profit", "Operating Profit") if not banking else safe_column(row, "Financing Profit", "Financing Profit")),
            operatingMargins=safe_get_as_string(safe_column(row, "OPM %", "OPM %") if not banking else safe_column(row, "Financing Margin %", "Financing Margin %")),
            epsTrailingTwelveMonths=safe_get_as_string(row.get('EPS in Rs'), "0"),
            epsForward=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get('EPS in Rs'))))),
            FCFF_Cagr=float(safe_get_value(calculate_growth_with_rolling(str(fcff)))),
            NetIncome=safe_get_as_string(safe_column(row, "Net Profit+", "Net Profit")),
            NetIncome_cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(safe_column(row, "Net Profit+", "Net Profit"))))),
        ))

        db.add(Expenses(
            id=str(uuid4()),
            stock_id=stock.id,
            CurrentDebt_cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Borrowing+"))))),
            CapitalExpenditure_cagr=float(safe_get_value(calculate_growth_with_rolling(capex))),
            CapitalExpenditure=str(capex),
            dividendPayoutratio=safe_get_as_string(row.get("Dividend Payout %"), 0),
            InterestExpense_cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(row.get("Interest"))))),
            EBIT=safe_get_as_string(row.get("Profit before tax")),
            TaxRate=safe_get_as_string(row.get("Tax %"), "0"),
            Intrest_Expense=safe_get_as_string(row.get("Interest"), "0"),
            Operating_Expense=safe_get_as_string(row.get("Expenses+"), "0"),
            WACC=float(safe_get_value(wacc))
        ))

        db.add(Financials(
            id=str(uuid4()),
            stock_id=stock.id,
            Date_BalanceSheet=row.get("Date_balance_sheet"),
            EquityCapital=safe_get_as_string(safe_column(row, "Equity Capital", "Equity Capital"), "0"),
            RetainedEarnings_cagr=float(safe_get_value(calculate_growth_with_rolling(safe_get_as_string(safe_column(row, "Reserves+", "Reserves"))))),
            RetainedEarnings=safe_get_as_string(safe_column(row, "Reserves+", "Reserves"), "0"),
            UnusualExpense=safe_get_as_string(safe_column(row, "Other Income+", "Other Income"), "0"),
            DepreciationAmortization=safe_get_as_string(row.get("Depreciation"), "0"),
            WorkingCapital=str(working_capital),
            Date_cashflow=row.get("Date_cash_flow"),
            CashfromFinancingActivities=safe_get_as_string(safe_column(row, "Cash from Financing Activity+", "Cash from Financing Activity"), "0"),
            CashfromInvestingActivities=safe_get_as_string(safe_column(row, "Cash from Investing Activity+", "Cash from Investing Activity"), "0"),
            CashFromOperatingActivities=safe_get_as_string(safe_column(row, "Cash from Operating Activity+", "Cash from Operating Activity"), "0"),
            TotalAssets=safe_get_as_string(row.get("Total Assets"), "0"),
            TotalReceivablesNet=safe_get_as_string(row.get("TotalLiabilities"), "0"),
            FixedAssets=safe_get_as_string(safe_column(row, "Fixed Assets+", "Fixed Assets"), "0"),
            TotalLiabilities=safe_get_as_string(row.get("Total Liabilities"), "0"),
            TotalDebt=safe_get_as_string(safe_column(row, "Borrowings+", "Borrowings"), "0"),
            ROCE=safe_get_as_string(row.get("ROCE %"), "0"),
        ))

        db.add(ValuationMetrics(
            id=str(uuid4()),
            stock_id=stock.id,
            ROE=float(safe_get_value(roe)),
            ROA=float(safe_get_value(atr)),
            ROIC=safe_get_value(safe_get_as_string(row.get("ROCE %"), "0")),
            WACC=float(safe_get_value(wacc)),
            COD=float(safe_get_value(cod)),
            ICR=float(safe_get_value(icr)),
            FCFF=str(fcff),
        ))

        db.add(Days(
            id=str(uuid4()),
            stock_id=stock.id,
            Date=row.get("Date_ratios"),
            InventoryDays=safe_get_as_string(row.get("Inventory Days"), "0"),
            DebtorDays=safe_get_as_string(row.get("Debtor Days"), "0"),
            DaysPayable=safe_get_as_string(row.get("Days Payable"), "0"),
            WorkingCapitalDays=safe_get_as_string(row.get("Working Capital Days"), "0"),
            CashConversionCycle=safe_get_as_string(row.get("Cash Conversion Cycle"), "0"),
        ))

        db.add(Shareholding(
            id=str(uuid4()),
            stock_id=stock.id,
            Date=row.get('Date_shareholding'),
            Promoters=safe_get_as_string(safe_column(row, "Promoters+", "Promoters"), 0),
            FIIs=safe_get_as_string(safe_column(row, "FIIs+", "FIIs"), 0),
            DIIs=safe_get_as_string(safe_column(row, "DIIs+", "DIIs"), 0),
            Public=safe_get_as_string(safe_column(row, "Public+", "Public"), 0),
            Government=safe_get_as_string(safe_column(row, "Government+", "Government"), 0),
            Others=safe_get_as_string(safe_column(row, 'Others+', 'Others'), 0),
            ShareholdersCount=row.get('No. of Shareholders'),
        ))
        print(f"{ticker} updated")
        db.commit()
        update_comparables(stock, db)

    return {"message": "Data uploaded and updated successfully."}



@router.patch("/update_single/{ticker}")
def update_single_ticker(ticker: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import vectorbt as vbt
    import pandas as pd
    from datetime import datetime, timezone, timedelta
    import yfinance as yf
    from uuid import uuid4

    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        return {"detail": f"Ticker {ticker} not found."}

    stock_data = yf.Ticker(f"{ticker}.NS")
    updated_time = None
    if stock.updated:
        try:
            updated_time = datetime.fromisoformat(stock.updated)
            if updated_time.tzinfo is None:
                # Make it timezone-aware if it's naive
                updated_time = updated_time.replace(tzinfo=timezone.utc)
        except Exception:
            updated_time = None
    else:
        updated_time = None

    if updated_time:
        start_dt = updated_time
    else:
        start_dt = datetime.now(timezone.utc) - timedelta(days=8)

    raw_end_dt = start_dt + timedelta(days=8)
    now = datetime.now(timezone.utc)
    end_dt = min(raw_end_dt, now)

    start_str = start_dt.strftime('%Y-%m-%d')
    end_str = end_dt.strftime('%Y-%m-%d') 

    print(start_str , end_str)
    
    data_daily = stock_data.history(period="10y", interval="1d")
    data_min = stock_data.history(period = "8d", interval="5m")
    print(data_min)
    def fetch_last_14(ticker, period):
        rows = db.query(PriceData).filter(
            PriceData.ticker == ticker,
            PriceData.period == period
        ).order_by(PriceData.date.desc()).limit(14).all()
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame([{
            'Open': r.open_price,
            'High': r.high_price,
            'Low': r.low_price,
            'Close': r.close_price,
            'Volume': r.volume,
            'date': r.date
        } for r in rows])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df.sort_index()

    prev_daily = fetch_last_14(ticker, "1d")
    prev_min = fetch_last_14(ticker, "1m")

    if not prev_daily.empty:
        data_daily = pd.concat([prev_daily, data_daily])
        data_daily = data_daily[~data_daily.index.duplicated(keep='last')]
    if not prev_min.empty:
        data_min = pd.concat([prev_min, data_min])
        data_min = data_min[~data_min.index.duplicated(keep='last')]

    if not data_daily.empty:
        data_daily['RSI'] = vbt.RSI.run(data_daily['Close'], window=14).rsi
        data_daily['OBV'] = vbt.OBV.run(data_daily['Close'], data_daily['Volume']).obv
        data_daily = data_daily.dropna()
    if not data_min.empty:
        data_min['RSI'] = vbt.RSI.run(data_min['Close'], window=14).rsi
        data_min['OBV'] = vbt.OBV.run(data_min['Close'], data_min['Volume']).obv
        data_min = data_min.dropna()

    if updated_time:
        updated_time = pd.Timestamp(updated_time)
        if updated_time.tzinfo is not None:
            updated_time = updated_time.tz_convert(None) if hasattr(updated_time, "tz_convert") else updated_time.tz_localize(None)
        for df in [data_daily, data_min]:
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
        data_daily = data_daily[data_daily.index > updated_time]
        data_min = data_min[data_min.index > updated_time]

    if not data_daily.empty and not data_min.empty:
        for date, row in data_daily.iterrows():
            date_str = format_with_colon(date)
            existing_record = (
                db.query(PriceData)
                .filter(
                    PriceData.ticker == ticker,
                    PriceData.date == date_str,
                    PriceData.period == "1d",
                ).first()
            )
            if not existing_record:
                db.add(PriceData(
                    id=str(uuid4()),
                    stock_id=stock.id,
                    ticker=ticker,
                    date=date_str,
                    open_price=get_scalar(row["Open"], ticker),
                    high_price=get_scalar(row["High"], ticker),
                    low_price=get_scalar(row["Low"], ticker),
                    close_price=get_scalar(row["Close"], ticker),
                    RSI=get_scalar(row["RSI"], ticker),
                    OnbalanceVolume=get_scalar(row["OBV"], ticker),
                    volume=get_scalar(row["Volume"], ticker),
                    period="1d",
                ))

        for timestamp, row in data_min.iterrows():
            timestamp_str = format_with_colon(timestamp)
            existing_record = (
                db.query(PriceData)
                .filter(
                    PriceData.ticker == ticker,
                    PriceData.date == timestamp_str,
                    PriceData.period == "1m",
                ).first()
            )
            if not existing_record:
                db.add(PriceData(
                    id=str(uuid4()),
                    stock_id=stock.id,
                    ticker=ticker,
                    date=timestamp_str,
                    open_price=get_scalar(row["Open"], ticker),
                    high_price=get_scalar(row["High"], ticker),
                    low_price=get_scalar(row["Low"], ticker),
                    close_price=get_scalar(row["Close"], ticker),
                    RSI=get_scalar(row["RSI"], ticker),
                    OnbalanceVolume=get_scalar(row["OBV"], ticker),
                    volume=get_scalar(row["Volume"], ticker),
                    period="1m",
                ))
    db.commit()

    end_dt_with_tz = end_dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
    stock.updated = end_dt_with_tz.isoformat()
    
    last_close_row = db.query(PriceData.close_price).filter(
        PriceData.ticker == ticker,
        PriceData.period == "1d"
    ).order_by(PriceData.date.desc()).offset(1).limit(1).first()

    last_close = last_close_row[0] if last_close_row else None
    print(f"Last close for {ticker}: {last_close}")
    current_price = db.query(PriceData).filter(
        PriceData.ticker == ticker,
        PriceData.period == "1m"
    ).order_by(PriceData.date.desc()).first()
    percent_change =  100*(current_price.close_price - last_close )/ last_close if last_close else None
     
    

    return {
        "detail": f"{ticker} updated successfully.",
        "latest_price": current_price.close_price,
        "percent_change": round(percent_change, 2) if percent_change is not None else None
    }



@router.patch("/UpdateAllData/{ticker}" , response_model = dict)
def UpdateAllTechnicaldata(ticker ,db: Session = Depends(get_db) , timeinterval : int = 20 , current_user: User = Depends(get_current_user) ) :
    #   datetime
    # stocks = db.query(Stock).all()[:]
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        # update  the current price as well  
        pricingdata = update_single_ticker(ticker , db)
        
        # c1 = CreateVolumeChannel(db , stock.Ticker , period="1m")
        # c2 = CreateVolumeChannel(db , stock.Ticker , period="1d") 


        # data_1d = MakeStrongSupportResistance(stock.Ticker , db , period = "1d" )
        # data_1m = MakeStrongSupportResistance(stock.Ticker , db , period = "1m")
        

        # data_1d = CreatepatternSuppourt(stock.Ticker , db , period = "1d" )
        # data_1m = CreatepatternSuppourt(stock.Ticker , db , period = "1m")
 
        # channeldata = CreateChannel(db, stock.Ticker,timeinterval ,period="1m")             
        # channeldata = CreateChannel(db, stock.Ticker,timeinterval ,period="1d")             


        # Rsidata = CalculateRSI( stock.Ticker,db , period = "1m")
        # Rsidata = CalculateRSI( stock.Ticker,db , period = "1d")


        return pricingdata



@router.patch("/CreateSuppourtResistances/{ticker}")
def CreateNewLevels(ticker: str, db: Session = Depends(get_db) , current_user: User = Depends(get_current_user)):

    # Create support and resistance for the 1d period
    data_1d = CreatepatternSuppourt(ticker, db, "1d")
    technicaldata_1d = db.query(StockTechnicals).join(Stock).filter(
        Stock.Ticker == ticker, 
        StockTechnicals.period == "1d"
    ).first()
    if technicaldata_1d:
        technicaldata_1d.CurrentSupport = data_1d.get("Suppourt", None)
        technicaldata_1d.CurrentResistance = data_1d.get("Resistance", None)
    else:
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

    # Create support and resistance for the 30m period
  
    db.commit()

    CreateVolumeChannel(db, ticker, period="1m")
    CreateVolumeChannel(db, ticker, period="1d")


    return {
        "status": "Success",
        "message": f"Support and Resistance levels updated for {ticker}."
    }


def update_comparables(stock, db):
    # Step 1: Calculate ratios from annual + quarterly data
    ratios = calculate_ratios_from_annual_data(stock)
    if "error" in ratios:
        return {"error": "Cannot calculate base ratios."}

    # Step 2: Calculate PEG and Median PE using historical prices
    price_ratios = CalculateMedianpe(stock.Ticker, db)
    if "error" in price_ratios:
        return {"error": "Cannot calculate PEG/MedianPE from price data."}
    forwardpe = calculate_forward_pe(stock.Ticker ,db)
    # Step 3: Combine all ratio data
    combined_ratios = {
        "trailingPE": ratios.get("PE"),
        "forwardPE": float(forwardpe.get("FPE" , None)),
        "pricetoBook": 0.0,
        "pricetoFreeCashFlow": ratios.get("Price_to_Cashflow"),
        "pricetoSales": ratios.get("PS"),
        "DebttoEquity": ratios.get("DebtToEquity"),
        "dividendYield": getattr(stock.earning_metrics[0], "dividendYield", 0.0) if stock.earning_metrics else 0.0,
        "payoutRatio": getattr(stock.earning_metrics[0], "PayoutRatio", None) if stock.earning_metrics else None,
        "medianpe": price_ratios.get("MedianPE"),
        "peg": price_ratios.get("PEG"),
        "FCFF_Yield": ratios.get("FCFF_Yield"),
        "EV": ratios.get("EV"),
        "EVEBITDA": ratios.get("EV/EBITDA"),
        "CurrentRatio": ratios.get("CurrentRatio"),
        "Avg_Sales_QoQ_Growth_Percent": ratios.get("Avg_Sales_QoQ_Growth_Percent"),
        "Avg_NetProfit_QoQ_Growth_Percent": ratios.get("Avg_NetProfit_QoQ_Growth_Percent"),
        "Avg_OperatingProfit_QoQ_Growth_Percent": ratios.get("Avg_OperatingProfit_QoQ_Growth_Percent"),
        "Avg_EPS_QoQ_Growth_Percent": ratios.get("Avg_EPS_QoQ_Growth_Percent"),
        "stock_id": stock.id
    }
    
    print(combined_ratios)
    # Step 4: Check if Comparables already exist and update it; otherwise create new
    existing = db.query(Comparables).filter(Comparables.stock_id == stock.id).first()
    if existing:
        for key, value in combined_ratios.items():
            setattr(existing, key, value)
    else:
        new_ratios = Comparables(**combined_ratios)
        db.add(new_ratios)

    db.commit()
    return {"message": "Comparables updated successfully."}


@router.post("/update/comparables/{ticker}")
def update_comparables_by_ticker(ticker: str, db: Session = Depends(get_db) ):
    STOCK = db.query(Stock).filter(Stock.Ticker == ticker).first()
    result = update_comparables(STOCK, db)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {"message": f"Comparables updated for {ticker}"}
