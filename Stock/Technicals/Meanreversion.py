import yfinance as yf 
import pandas as pd 
import numpy as np
from Database.models import *
from .StockChannels import CreateChannel
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler 
from supabase import create_client, Client
from uuid import uuid4

# --- Supabase Client ---
SUPABASE_URL = "https://uitfyfywxzaczubnecft.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVpdGZ5Znl3eHphY3p1Ym5lY2Z0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTQ1MjMzNiwiZXhwIjoyMDY3MDI4MzM2fQ.yjZ6UsGzO4F6VyU0q_HSUVrekFr9XGHazN9cd61nOZ8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def CreateVolumeChannel(ticker: str, data, timeperiod: int = 20, period: str = "1d"):
    # Fetch price data from Supabase
    # price_data = price_data.limit(100).all()
    # if not price_data:
    #     print("No Price Data")
    #     return

    # data = pd.DataFrame([{
    #     "OnbalanceVolume": p.OnbalanceVolume,
    #     "date": p.date
    # } for p in price_data])
    print(len(data), timeperiod)
    if len(data) < timeperiod:
        print(f"Not enough data points to calculate channels for timeperiod: {timeperiod} , {period}")
        return 

    # --- Scale OBV before passing to regression ---
    scaler = StandardScaler()
    data["OnbalanceVolume_scaled"] = scaler.fit_transform(
        data["OnbalanceVolume"].values.reshape(-1, 1)
    ).flatten()

    # Calculate channel slopes and intercepts (on scaled OBV)
    upperlineslope, upperintercept = CreateUpperChannel(data, window=timeperiod, scaled=True)
    lowerlineslope, lowerintercept = CreateLowerChannel(data, window=timeperiod, scaled=True)

    # Save/update in Supabase
    tech_res = supabase.table("StockTechnicals") \
        .select("id") \
        .eq("ticker", ticker) \
        .eq("period", period) \
        .execute()

    if tech_res.data:
        supabase.table("StockTechnicals").update({
            "VolumeUpperChannelSlope": float(upperlineslope),
            "VolumeUpperChannelIntercept": float(upperintercept),
            "VolumeLowerChannelSlope": float(lowerlineslope),
            "VolumeLowerChannelIntercept": float(lowerintercept)
        }).eq("id", tech_res.data[0]["id"]).execute()
    else:
        stock_res = supabase.table("Stocks").select("id").eq("Ticker", ticker).execute()
        stock_id = stock_res.data[0]["id"] if stock_res.data else None

        supabase.table("StockTechnicals").insert({
            "id": str(uuid4()),
            "ticker": ticker,
            "period": period,
            "stock_id": stock_id,
            "VolumeUpperChannelSlope": float(upperlineslope),
            "VolumeUpperChannelIntercept": float(upperintercept),
            "VolumeLowerChannelSlope": float(lowerlineslope),
            "VolumeLowerChannelIntercept": float(lowerintercept)
        }).execute()
    
    return {
        "UpperChannelData": {
            "Slope": upperlineslope,
            "Intercept": upperintercept,
            "Channel": ((upperlineslope * np.arange(len(data))) + upperintercept).tolist(),
        },
        "LowerChannelData": {
            "Slope": lowerlineslope,
            "Intercept": lowerintercept,
            "Channel": ((lowerlineslope * np.arange(len(data))) + lowerintercept).tolist(),
        },
    }


def CreateUpperChannel(data, window, scaled=False):
    """Create an upper channel using rolling max."""
    col = "OnbalanceVolume_scaled" if scaled else "OnbalanceVolume"
    highwindow = data[col].rolling(window=10).max().dropna()

    y = highwindow.values
    x = np.arange(len(y)).reshape(-1, 1)

    lr = LinearRegression()
    lr.fit(x, y)

    return lr.coef_[0], lr.intercept_


def CreateLowerChannel(data, window, scaled=False):
    """Create a lower channel using rolling min."""
    col = "OnbalanceVolume_scaled" if scaled else "OnbalanceVolume"
    lowwindow = data[col].rolling(window=10).min().dropna()

    y = lowwindow.values
    x = np.arange(len(y)).reshape(-1, 1)

    lr = LinearRegression()
    lr.fit(x, y)

    return lr.coef_[0], lr.intercept_


def format_with_colon(dt):
    """Format datetime with a colon in the timezone offset and seconds set to 00."""
    return dt.strftime('%Y-%m-%d %H:%M:00%z')[:-2] + ':' + dt.strftime('%Y-%m-%d %H:%M:00%z')[-2:]

def CalculateVolumepeakmaxmin(db, date, ticker, period, interval):
    tolerance = 0.003
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    if period == "1d":
        # Generate a list of dates for daily intervals
        start_date = datetime.fromisoformat(date).date()
        dates = [
            format_with_colon(
                datetime.combine(start_date, datetime.min.time(), ist_offset) - timedelta(days=i)
            )
            for i in range(interval)
        ]
    else:
        # Generate a list of datetime values for minute intervals
        start_datetime = datetime.fromisoformat(date).replace(tzinfo=ist_offset)
        dates = [
            format_with_colon((start_datetime - timedelta(minutes=i)).replace(second=0))
            for i in range(interval)
        ]
    # Query the database for the matching dates and ticker
    min_peak = (
        db.query(func.min(PriceData.OnbalanceVolume))
        .join(Stock)
        .filter(PriceData.date.in_(dates), Stock.Ticker == ticker)
        .scalar()
    )

    max_peak = (
        db.query(func.max(PriceData.OnbalanceVolume))
        .join(Stock)
        .filter(PriceData.date.in_(dates), Stock.Ticker == ticker)
        .scalar()
    )

    return {
        "min": min_peak,
        "max": max_peak
    }