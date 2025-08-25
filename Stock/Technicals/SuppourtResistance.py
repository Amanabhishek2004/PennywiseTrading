from datetime import datetime
from dateutil import parser  # pip install python-dateutil
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
            .order_by(PriceData.date.asc())
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
        .order_by(PriceData.date.asc())
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

from datetime import datetime

def MakeStrongSupportResistance(ticker, db, period, prices, stock_data):
    if not stock_data:
        raise ValueError(f"Stock with ticker {ticker} not found in the database.")

    current_price = stock_data.CurrentPrice  

    # --- Parse last_updated properly ---
    last_updated = None
    if stock_data.updated:
        if isinstance(stock_data.updated, datetime):
            last_updated = stock_data.updated
        else:
            try:
                last_updated = parser.parse(str(stock_data.updated))
                print("[INFO] Parsed updated field:", last_updated)
            except Exception:
                print(f"[WARN] Failed to parse updated field: {stock_data.updated}")

    # --- Base query ---
    query = prices.filter(
        PriceData.stock_id == stock_data.id,
        PriceData.period == period,
        PriceData.close_price >= current_price * 0.9,
        PriceData.close_price <= current_price * 1.1,
        PriceData.date >= stock_data.updated if stock_data.updated else "",
    )

    # --- Apply last_updated filter if available ---
    Prices = query.order_by(PriceData.date.asc()).all()
    print(f"[DEBUG] MakeStrong levels Loaded {len(Prices)} candles for {ticker} [{period}]")

    if not Prices:
        return {"message": "No new prices to process", "Ticker": ticker, "Period": period}

    # --- Convert to DataFrame ---
    data = pd.DataFrame({
        "Date": [p.date for p in Prices],
        "Low": [p.low_price for p in Prices],
        "High": [p.high_price for p in Prices],
        "Close": [p.close_price for p in Prices],
    })

    if data.empty:
        return {"message": "Empty DataFrame after query", "Ticker": ticker, "Period": period}

    # Rolling min/max for support/resistance zones
    data["RoundedLow"] = data["Low"].rolling(window=10, min_periods=1).min()
    data["RoundedHigh"] = data["High"].rolling(window=10, min_periods=1).max()

    def conditional_round(price):
        if pd.isna(price):
            return None
        return round(price, 1) if price < 50 else round(price)

    data["RoundedLow"] = data["RoundedLow"].apply(conditional_round)
    data["RoundedHigh"] = data["RoundedHigh"].apply(conditional_round)
    data.dropna(subset=["RoundedLow", "RoundedHigh"], inplace=True)

    # Count levels
    suppourtdata = data[["RoundedLow"]].value_counts().reset_index()
    suppourtdata.columns = ["Low", "count_x"]

    resistancedata = data[["RoundedHigh"]].value_counts().reset_index()
    resistancedata.columns = ["High", "count_y"]

    merged_data = suppourtdata.merge(
        resistancedata, how="inner", left_on="Low", right_on="High"
    )
    merged_data["count"] = merged_data["count_x"] + merged_data["count_y"]

    supports = merged_data[(merged_data["Low"] < current_price)].sort_values(
        by="count", ascending=False
    ).head(4)

    resistances = merged_data[(merged_data["Low"] > current_price)].sort_values(
        by="count", ascending=False
    ).head(4)

    strong_levels = pd.concat([supports, resistances]).reset_index(drop=True)

    # --- Insert/Update support/resistance in DB ---
    for _, row in strong_levels.iterrows():
        existing = db.query(SupportData).filter(
            SupportData.stock_id == stock_data.id,
            SupportData.Price == float(row["Low"]),
            SupportData.period == period,
            SupportData.Pattern == "Strong Levels"
        ).first()

        if existing:
            existing.retests = int(row["count"])
        else:
            suppourt = SupportData(
                stock_id=stock_data.id,
                Price=float(row["Low"]),
                period=period,
                Pattern="Strong Levels",
                retests=int(row["count"]),
            )
            db.add(suppourt)
    print(strong_levels)
    # ⚠️ Removed db.commit() → caller should commit at API/service layer
    return {
        "Ticker": ticker,
        "Period": period,
        "Levels": strong_levels.to_dict(orient="records"),
    }


from datetime import datetime
from sqlalchemy import cast, String, DateTime
from datetime import datetime

from dateutil import parser
from sqlalchemy import func, cast, DateTime

def CreatepatternSuppourt(Ticker, db, period, price_query, stock_data):
    if not stock_data:
        return {"error": "Stock not found"}

    current_price = stock_data.CurrentPrice

    # --- Parse last_time properly ---

    # --- Base query ---
    price_query = price_query.filter(
        PriceData.stock_id == stock_data.id,
        PriceData.period == period,
        PriceData.close_price.between(current_price * 0.9, current_price * 1.1) , 
        PriceData.date >= stock_data.updated if stock_data.updated else "",
    ).order_by(PriceData.date.asc())

    # --- Filter by last_updated safely ---
       
    short_termprices = price_query.all()
    print(f"[DEBUG] Loaded {len(short_termprices)} candles for {Ticker} [{period}]")
    if not short_termprices:
        return {
            "message": "No new candles to process",
            "Ticker": Ticker,
            "Period": period
        }

    # --- Identify patterns ---
    patterns = []
    for idx, price in enumerate(short_termprices):
        data = IdentifySingleCandleStickPattern(price, period)
        if not data and idx > 0:
            data = IdentifyDoubleCandleStickPatterns(short_termprices[idx-1:idx+1], period)
        if data:
            patterns.append(data)

    # --- Bulk fetch existing patterns once ---
    all_existing = db.query(SupportData).filter(
        SupportData.stock_id == stock_data.id,
        SupportData.period == period
    ).all()
    existing_map = {round(e.Price, 2): e for e in all_existing}

    processed_levels = set()
    new_patterns = []

    for data in patterns:
        price_level = data.get("Suppourt") or data.get("Resistance")
        if not price_level or price_level in processed_levels:
            continue
        processed_levels.add(price_level)

        tolerance = 0.008 * price_level
        key = round(price_level, 2)

        if key in existing_map and abs(existing_map[key].Price - price_level) <= tolerance:
            existing_map[key].retests += 1
            existing_map[key].Pattern = data["pattern"]
            existing_map[key].timestamp = str(data["time"])
        else:
            new_patterns.append(SupportData(
                stock_id=stock_data.id,
                Price=price_level,
                period=period,
                Pattern=data["pattern"],
                timestamp=str(data["time"]),
                retests=1
            ))

    if new_patterns:
        db.bulk_save_objects(new_patterns)

    # --- Update StockTechnicals (support/resistance) ---
    support = db.query(SupportData.Price, SupportData.Pattern, SupportData.timestamp).filter(
        SupportData.stock_id == stock_data.id,
        SupportData.period == period,
        SupportData.Price < current_price
    ).order_by(SupportData.Price.desc()).first()

    resistance = db.query(SupportData.Price, SupportData.Pattern, SupportData.timestamp).filter(
        SupportData.stock_id == stock_data.id,
        SupportData.period == period,
        SupportData.Price > current_price
    ).order_by(SupportData.Price.asc()).first()

    technical = db.query(StockTechnicals).filter(
        StockTechnicals.stock_id == stock_data.id,
        StockTechnicals.period == period
    ).first()

    if technical:
        technical.CurrentSupport = support.Price if support else None
        technical.CurrentResistance = resistance.Price if resistance else None
    else:
        db.add(StockTechnicals(
            stock_id=stock_data.id,
            ticker=Ticker,
            period=period,
            CurrentSupport=support.Price if support else None,
            CurrentResistance=resistance.Price if resistance else None
        ))

    # ⚠️ Removed db.commit() → should be committed outside at API level
    return {
        "Support": support.Price if support else None,
        "Resistance": resistance.Price if resistance else None,
        "Support_pattern": support.Pattern if support else None,
        "Resistance_pattern": resistance.Pattern if resistance else None,
        "Ticker": Ticker,
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


