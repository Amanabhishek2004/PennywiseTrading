import yfinance as yf
from sklearn.linear_model import LinearRegression
import numpy as np 
import pandas_ta as ta
from Database.models import *   
from datetime import datetime, timedelta
import pandas as pd 



def CreateTrendline(data) :
    x = np.arange(len(data)).reshape(-1, 1)  # Reshape for sklearn  
    y = data.values  # Reshape for sklearn   
    model = LinearRegression()  
    model.fit(x, y)  # Fit the model
    trendline = model.predict(x)  # Predict the trendline
    m , b = model.coef_[0] , model.intercept_
    return trendline , m , b


import numpy as np



def CalculateRSI(ticker, db, period):
    """
    Calculate and update the RSI (Relative Strength Index) for a given stock.
    
    Args:
        ticker (str): Stock ticker symbol.
        db (Session): Database session.
        period (str): Period ("1m" or "1d").
    
    Returns:
        dict: Contains RSI signal, current RSI, region, trend slope, and intercept.
    """
    try:
        # Fetch stock data
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if not stock:
            print(f"No stock named {ticker}")
            return

        # Fetch price data based on the period
        price_query = (
            db.query(PriceData.close_price)
            .filter(
                PriceData.stock_id == stock.id,
                PriceData.period == period
            )
            .order_by(PriceData.date.desc())
        )
        prices = pd.Series([price.close_price for price in price_query.all()])
        rsi_values = [price.Rsi for price in price_query.all()]
        if len(prices) < 14:
            print("Not enough data to calculate RSI.")
            return

        # Calculate RSI
        current_rsi = rsi_values.iloc[-1]
        if pd.isna(current_rsi):
            print("Unable to calculate RSI for the latest period.")
            return

        # Determine trendline and region
        valid_rsi = rsi_values[-5:].dropna()
        if len(valid_rsi) < 2:
            print("Not enough data to calculate RSI trendline.")
            return

        trendline = np.polyfit(range(len(valid_rsi)), valid_rsi, 1)
        m, b = trendline[0], trendline[1]

        region = "Neutral"
        signal = None

        if b + m * (len(valid_rsi) - 1) > current_rsi:  # RSI below trendline
            if current_rsi > 70:
                region = "Overbought"
            elif current_rsi < 30:
                region = "Oversold"
            signal = f"RSI crossed below the {'Positive' if m > 0 else 'Negative'} trendline"
        else:  # RSI above trendline
            if current_rsi > 70:
                region = "Overbought"
            elif current_rsi < 30:
                region = "Oversold"
            signal = f"RSI crossed above the {'Negative' if m < 0 else 'Positive'} trendline"

        # Update or create the StockTechnicals entry in the database
        technical = db.query(StockTechnicals).filter(
            StockTechnicals.period == period, 
            StockTechnicals.ticker == ticker
        ).first()

        if technical:
            technical.RsiSlope = m
            technical.Rsiintercept = b
            technical.CurrentRsi = current_rsi
        else:
            technical = StockTechnicals(
                stock_id=stock.id,
                ticker=ticker,
                period=period,
                RsiSlope=m,
                Rsiintercept=b,
                CurrentRsi=current_rsi
            )
            db.add(technical)

        db.commit()

        return {
            "Signal": signal,
            "Current RSI": current_rsi,
            "Region": region,
            "Trend Slope": m,
            "Intercept": b,
        }

    except Exception as e:
        print(f"Error calculating RSI: {e}")
        return



from datetime import datetime, timedelta, timezone

def CalculateRSIpeakMaxmin(db, close_price, currentrsi, date, period, interval=15):
    """
    Check if RSI is forming a peak at higher levels compared to previous intervals.
    
    Args:
        db (Session): Database session for queries.
        close_price (float): Current close price of the stock.
        currentrsi (float): Current RSI value.
        date (str): Current date as an ISO-formatted string.
        period (str): Timeframe for analysis.
        interval (int): Number of periods to check.

    Returns:
        bool: True if RSI forms a peak, False otherwise.
    """
    # Define the IST timezone offset
    ist_offset = timezone(timedelta(hours=5, minutes=30))

    def format_with_colon(dt):
        """Format datetime with a colon in the timezone offset and seconds set to 00."""
        return dt.strftime('%Y-%m-%d %H:%M:00%z')[:-2] + ':' + dt.strftime('%Y-%m-%d %H:%M:00%z')[-2:]

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

    print(dates)

    # Query RSI data within the interval
    data = db.query(PriceData).filter(
        PriceData.date.in_(dates),
        PriceData.close_price >= close_price,
        PriceData.RSI < currentrsi
    ).all()
    

    return True if data else False 





def CalculatePricetrend(ticker ,db , period):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()  
    signal = None
    if period == "Shortterm" :
        prices = db.query(PriceData).fiter(PriceData.stock_id == stock.id and period == "1m" ).order_by(PriceData.Date.desc()).all()
    else : 
        prices = db.query(PriceData).fiter(PriceData.stock_id == stock.id and period == "1d" ).order_by(PriceData.Date.desc()).all()
    close_price = map(lambda x: x.close_price , prices)    
    trendline , m , b = CreateTrendline(close_price.rolling(20).mean()[-5 : ]) 
    signal = None   
    current_price = close_price.iloc[-1]    
    if m > 0 and current_price < trendline[-1] : 
        signal = "Price is Below the Positive Trendline"
    elif m < 0 and current_price > trendline[-1] : 
        signal = "Price is Above the Negative Trendline"
    else :
        signal = "Price Is With The Trend"
    return {
        "Signal": signal,
        "Current Price": current_price ,
        "Trend" : m , 
        "intercept" : b 
    }    
    # Generate buy/sell signals based on RSI


"""
TRACK THE RSI TREND FOR LAST5 DAYS AND STORE THEM LIKE THIS  {
"DATE" :  ,
"TREND" : , 
}
"""

