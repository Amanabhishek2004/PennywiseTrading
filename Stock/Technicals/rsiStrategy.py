import yfinance as yf
from sklearn.linear_model import LinearRegression
import numpy as np 

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
        # Fetch stock data 
        from Database.models import  Stock , StockTechnicals , Channel , PriceData          
        print("running")
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if not stock:
            print(f"No stock named {ticker}")
            return

        # Fetch price data based on the period
        price_query = (
            db.query(PriceData)
            .filter(
                PriceData.stock_id == stock.id,
                PriceData.period == period
            )
            .order_by(PriceData.date.asc())
            .all()
)
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
        valid_rsi = rsi_values[-20:]
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
            technical.RsiSlope = float(m)
            technical.Rsiintercept = float(b)
            technical.CurrentRsi = float(current_rsi)
        else:
            technical = StockTechnicals(
                stock_id=stock.id,
                ticker=ticker,
                period=period,
                RsiSlope=float(m),
                Rsiintercept=float(b),
                CurrentRsi=float(current_rsi)
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

def CalculateRSIpeakMaxmin(db, close_price, currentrsi, ticker, period, interval=30):
    from Database.models import PriceData, Stock

    # Get the stock object
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        print(f"No stock found for ticker {ticker}")
        return False, False

    # Get the last PriceData instance for this stock and period
    last_price = (
        db.query(PriceData)
        .filter(PriceData.stock_id == stock.id, PriceData.period == period)
        .order_by(PriceData.date.desc())
        .first()
    )
    if not last_price:
        print("No price data found.")
        return False, False

    # Use the date from the last PriceData instance
    last_date_str = last_price.date
    ist_offset = timezone(timedelta(hours=5, minutes=30))

    def format_with_colon(dt):
        """Format datetime with a colon in the timezone offset and seconds set to 00."""
        return dt.strftime('%Y-%m-%d %H:%M:00%z')[:-2] + ':' + dt.strftime('%Y-%m-%d %H:%M:00%z')[-2:]

    if period == "1d":
        start_date = datetime.fromisoformat(str(last_date_str)).date()
        dates = [
            format_with_colon(
                datetime.combine(start_date, datetime.min.time(), ist_offset) - timedelta(days=i)
            )
            for i in range(interval)
        ]
    else:
        interval_data_mock = int(period[0])
        interval_data = 30 if interval_data_mock == 3 else 5
        start_datetime = datetime.fromisoformat(str(last_date_str)).replace(tzinfo=ist_offset)
        dates = [
            format_with_colon((start_datetime - timedelta(minutes=i * interval_data)).replace(second=0))
            for i in range(interval)
        ]

    print(dates)
    tolerance = 0.003 *close_price

    # Query RSI data within the interval
    data_min = db.query(PriceData).filter(
        PriceData.date.in_(dates),
        PriceData.close_price >= close_price,
        PriceData.RSI < currentrsi
    ).all()

    data_max = db.query(PriceData).filter(
        PriceData.date.in_(dates),
        PriceData.close_price <= close_price,
        PriceData.RSI > currentrsi
    ).all()

    print("max rsi -- " , [x.RSI for x in data_max] , currentrsi)
    return len(data_max) != 0, len(data_min) != 0





def CalculatePricetrend(ticker ,db , period):
    from Database.models import  Stock , StockTechnicals , Channel , PriceData          
    
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



