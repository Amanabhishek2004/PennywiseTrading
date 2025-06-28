import numpy as np 
from datetime import datetime, timedelta, timezone
import pandas as pd
import yfinance as yf
from Database.models import PriceData, StockTechnicals, Channel
#  Calculate Vwap 
def CalculateVWAP(ticker, db, period, window="week"):

    now = datetime.now()
    if window == "week":
        start_time = now - timedelta(days=7)
    elif window == "month":
        start_time = now - timedelta(days=30)
    elif window == "year":
        start_time = now - timedelta(days=365)
    else:
        raise ValueError("window must be 'week', 'month', or 'year'")

    # Query all prices for the ticker and period
    prices = (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.period == period)
        .order_by(PriceData.date.asc())
        .all()
    )

    # Filter prices for the selected window
    recent_prices = []
    for price in prices:
        price_date = datetime.strptime(price.date, "%Y-%m-%d %H:%M:%S")
        if price_date >= start_time:
            recent_prices.append(price)

    if not recent_prices:
        return None

    total_volume = sum(p.volume for p in recent_prices)
    if total_volume == 0:
        return None

    vwap = sum(p.close_price * p.volume for p in recent_prices) / total_volume
    return vwap



