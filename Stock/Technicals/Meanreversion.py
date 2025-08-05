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

def CreateVolumeChannel(db, Ticker: str, timeperiod: int = 30, period: str = "1d"):
    from Database.models import Stock, StockTechnicals, Channel, PriceData  
    
    print("VOL", period)

    price_data = (
        db.query(PriceData)
        .filter(PriceData.ticker == Ticker, PriceData.period == period)
        .order_by(PriceData.date.asc())
        .all()
    )

    if not price_data:
        print("No Price Data")
        return

    # Convert to pandas DataFrame
    data = pd.DataFrame([{
        "date": record.date,
        "Volume": record.OnbalanceVolume,
    } for record in price_data])
    print(data) 
    if len(data) < timeperiod:
        raise ValueError(f"Not enough data points to calculate channels for timeperiod: {timeperiod} , {period}")

    # Calculate channels
    upperlineslope, upperintercept = CreateUpperChannel(data, window=timeperiod)
    lowerlineslope, lowerintercept = CreateLowerChannel(data, window=timeperiod)

    existing_channel = db.query(StockTechnicals).filter(
        StockTechnicals.ticker == Ticker,
        StockTechnicals.period == period
    ).first()

    if existing_channel:
        print("Updating existing channel")
        existing_channel.VolumeUpperChannelSlope = float(upperlineslope)
        existing_channel.VolumeUpperChannelIntercept = float(upperintercept)
        existing_channel.VolumeLowerChannelSlope = float(lowerlineslope)
        existing_channel.VolumeLowerChannelIntercept = float(lowerintercept)
    else:
        print("Creating new StockTechnicals entry")
        # Get the related stock_id
        stock = db.query(Stock).filter(Stock.Ticker == Ticker).first()
        stock_id = stock.id if stock else None

        new_entry = StockTechnicals(
            ticker=Ticker,
            period=period,
            stock_id=stock_id,
            VolumeUpperChannelSlope=float(upperlineslope),
            VolumeUpperChannelIntercept=float(upperintercept),
            VolumeLowerChannelSlope=float(lowerlineslope),
            VolumeLowerChannelIntercept=float(lowerintercept),
        )
        db.add(new_entry)

    db.commit()

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
    highwindow = data["Volume"].rolling(window=window).max()
    x = np.arange(len(data["Volume"][-window:])).reshape(-1, 1)
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
    lowwindow = data["Volume"].rolling(window=window).min()
    x = np.arange(len(data["Volume"][-window:])).reshape(-1, 1)
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
     
     
     








