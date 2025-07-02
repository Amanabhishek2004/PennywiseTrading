from collections import namedtuple
import numpy as np
import pandas as pd
from .StockChannels import CreateUpperChannel, CreateLowerChannel
from Database.models import *
from datetime import datetime
from Database.models import * 
from sqlalchemy import and_
# from .models import *

def UpdateTheChannelsdata(Ticker, db):
    try:

        #  for minute wise update
        price_min = (
            db.query(PriceData)
            .filter(PriceData.period == "1m", PriceData.stock.Ticker == Ticker)
            .all()
        )
        stock_data = db.query(Stock).filter(Stock.Ticker == Ticker).first()
        opendata = np.array(price.open_price for price in price_min)
        closedata = np.array(price.close_price for price in price_min)
        highdata = np.array(price.high_price for price in price_min)
        lowdata = np.array(price.high_price for price in price_min)
        data = np.hstack([opendata, closedata, highdata, lowdata])
        stock = pd.DataFrame(data, columns=["Open", "Close", "High", "Low"])
        upperlineslope, upperintercept = CreateUpperChannel(stock, window=30)
        lowerlineslope, lowerintercept = CreateLowerChannel(stock, window=30)
          
        stock_data.channel

        return data
    except Exception as e:
        print("Error in UpdateTheChannelsdata: ", e)






def UpdateSuppourt(Ticker, db, period):

    stock_data = db.query(Stock).filter(Stock.Ticker == Ticker).first()
    short_termprices = (
        db.query(PriceData).join(Stock)
        .filter(PriceData.period == period, Stock.Ticker == Ticker)
        .all()
    )
    last_short_term_price = short_termprices[-1]
    data = IdentifySingleCandleStickPattern(last_short_term_price, period)
    if not data : 
        data = IdentifyDoubleCandleStickPatterns(short_termprices[-2 : ], period)  
    
    if data and data.get("Suppourt"):
    #   if suppourt already exixts 
        suppourt = db.query(SupportData).filter(   
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price == (data["Suppourt"]),
        ).first()  
        if suppourt:    
            suppourt.retests += 1  
            suppourt.pattern = data["pattern"]  
        else: 
            suppourt = SupportData(
                stock_id=stock_data.id,
                Price=(data["Suppourt"]),
                period=period,
                timestamp =  data["time"] , 
                Pattern=data["pattern"],
                retests=1,
            )
            db.add(suppourt)    
    if data and data.get("Resistance"):
        #   if resistance already exists 
        resistance = db.query(SupportData).filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price == (data["Resistance"]),
        ).first()
        if resistance:
            resistance.retests += 1
            resistance.pattern = data["pattern"]    
        else:
            resistance = SupportData(
                stock_id=stock_data.id,
                Price=(data["Resistance"]),
                period=period,
                timestamp =  data["time"] , 
                Pattern=data["pattern"],
                retests=1,
            )
            db.add(resistance)
    
    db.commit()
    # filter the supports in increasing order 
    support = (
        db.query(SupportData)
        .filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
           SupportData.Price <= stock_data.CurrentPrice
        )
        .order_by(SupportData.Price.desc())
        .first()
    )
      
    # filter the resistances in decreasing order
    resistance = (
        db.query(SupportData)
        .filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price >= stock_data.CurrentPrice
        )
        .order_by(SupportData.Price.asc())
        .first()
    )

    # print(stock_data.CurrentPrice)
    
    

    return {
        "Support": support.Price if support else None,
        "Resistance": resistance.Price if resistance else None,
        "Support_pattern": support.Pattern if support else None,
        "Resistance_pattern": resistance.Pattern if resistance else None,
        "Ticker": Ticker,
        "Support_time": support.timestamp if support else None,
        "Resistance_time": resistance.timestamp if resistance else None,
        "Period": period,
    }

def MakeStrongSupportResistance(ticker, db, period):
    stock_data = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock_data:
        raise ValueError(f"Stock with ticker {ticker} not found in the database.")

    # Get the current price
    current_price = stock_data.CurrentPrice  

    # Fetch price data within the 10% range of the current price
    Prices = db.query(PriceData).filter(
    PriceData.stock_id == stock_data.id,
    PriceData.period == period,
    and_(
        PriceData.close_price >= current_price * 0.9,  # Lower bound
        PriceData.close_price <= current_price * 1.1   # Upper bound
    )
).all()
    if not Prices: 
        return

    data = pd.DataFrame({
        "Date": [price.date for price in Prices],
        "Low": [price.low_price for price in Prices],
        "High": [price.high_price for price in Prices],
        "Close": [price.close_price for price in Prices]
    })

    if data.empty:  # Check if data is empty
        raise ValueError(f"No valid data to process for ticker {ticker}.")

    # Apply rolling calculations and rounding
    data["RoundedLow"] = data["Low"].rolling(window=10, min_periods=1).min()
    data["RoundedHigh"] = data["High"].rolling(window=10, min_periods=1).max()

    def conditional_round(price):
        if pd.isna(price):  # Handle NaN values
            return None
        return round(price, 1) if price < 50 else round(price)

    data["RoundedLow"] = data["RoundedLow"].apply(conditional_round)
    data["RoundedHigh"] = data["RoundedHigh"].apply(conditional_round)

    # Drop rows with NaN values in RoundedLow and RoundedHigh
    data.dropna(subset=["RoundedLow", "RoundedHigh"], inplace=True)

    # Prepare support and resistance data with counts and dates
    suppourtdata = data[["RoundedLow"]].value_counts().reset_index()
    suppourtdata.columns = ["Low", "count_x"]

    resistancedata = data[["RoundedHigh"]].value_counts().reset_index()
    resistancedata.columns = ["High", "count_y"]

    # Merge support and resistance data
    merged_data = suppourtdata.merge(
        resistancedata, how="inner", left_on="Low", right_on="High"
    )

    # Combine counts and sort by their total occurrences
    merged_data["count"] = merged_data["count_x"] + merged_data["count_y"]

    # Separate into support and resistance levels
    supports = merged_data[
        (merged_data["Low"] < current_price)
    ].sort_values(by="count", ascending=False).head(4)
    print(period , supports)
    resistances = merged_data[
        (merged_data["Low"] > current_price)
    ].sort_values(by="count", ascending=False).head(4)

    # Combine support and resistance levels
    strong_levels = pd.concat([supports, resistances]).reset_index(drop=True)

    # Create support and resistance entries in the database
    for _, row in strong_levels.iterrows():
        suppourt = SupportData(
            stock_id=stock_data.id,
            Price=float(row["Low"]),  # Convert to native Python float
            period=period,
            Pattern="Strong Levels",
            retests=int(row["count"]),  # Convert to native Python int
        )
        db.add(suppourt)

        db.commit()
    db.commit()    

def CreatepatternSuppourt(Ticker, db, period):
    stock_data = db.query(Stock).filter(Stock.Ticker == Ticker).first()
    if not stock_data:
        return {"error": "Stock not found"}

    current_price = stock_data.CurrentPrice  # Retrieve the current price
 
    
    last_support = (
        db.query(SupportData)
        .filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.timestamp != None  # Only consider supports with a timestamp
        )
        .order_by(SupportData.timestamp.desc())
        .first()
    )
    last_time = last_support.timestamp if last_support else None

    price_query = db.query(PriceData).filter(
        PriceData.stock_id == stock_data.id,
        PriceData.period == period,
        and_(
            PriceData.close_price >= current_price * 0.9,
            PriceData.close_price <= current_price * 1.1
        )
    )
    if last_time:
        price_query = price_query.filter(PriceData.date > last_time)
    
    short_termprices = price_query.all()   
     
    if not short_termprices:
        return {"error": "No price data available within the 10 percent range for the given period"}

    patterns = []  # Store identified patterns

    for index, price in enumerate(short_termprices):
        # Identify single candlestick patterns
        data = IdentifySingleCandleStickPattern(price, period)
        if not data and index > 0:
            # Identify double candlestick patterns (requires at least two prices)
            data = IdentifyDoubleCandleStickPatterns(
                short_termprices[index - 1 : index + 1],  # Last two candles
                period
            )

        if data:
            patterns.append(data)

    # Process identified patterns and update or insert them into the database
    for data in patterns:
        price_level = data.get("Suppourt") or data.get("Resistance")
        tolerance = 0.008 * price_level  # Tolerance level for matching
        pattern_type = "Suppourt" if "Suppourt" in data else "Resistance"

        # Check for existing support/resistance with explicit range conditions
        existing_pattern = db.query(SupportData).filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price >= price_level - tolerance,  # Lower bound
            SupportData.Price <= price_level + tolerance   # Upper bound
        ).first()

        if existing_pattern:
            # Update the existing pattern
            existing_pattern.retests += 1
            existing_pattern.Pattern = data["pattern"]
            existing_pattern.timestamp = data["time"]
        else:
            # Create a new pattern if none exists
            new_pattern = SupportData(
                stock_id=stock_data.id,
                Price=price_level,
                period=period,
                Pattern=data["pattern"],
                timestamp=data["time"],
                retests=1,
            )
            db.add(new_pattern)
            db.commit()  
    # Commit changes to the database
    db.commit()

    # Fetch the nearest support and resistance levels
    support = (
        db.query(SupportData)
        .filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price <= current_price,
        )
        .order_by(SupportData.Price.desc())  # Nearest support below current price
        .first()
    )

    resistance = (
        db.query(SupportData)
        .filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price >= current_price,
        )
        .order_by(SupportData.Price.asc())  # Nearest resistance above current price
        .first()
    )

    # Safely extract attributes or use defaults
    return {
        "Support": support.Price if support else None,
        "Resistance": resistance.Price if resistance else None,
        "Support_pattern": support.Pattern if support else None,
        "Resistance_pattern": resistance.Pattern if resistance else None,
        "Ticker": Ticker,
        "Support_time": support.timestamp if support else None,
        "Resistance_time": resistance.timestamp if resistance else None,
        "Period": period,
    }



def IdentifySingleCandleStickPattern(price, period):
    body = abs(price.open_price - price.close_price)
    uppershadow = price.high_price - max(price.open_price, price.close_price)
    lowershadow = min(price.open_price, price.close_price) - price.low_price

    # Hammer
    if body > 0 and uppershadow <= 0.02 * body and lowershadow >= 1.5 * body:
        return {
            "Suppourt": price.low_price,
            "pattern": "Hammer",
            "time": price.date,
            "period": period,
        }

    # Shooting Star
    if body > 0 and uppershadow >= 2 * body and lowershadow <= 0.2 * body:
        return {
            "Resistance": price.high_price,
            "pattern": "Shooting Star",
            "time": price.date,
            "period": period,
        }

    # Doji
    if body <= 0.1 * (price.high_price - price.low_price):  # Body is very small
        if uppershadow == 0 and lowershadow > 0:
            return {
                "Suppourt": price.low_price,
                "pattern": "T",
                "time": price.date,
                "period": period,
            }
        elif lowershadow == 0 and uppershadow > 0:
            return {
                "Resistance": price.high_price,
                "pattern": "Inverted T",
                "time": price.date,
                "period": period,
            }
        elif uppershadow > 0 and lowershadow > 0:
            return {
                "Resistance": price.close_price,
                "pattern": "Doji",
                "time": price.date,
                "period": period,
            }

    return None


def IdentifyDoubleCandleStickPatterns(prices, period):
    if len(prices) < 2:
        return None

    first = prices[-2]
    second = prices[-1]

    o1, c1 = first.open_price, first.close_price
    o2, c2 = second.open_price, second.close_price

    # Bullish Engulfing: First candle bearish, second candle bullish
    if c1 < o1 and c2 > o2 and c1 > o2 and o1 < c2:
        return {
            "Suppourt": min(second.low_price, first.low_price),
            "pattern": "Bullish Engulfing",
            "time": second.date,
            "period": period,
        }

    # Bearish Engulfing: First candle bullish, second candle bearish
    if c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
        return {
            "Resistance": max(second.high_price, first.high_price),
            "pattern": "Bearish Engulfing",
            "time": second.date,
            "period": period,
        }

    # Dark Cloud Cover: First candle bullish, second opens above and closes below midpoint of first body
    midpoint = o1 + (c1 - o1) / 2
    if c1 > o1 and o2 > c1 and c2 < midpoint and c2 > o1:
        return {
            "Resistance": max(second.high_price, first.high_price),
            "pattern": "Dark Cloud Cover",
            "time": second.date,
            "period": period,
        }

    # Piercing Pattern: First candle bearish, second opens below and closes above midpoint of first body
    if c1 < o1 and o2 < c1 and c2 > midpoint and c2 < o1:
        return {
            "Suppourt": min(second.low_price, first.low_price),
            "pattern": "Piercing Pattern",
            "time": second.date,
            "period": period,
        }

    # Rising Window (Gap Up): Second low is higher than first high
    if second.low_price > first.high_price:
        return {
            "Suppourt": second.low_price,
            "pattern": "Rising Window",
            "time": second.date,
            "period": period,
        }

    # Falling Window (Gap Down): Second high is lower than first low
    if second.high_price < first.low_price:
        return {
            "Resistance": second.high_price,
            "pattern": "Falling Window",
            "time": second.date,
            "period": period,
        }

    return None


Price = namedtuple("Price", ["open_price", "close_price", "high_price", "low_price", "date"])
test_data = [
    Price(open_price=100, close_price=105, high_price=110, low_price=95, date="2025-06-10"),
    Price(open_price=106, close_price=101, high_price=111, low_price=100, date="2025-06-11"),
]

for price in test_data:
    result = IdentifySingleCandleStickPattern(price, "1d")
    print(result)

for i in range(len(test_data) - 1):
    result = IdentifyDoubleCandleStickPatterns(test_data[i:i+2], "1d")
    print(result)
