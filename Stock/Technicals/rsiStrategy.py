import yfinance as yf
from sklearn.linear_model import LinearRegression
import numpy as np 
from datetime import datetime, timedelta
import pandas as pd 
from sklearn.preprocessing import StandardScaler



def CreateTrendline(data):
 
    x = np.arange(len(data)).reshape(-1, 1)  # Reshape for sklearn  
    y = data.values  # Reshape for sklearn   

    # Apply scaling to x and y
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    x_scaled = scaler_x.fit_transform(x)
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).flatten()

    model = LinearRegression()
    model.fit(x_scaled, y_scaled)  # Fit the model on scaled data
    trendline = model.predict(x_scaled)  # Predict the trendline (scaled)

    m, b = model.coef_[0], model.intercept_
    return trendline, m, b


import numpy as np



def CalculateRSI(ticker, db, period, price_data):
    from Database.models import Stock, StockTechnicals, PriceData
    import pandas as pd

    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        print(f"No stock named {ticker}")
        return

    price_query = (
        price_data
        .filter(
            PriceData.stock_id == stock.id,
            PriceData.period == period
        )
        .order_by(PriceData.date.desc())
        .all()
    )

    prices = pd.Series([p.close_price for p in price_query])
    rsi_values = pd.Series([p.RSI for p in price_query])
    
    if len(prices) < 14:
        print("Not enough data to calculate RSI.")
        return
      
    current_rsi = float(rsi_values.iloc[0])
    if pd.isna(current_rsi):
        print("Unable to calculate RSI for the latest period.")
        return

    valid_rsi = rsi_values[:21]
    if len(valid_rsi) < 2:
        print("Not enough data to calculate RSI trendline.")
        return
    
    trendline, m, b = CreateTrendline(valid_rsi)

    technical = db.query(StockTechnicals).filter(
        StockTechnicals.stock_id == stock.id,
        StockTechnicals.period == period
    ).first()

    if technical:
        technical.RsiSlope = float(m)
        technical.Rsiintercept = float(b)
        technical.CurrentRsi = current_rsi
    else:
        technical = StockTechnicals(
            stock_id=stock.id,
            ticker=ticker,
            period=period,
            RsiSlope=float(m),
            Rsiintercept=float(b),
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

def CalculateRSIpeakMaxmin(db, close_price, currentrsi, ticker, period, interval=30 , price_query = None):
    from Database.models import PriceData, Stock

    stock_id = db.query(Stock.id).filter(Stock.Ticker == ticker).scalar()
    if not stock_id:
        print(f"No stock found for ticker {ticker}")
        return False, False

    # Get last N records subquery
    subquery = (
        price_query
        .filter(PriceData.stock_id == stock_id, PriceData.period == period)
        .order_by(PriceData.date.desc())
        .limit(interval)
        .subquery()
    )

    # Check if any min condition exists
    data_min_exists = (
        db.query(PriceData.id)
        .filter(
            PriceData.id.in_(subquery),
            PriceData.close_price <= close_price,
            PriceData.RSI < currentrsi
        )
        .first() is not None
    )

    # Check if any max condition exists
    data_max_exists = (
        db.query(PriceData.id)
        .filter(
            PriceData.id.in_(subquery),
            PriceData.close_price >= close_price,
            PriceData.RSI > currentrsi
        )
        .first() is not None
    )

    return data_max_exists, data_min_exists





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



