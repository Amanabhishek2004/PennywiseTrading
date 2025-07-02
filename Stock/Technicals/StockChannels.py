import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from Database.models import *


def CreateChannel(db, Ticker: str, timeperiod: int = 30, period: str = "1d"):
    # Query the PriceData table for the specified ticker
    price_data = (
        db.query(PriceData)
        .filter(PriceData.ticker == Ticker, PriceData.period == period)
        .order_by(PriceData.date.asc())
        .all()
    )

    # Validate data
    if not price_data:
        print(f"No data found for Ticker: {Ticker}")
        return
    # Convert to pandas DataFrame
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
    )

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
            stock_id=price_data[
                0
            ].stock_id,  # Assuming all records have the same stock_id
            ticker=Ticker,
            upper_channel_slope=upperlineslope,
            upper_channel_intercept=upperintercept,
            period=period,
            lower_channel_slope=lowerlineslope,
            lower_channel_intercept=lowerintercept,
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
    Create an upper channel using a rolling window.
    """
    highwindow = data["high_price"].rolling(window=window).max()
    x = np.arange(len(data["close_price"][-window:])).reshape(-1, 1)
    y = highwindow[-window:].dropna().values

    lr = LinearRegression()
    lr.fit(x[: len(y)], y)  # Align x and y
    intercept = lr.intercept_
    coefficient = lr.coef_[0]

    return coefficient, intercept


def CreateLowerChannel(data, window):
    """
    Create a lower channel using a rolling window.
    """
    lowwindow = data["low_price"].rolling(window=window).min()
    x = np.arange(len(data["close_price"][-window:])).reshape(-1, 1)
    y = lowwindow[-window:].dropna().values

    lr = LinearRegression()
    lr.fit(x[: len(y)], y)  # Align x and y
    intercept = lr.intercept_
    coefficient = lr.coef_[0]

    return coefficient, intercept
