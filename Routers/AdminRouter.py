from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import *
from typing import List
from Database.Schemas.StockSchema import *
from fastapi import UploadFile
from Stock.Technicals.StockChannels import CreateChannel , CreateLowerChannel , CreateUpperChannel
import pandas as pd
from Stock.Technicals.Meanreversion import CalculateVolumepeakmaxmin
from Stock.Technicals.rsiStrategy import CalculateRSI , CreateTrendline
import numpy as np 
from Stock.Technicals.SuppourtResistance import *
from Stock.Technicals.Meanreversion import * 
from datetime import timezone
from Stock.Fundametals.StockMetricCalculation import * 
from Routers.UserAccountRoutes import get_current_user , verify_premium_access
from Stock.Fundametals.StockComparables import * 
from Stock.Fundametals.StockForwardRatios import  *


router = APIRouter(prefix="/Admin", tags=["Admin"]   , 
                   dependencies= [Depends(verify_premium_access)])


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

    for row_index, row in df[1099:].iterrows():
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
        revenue = convert_to_list(safe_column(row, "Sales+", "Sales")) if not banking else convert_to_list(safe_column(row, "Revenue+", "Revenue"))
        equity_capital = convert_to_list(safe_column(row, "Equity Capital", "Equity Capital"))
        retained_earnings = convert_to_list(safe_column(row, "Reserves+", "Reserves"))
        net_income = convert_to_list(safe_column(row, "Net Profit+", "Net Profit"))
        total_assets = convert_to_list(safe_column(row, "Total Assets", "Total Assets"))
        otherassets = convert_to_list(safe_column(row, "Other Assets+", "Other Assets"))
        receivabledays = convert_to_list(safe_column(row, "Debtor Days", "Debtor Days"))
        total_liabilities = convert_to_list(safe_column(row, "Total Liabilities", "Total Liabilities"))
        debt = convert_to_list(safe_column(row, "Borrowings+", "Borrowings"))
        operatingprofit = convert_to_list(safe_column(row, "Operating Profit", "Operating Profit")) if not banking else convert_to_list(safe_column(row, "Financing Profit", "Financing Profit"))
        beta = safe_get_as_float(row.get("beta"), 1)
        roic_list = convert_to_list(safe_column(row, "ROIC %", "ROIC %"))
        expense = convert_to_list(safe_column(row, "Expenses+", "Expenses"))
        working_capital = calculate_working_capital(total_liabilities , total_debt=debt , current_assets=otherassets )
        total_receivables = calculate_receivables_from_days(
            receivabledays, revenue
        )
        grossmargin =calculate_gross_margin_array(revenue , operating_profit=operatingprofit  , operating_expenses = expense)
        netmargin = calculate_net_profit_margin_array(revenue , net_income)
        capex, fcff = CalculateFCFF(operating_cashflow, interest_expense, tax_rate, fixed_assets, working_capital)
        wacc = CalculateWACC(CalculateCOE(beta), beta, debt, equity_capital, tax_rate)
        roe  , roe_yearly = CalculateROE(equity_capital, retained_earnings, net_income)
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
            RoeYearly = str(roe_yearly) if roe_yearly else "0", 
            GrossProfit = safe_get_as_string(grossmargin), 
            NetProfitMargin = safe_get_as_string(netmargin),    
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
            OtherAssets=safe_get_as_string(safe_column(row, "Other Assets+", "Other Assets"), "0"),
            OtherLiabilities=safe_get_as_string(safe_column(row, "Other Liabilities+", "Other Liabilities"), "0"),
            TotalAssets=safe_get_as_string(row.get("Total Assets"), "0"),
            TotalReceivablesNet=safe_get_as_string(total_receivables, "0"),
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



from supabase import create_client, Client
from datetime import datetime, timezone, timedelta
import pandas as pd
import yfinance as yf
import vectorbt as vbt
from uuid import uuid4

# --- Supabase Client ---
SUPABASE_URL = "https://uitfyfywxzaczubnecft.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVpdGZ5Znl3eHphY3p1Ym5lY2Z0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTQ1MjMzNiwiZXhwIjoyMDY3MDI4MzM2fQ.yjZ6UsGzO4F6VyU0q_HSUVrekFr9XGHazN9cd61nOZ8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Helper Functions ---
def fetch_last_14_supabase(ticker, period):
    """Fetch last 14 records for given ticker and period from Supabase."""
    rows = (
        supabase.table("PriceData")
        .select("open_price, high_price, low_price, close_price, volume, date")
        .eq("ticker", ticker)
        .eq("period", period)
        .order("date", desc=True)
        .limit(14)
        .execute()
    )

    if not rows.data:
        return pd.DataFrame()

    df = pd.DataFrame(rows.data)

    # Normalize all date strings before parsing
    df['date'] = df['date'].apply(normalize_datetime_string)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df.rename(
        {
            "open_price": "Open",
            "high_price": "High",
            "low_price": "Low",
            "close_price": "Close",
            "volume": "Volume"
        },
        axis=1,
        inplace=True
    )

    df.set_index('date', inplace=True)

    print(df)
    return df.sort_index()

def format_with_colon(dt):
    """Ensure datetime is in ISO format with colon in offset."""
    return dt.isoformat()

def get_scalar(value):
    """Convert NumPy or Pandas scalar to Python type."""
    try:
        return value.item()
    except:
        return float(value)

def to_float(val):
    return float(get_scalar(val))

def to_int(val):
    return int(get_scalar(val))

# --- Main Function ---
from datetime import datetime, timedelta, timezone
import pandas as pd
import yfinance as yf
from uuid import uuid4
import vectorbt as vbt

# --- Helper function to normalize datetime strings ---
def normalize_datetime_string(dt_str: str) -> str:

    s = str(dt_str).strip()
    if " " in s and "+" in s:
        date_part, tz_part = s.rsplit("+", 1)
        tz_part = tz_part.strip()
        if len(tz_part) == 2:  # convert +00 to +0000
            tz_part += "00"
        s = date_part.replace(" ", "T") + "+" + tz_part
    return s


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  


import pandas as pd
import numpy as np
import vectorbt as vbt
import yfinance as yf
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi import Depends
# from Database import get_db
from Database.models import PriceData
# Import your own helpers: fetch_last_14_supabase, CreateChannel, CalculateRSI, CreateVolumeChannel, supabase, normalize_datetime_string


import pandas as pd

def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize dataframe to have 'date' column instead of DateTimeIndex."""
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    # Handle yfinance intraday (Datetime) and daily (Date)
    if "Datetime" in df.columns:
        df.rename(columns={"Datetime": "date"}, inplace=True)
    elif "Date" in df.columns:
        df.rename(columns={"Date": "date"}, inplace=True)

    # Fallback only if still missing
    if "date" not in df.columns:
        df["date"] = df.index

    # Ensure proper datetime with timezone awareness
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)

    return df

def update_single_ticker_supabase(ticker: str, db):
    # 1. Fetch stock from Supabase
    stock_data = supabase.table("Stocks").select("*").eq("Ticker", ticker).single().execute()
    if not stock_data.data:
        return {"detail": f"Ticker {ticker} not found."}
    stock = stock_data.data

    # 2. Get last updated time
    safe_time_str = normalize_datetime_string(stock.get("updated", None))
    updated_time = pd.Timestamp(safe_time_str, tz="UTC") if safe_time_str else None

    # 3. Determine time window
    start_dt = updated_time if updated_time else datetime.now(timezone.utc) - timedelta(days=9)
    raw_end_dt = start_dt + timedelta(days=9)
    if raw_end_dt.tzinfo is None:
        raw_end_dt = raw_end_dt.replace(tzinfo=timezone.utc)

    # 4. Fetch Yahoo Finance data
    stock_yf = yf.Ticker(f"{ticker}.NS")
    data_daily = prepare_df(stock_yf.history(period="5y", interval="1d"))
    data_min = prepare_df(stock_yf.history(start=start_dt.date(), period="8d", interval="5m"))

    # 5. Fetch last 14 rows from DB
    prev_daily = prepare_df(fetch_last_14_supabase(ticker, "1d"))
    prev_min = prepare_df(fetch_last_14_supabase(ticker, "1m"))

    # 6. Combine historical + new data
    data_for_technical1d = pd.concat([prev_daily, data_daily]).drop_duplicates(subset=["date"], keep="last").sort_values("date")
    data_for_technical1m = pd.concat([prev_min, data_min]).drop_duplicates(subset=["date"], keep="last").sort_values("date")

    # 7. Add RSI & OBV
    if not data_for_technical1d.empty:
        data_for_technical1d["RSI"] = vbt.RSI.run(data_for_technical1d["Close"], window=14).rsi
        data_for_technical1d["OBV"] = vbt.OBV.run(data_for_technical1d["Close"], data_for_technical1d["Volume"]).obv
        data_for_technical1d.dropna(inplace=True)

    if not data_for_technical1m.empty:
        data_for_technical1m["RSI"] = vbt.RSI.run(data_for_technical1m["Close"], window=14).rsi
        data_for_technical1m["OBV"] = vbt.OBV.run(data_for_technical1m["Close"], data_for_technical1m["Volume"]).obv
        data_for_technical1m.dropna(inplace=True)

    # 8. Rename OHLCV columns to match DB
    rename_map = {
        "Open": "open_price",
        "High": "high_price",
        "Low": "low_price",
        "Close": "close_price",
        "Volume": "volume",
        "RSI": "RSI",
        "OBV": "OnbalanceVolume",
    }
    data_for_technical1d.rename(columns=rename_map, inplace=True)
    data_for_technical1m.rename(columns=rename_map, inplace=True)

    # 9. Filter by last updated time
    if updated_time:
        data_for_technical1d = data_for_technical1d.loc[data_for_technical1d["date"] > updated_time]
        data_for_technical1m = data_for_technical1m.loc[data_for_technical1m["date"] > updated_time]
    channels_1m = CreateChannel(db, data_for_technical1d, ticker, timeperiod=20, period="1d")
    channels_1d = CreateChannel(db, data_for_technical1m, ticker, timeperiod=20, period="1m")
    CreatepatternSuppourt(data_for_technical1d , ticker , db , period= "1d" , channel=channels_1d)
    CreatepatternSuppourt(data_for_technical1d , ticker , db , period= "1m" , channel=channels_1m)
    MakeStrongSupportResistance(ticker , db , period="1m" , prices = data_for_technical1m.to_dict()) 
    MakeStrongSupportResistance(ticker , db , period = "1d" , prices = data_for_technical1d.to_dict())
    CalculateRSI(ticker, db, "1m", data_for_technical1d, data_for_technical1m["RSI"])
    CalculateRSI(ticker, db, "1d", data_for_technical1m, data_for_technical1d["RSI"])
    CreateVolumeChannel(ticker = ticker, data = data_for_technical1m, period = "1m")
    CreateVolumeChannel(ticker=ticker, data = data_for_technical1d, period = "1d") 


    def build_rows(df, period):
        rows = []
        for _, row in df.iterrows():
            rows.append(
                {
                    "id": str(uuid4()),
                    "stock_id": stock["id"],
                    "ticker": ticker,
                    "date": row["date"].isoformat().replace("T", " "),
                    "open_price": float(row["open_price"]),
                    "high_price": float(row["high_price"]),
                    "low_price": float(row["low_price"]),
                    "close_price": float(row["close_price"]),
                    "RSI": float(row["RSI"]),
                    "OnbalanceVolume": float(row["OnbalanceVolume"]),
                    "volume": int(row["volume"]),
                    "period": period,
                }
            )
        return rows

    price_rows = []
    if not data_daily.empty:
        price_rows.extend(build_rows(data_for_technical1d, "1d"))
    if not data_min.empty:
        price_rows.extend(build_rows(data_for_technical1m, "1m"))

    # 10. Upsert into Supabase
    if price_rows:
        print(f"Upserting {len(price_rows)} rows for {ticker}")
        supabase.table("PriceData").upsert(price_rows, on_conflict="ticker,date,period").execute()

    # 11. Update Stocks.updated with latest 1m candle
    last_1m_time = data_min["date"].iloc[-1] if not data_min.empty else None
 
    # 12. Fetch last close and current price
    last_close_row = (
        supabase.table("PriceData")
        .select("close_price")
        .eq("ticker", ticker)
        .eq("period", "1d")
        .order("date", desc=True)
        .range(1, 1)
        .execute()
    )
    last_close = last_close_row.data[0]["close_price"] if last_close_row.data else None

    current_price_row = (
        supabase.table("PriceData")
        .select("close_price")
        .eq("ticker", ticker)
        .eq("period", "1d")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    current_price = current_price_row.data[0]["close_price"] if current_price_row.data else None

    if current_price is not None:
        supabase.table("Stocks").update(
            {
                "CurrentPrice": float(current_price),
                "marketCap": float(current_price) * stock.get("sharesOutstanding", 0),
            }
        ).eq("Ticker", ticker).execute()

    return {
        "ticker": ticker,
        "inserted_rows": len(price_rows),
        "last_updated": str(last_1m_time) if last_1m_time else None,
        "last_close": last_close,
        "current_price": current_price,
    }

from sqlalchemy.sql import exists

@router.patch("/UpdatedDateChanger") 
def update_date_changer(db: Session = Depends(get_db)):

    stocks = (
    db.query(Stock)
    .filter(
        exists().where(PriceData.stock_id == Stock.id)
    )
    .all()
)
    for stock in stocks:
            
            records = db.query(PriceData).filter(PriceData.period == "1m", PriceData.stock_id == stock.id).order_by(PriceData.date.desc()).first()
            stock.updated = records.date if records else None 
            print(f"Updated {stock.Ticker} with date {stock.updated}") 
    db.commit()
    return {"detail": "Date changer updated successfully."}          



@router.patch("/UpdateAllData/{ticker}", response_model=dict)
def UpdateAllTechnicaldata(
    ticker: str,
    db: Session = Depends(get_db),
    timeinterval: int = 20,
    current_user: User = Depends(get_current_user)
):
    stock = db.query(Stock.id, Stock.Ticker, Stock.updated, Stock.CurrentPrice).filter(
        Stock.Ticker == ticker
    ).first()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Update pricing first (should be done synchronously)
    pricingdata = update_single_ticker_supabase(ticker , db)

    if pricingdata["last_updated"] : 
       db.query(Stock).filter(Stock.Ticker == ticker).update(
        {"updated": pricingdata["last_updated"]}
    )
    db.commit()
 
    return {
        "message": "Data updated successfully",
        "ticker": ticker,
        "pricing": pricingdata,
    }

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
        "peg": ratios.get("PEG"),
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
    
    print(ratios)
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
