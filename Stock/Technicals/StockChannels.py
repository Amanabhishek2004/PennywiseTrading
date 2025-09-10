import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from uuid import uuid4

def CreateChannel(db, data=None, Ticker: str=None, timeperiod: int=20, period: str="1d"):
    """
    Create price channels (upper/lower regression lines) for a given ticker and period.
    Channels are fitted on the last `timeperiod` bars.
    """

    from Database.models import PriceData, Channel

    # Fetch data from DB if not provided
    if data is None: 
        price_data = (
            db.query(PriceData)
            .filter(PriceData.ticker == Ticker, PriceData.period == period)
            .order_by(PriceData.date.desc())
            .all()
        )
        if not price_data:
            print(f"No data found for Ticker: {Ticker}")
            return

        # Convert DB rows to DataFrame (ascending order)
        data = pd.DataFrame(
            [{
                "date": record.date,
                "close_price": record.close_price,
                "high_price": record.high_price,
                "low_price": record.low_price,
            } for record in price_data]
        ).sort_values("date").reset_index(drop=True)

    # Ensure enough data points
    if len(data) < timeperiod:
        return

    # Calculate channel slopes and intercepts
    upper_slope, upper_intercept = CreateUpperChannel(data, window=timeperiod)
    lower_slope, lower_intercept = CreateLowerChannel(data, window=timeperiod)

    # Check if channel already exists
    existing_channel = (
        db.query(Channel)
        .filter(Channel.ticker == Ticker, Channel.period == period)
        .first()
    )

    if existing_channel:
        existing_channel.upper_channel_slope = float(upper_slope)
        existing_channel.upper_channel_intercept = float(upper_intercept)
        existing_channel.lower_channel_slope = float(lower_slope)
        existing_channel.lower_channel_intercept = float(lower_intercept)
    else:
        channel = Channel(
            id=str(uuid4()),
            stock_id=price_data[0].stock_id,
            ticker=Ticker,
            upper_channel_slope=float(upper_slope),
            upper_channel_intercept=float(upper_intercept),
            period=period,
            lower_channel_slope=float(lower_slope),
            lower_channel_intercept=float(lower_intercept),
        )
        db.add(channel)

    # Commit
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error saving or updating channel data: {str(e)}")

    # Build channel lines across the dataset (for plotting)
    x_full = np.arange(len(data))
    return {
        "UpperChannelData": {
            "Slope": upper_slope,
            "Intercept": upper_intercept,
            "Channel": (upper_slope * x_full) + upper_intercept,
        },
        "LowerChannelData": {
            "Slope": lower_slope,
            "Intercept": lower_intercept,
            "Channel": (lower_slope * x_full) + lower_intercept,
        },
    }


def CreateUpperChannel(data, window: int):
    """
    Fit regression line on rolling max highs (last `window` values).
    """
    highs = data["high_price"].rolling(window=window).max().dropna().values[-window:]
    if len(highs) < 2:
        return 0, 0

    x = np.arange(len(highs)).reshape(-1, 1)
    lr = LinearRegression()
    lr.fit(x, highs)

    return lr.coef_[0], lr.intercept_


def CreateLowerChannel(data, window: int):
    """
    Fit regression line on rolling min lows (last `window` values).
    """
    lows = data["low_price"].rolling(window=window).min().dropna().values[-window:]
    if len(lows) < 2:
        return 0, 0

    x = np.arange(len(lows)).reshape(-1, 1)
    lr = LinearRegression()
    lr.fit(x, lows)

    return lr.coef_[0], lr.intercept_

