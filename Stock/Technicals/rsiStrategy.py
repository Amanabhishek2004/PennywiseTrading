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

    # try:
        # Fetch stock data 
        print("running")
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if not stock:
            print(f"No stock named {ticker}")
            return

        # Fetch price data based on the period
        price_query =( db.query(PriceData).filter(
                PriceData.stock_id == stock.id,
                PriceData.period == period
            ).all())
        prices = pd.Series([price.close_price for price in price_query])
        rsi_values = pd.Series([price.RSI for price in price_query])
        if len(prices) < 14:
            print("Not enough data to calculate RSI.")
            return
        print(rsi_values)   
        # Calculate RSI
        current_rsi = rsi_values.iloc[-1]
        if pd.isna(current_rsi):
            print("Unable to calculate RSI for the latest period.")
            return

        # Determine trendline and region
        valid_rsi = rsi_values[-5:]
        if len(valid_rsi) < 2:
            print("Not enough data to calculate RSI trendline.")
            return

        trendline , m , b  = CreateTrendline(valid_rsi)


        # Current RSI as scalar
        current_rsi = float(rsi_values.iloc[-1])

        # Trendline comparison
        comparison_value = b + m * (len(valid_rsi) - 1)

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
            "Current RSI": current_rsi,
            "Trend Slope": m,
            "Intercept": b,
        }

    # except Exception as e:
    #     print(f"Error calculating RSI: {e}")
    #     return



from datetime import datetime, timedelta, timezone

def CalculateRSIpeakMaxmin(db, close_price, currentrsi, date, period, interval=15):
 
    # Check if RSI is forming a peak at higher levels compared to previous intervals.

    print(currentrsi)    
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
