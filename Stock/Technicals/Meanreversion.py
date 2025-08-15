import yfinance as yf 
import pandas as pd 
import numpy as np
from Database.models import  *
from .StockChannels import CreateChannel
from Database.models import *
from datetime import datetime , timedelta , timezone
from sqlalchemy import func
from sklearn.linear_model import LinearRegression
from  sklearn.preprocessing import StandardScaler 
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

def OnbalanceVolume(prices) : 
    from Database.models import  Stock , StockTechnicals , Channel , PriceData  
    data = pd.DataFrame(
        {"Date": [price.Date for price in prices],  
         "Close": [price.close_price for price in prices],
         "Open": [price.open_price for price in prices],    
         "Volume": [price.volume for price in prices]}
    )
    data['OBV'] = data['Volume'].where(data['Close'] > data['Open'], -data['Volume']).cumsum()
    return {
        "OBV": data['OBV'].values,
        "Date": data['Date']   , 
        "price"  : [price.close_price for price in prices]
    }

def CreateVolumeChannel(ticker: str, timeperiod: int = 30, period: str = "1d"):
    # Fetch price data from Supabase
    price_data_res = supabase.table("PriceData") \
        .select("date, OnbalanceVolume") \
        .eq("ticker", ticker) \
        .eq("period", period) \
        .order("date", desc=False) \
        .execute()

    price_data = price_data_res.data
    if not price_data:
        print("No Price Data")
        return

    data = pd.DataFrame(price_data)
    if len(data) < timeperiod:
        raise ValueError(f"Not enough data points to calculate channels for timeperiod: {timeperiod} , {period}")

    # Calculate channel slopes and intercepts
    upperlineslope, upperintercept = CreateUpperChannel(data, window=timeperiod)
    lowerlineslope, lowerintercept = CreateLowerChannel(data, window=timeperiod)

    # Check if technical entry exists
    tech_res = supabase.table("StockTechnicals") \
        .select("id") \
        .eq("ticker", ticker) \
        .eq("period", period) \
        .execute()

    if tech_res.data:
        # Update existing technicals
        supabase.table("StockTechnicals").update({
            "VolumeUpperChannelSlope": float(upperlineslope),
            "VolumeUpperChannelIntercept": float(upperintercept),
            "VolumeLowerChannelSlope": float(lowerlineslope),
            "VolumeLowerChannelIntercept": float(lowerintercept)
        }).eq("id", tech_res.data[0]["id"]).execute()
    else:
        # Get stock_id
        stock_res = supabase.table("Stocks").select("id").eq("Ticker", ticker).execute()
        stock_id = stock_res.data[0]["id"] if stock_res.data else None

        # Insert new technical entry
        supabase.table("StockTechnicals").insert({
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


def CreateUpperChannel(data, window):
    """
    Create an upper channel using a rolling window, with scaling.
    """
    print(data)
     
    highwindow = data["OnbalanceVolume"].rolling(window=window).max()
    x = np.arange(len(data["OnbalanceVolume"][-window:])).reshape(-1, 1)
    y = highwindow[-window:].dropna().values

    # Apply scaling to x and y
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    x_scaled = scaler_x.fit_transform(x[:len(y)])
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

    lr = LinearRegression()
    lr.fit(x_scaled, y_scaled)  # Fit on scaled data
    intercept = lr.intercept_
    coefficient = lr.coef_[0]

    return coefficient, intercept

def CreateLowerChannel(data, window):
    """
    Create a lower channel using a rolling window, with scaling.
    """
    lowwindow = data["OnbalanceVolume"].rolling(window=window).min()
    x = np.arange(len(data["OnbalanceVolume"][-window:])).reshape(-1, 1)
    y = lowwindow[-window:].dropna().values

    # Apply scaling to x and y
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    x_scaled = scaler_x.fit_transform(x[:len(y)])
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

    lr = LinearRegression()
    lr.fit(x_scaled, y_scaled)  # Fit on scaled data
    intercept = lr.intercept_
    coefficient = lr.coef_[0]

    return coefficient, intercept


def format_with_colon(dt):
        """Format datetime with a colon in the timezone offset and seconds set to 00."""
        return dt.strftime('%Y-%m-%d %H:%M:00%z')[:-2] + ':' + dt.strftime('%Y-%m-%d %H:%M:00%z')[-2:]


def CalculateVolumepeakmaxmin(db, date, ticker, period, interval):
    from Database.models import  Stock , StockTechnicals , Channel , PriceData  
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
        .scalar()  # Fetch the scalar value
    )

    max_peak = (
        db.query(func.max(PriceData.OnbalanceVolume))
        .join(Stock)
        .filter(PriceData.date.in_(dates), Stock.Ticker == ticker)
        .scalar()  # Fetch the scalar value
    )

    return {
        "min": min_peak,  # Returns the minimum OBV
        "max": max_peak   # Returns the maximum OBV
    }
     
     
     








