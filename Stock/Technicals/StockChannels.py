import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from uuid import uuid4

def CreateChannel(db,data = None ,  Ticker: str = None, timeperiod: int = 20, period: str = "1d" , price_data = list):
    # Query the PriceData table for the specified ticker
    print(period)
    from Database.models import PriceData, Channel
    if data is None: 
        price_data = (
            db.query(PriceData)
            .filter(PriceData.ticker == Ticker, PriceData.period == period)
            .order_by(PriceData.date.desc())
            .all()
        )
        # Validate data
        if not price_data:
            print(f"No data found for Ticker: {Ticker}")
            return
        # Convert to pandas DataFrame (reverse to ascending order for regression)
        data = pd.DataFrame(
            [
                {
                    "date": record.date,
                    "close_price": record.close_price,
                    "high_price": record.high_price,
                    "low_price": record.low_price,
                }
                for record in price_data
            ]
        ).sort_values("date").reset_index(drop=True)

    print(len(data), timeperiod)
    # Ensure there are enough data points
    if len(data) < timeperiod:
        return

    # Calculate upper and lower channels
    upperlineslope, upperintercept = CreateUpperChannel(data, window=timeperiod)
    lowerlineslope, lowerintercept = CreateLowerChannel(data, window=timeperiod)

    # Check if the channel data already exists
    existing_channel = (
        db.query(Channel)
        .filter(Channel.ticker == Ticker, Channel.period == period)
        .first()
    )

    if existing_channel:
        # Update the existing channel record
        existing_channel.upper_channel_slope = float(upperlineslope)
        existing_channel.upper_channel_intercept = float(upperintercept)
        existing_channel.lower_channel_slope = float(lowerlineslope)
        existing_channel.lower_channel_intercept = float(lowerintercept)
    else:
        # Create a new channel record
        channel = Channel(
            id=str(uuid4()),
            stock_id=price_data[0].stock_id,
            ticker=Ticker,
            upper_channel_slope=float(upperlineslope),
            upper_channel_intercept=float(upperintercept),
            period=period,
            lower_channel_slope=float(lowerlineslope),
            lower_channel_intercept=float(lowerintercept),
        )
        db.add(channel)

    # Commit changes to the database
    try:
        db.commit()
    except InterruptedError as e:
        db.rollback()
        raise ValueError(f"Error saving or updating channel data: {str(e)}")

    return {
        "UpperChannelData": {
            "Slope": upperlineslope,
            "Intercept": upperintercept,
            "Channel": (upperlineslope * np.arange(len(data))) + upperintercept,
        },
        "LowerChannelData": {
            "Slope": lowerlineslope,
            "Intercept": lowerintercept,
            "Channel": (lowerlineslope * np.arange(len(data))) + lowerintercept,
        },
    }

def CreateUpperChannel(data, window):
    """
    Create an upper channel using rolling max over the latest 'window' rows.
    """
    highs_rolling = data["high_price"].rolling(window=10).max()
    highs = highs_rolling.dropna().values[-window:]  # last 'window' rolling max values
    x = np.arange(len(highs)).reshape(-1, 1)
    if len(highs) < 2:
        return 0, 0
    lr = LinearRegression()
    lr.fit(x, highs)
    intercept = lr.intercept_
    coefficient = lr.coef_[0]
    return coefficient, intercept

def CreateLowerChannel(data, window):
    """
    Create a lower channel using rolling min over the latest 'window' rows.
    """
    lows_rolling = data["low_price"].rolling(window=10).min()
    lows = lows_rolling.dropna().values[-window:]  # last 'window' rolling min values
    x = np.arange(len(lows)).reshape(-1, 1)
    if len(lows) < 2:
        return 0, 0
    lr = LinearRegression()
    lr.fit(x, lows)
    intercept = lr.intercept_
    coefficient = lr.coef_[0]
    return coefficient, intercept
