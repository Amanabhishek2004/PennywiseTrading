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
import pandas as pd
from dateutil import parser

def MakeStrongSupportResistance(ticker, db, period, prices=None, stock_data=None):
    if not stock_data:
        stock_data = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if not stock_data:
            return {"message": f"Stock with ticker {ticker} not found"}

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

    # ================================
    # Case 1: No prices passed → fetch from DB
    # ================================
    if prices is None:
        prices = db.query(PriceData).filter(
            PriceData.stock_id == stock_data.id,
            PriceData.period == period,
            PriceData.close_price >= current_price * 0.7,   # -30%
            PriceData.close_price <= current_price * 1.3,   # +30%
        )
        if last_updated:
            prices = prices.filter(PriceData.date >= last_updated)

        Prices = prices.order_by(PriceData.date.asc()).all()

        data = pd.DataFrame({
            "Date": [p.date for p in Prices],
            "Low": [p.low_price for p in Prices],
            "High": [p.high_price for p in Prices],
            "Close": [p.close_price for p in Prices],
            "OnBalanceVolume": [getattr(p, "onbalancevolume", None) for p in Prices],
            "RSI": [getattr(p, "rsi", None) for p in Prices],
        })

    # ================================
    # Case 2: prices is a dict/list of dicts
    # ================================
    elif isinstance(prices, (dict, list)):
        data = pd.DataFrame(prices)

        # Ensure required columns exist
        required_cols = {"date", "low_price", "high_price", "close_price"}
        missing = required_cols - set(data.columns)
        if missing:
            raise ValueError(f"Missing columns in price data: {missing}")

        # Rename consistently
        rename_map = {
            "date": "Date",
            "low_price": "Low",
            "high_price": "High",
            "close_price": "Close",
            "onbalancevolume": "OnBalanceVolume",
            "rsi": "RSI",
        }
        data.rename(columns=rename_map, inplace=True)

        # Convert Date (string → datetime)
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")

        # Ensure OBV/RSI columns exist
        if "OnBalanceVolume" not in data:
            data["OnBalanceVolume"] = None
        if "RSI" not in data:
            data["RSI"] = None

        # Filter by ±30% of current price
        data = data[
            (data["Close"] >= current_price * 0.7) &
            (data["Close"] <= current_price * 1.3)
        ]

    # ================================
    # Case 3: prices is already a query object
    # ================================
    else:
        Prices = prices.filter(
            PriceData.close_price >= current_price * 0.7,
            PriceData.close_price <= current_price * 1.3,
        ).order_by(PriceData.date.asc()).all()

        data = pd.DataFrame({
            "Date": [p.date for p in Prices],
            "Low": [p.low_price for p in Prices],
            "High": [p.high_price for p in Prices],
            "Close": [p.close_price for p in Prices],
            "OnBalanceVolume": [getattr(p, "OnBalanceVolume", None) for p in Prices],
            "RSI": [getattr(p, "RSI", None) for p in Prices],
        })

    # ================================
    # If no data found
    # ================================
    if data.empty:
        return {"message": "No price data found", "Ticker": ticker, "Period": period}

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

    return {
        "Ticker": ticker,
        "Period": period,
        "Levels": strong_levels.to_dict(orient="records"),
    }


import pandas as pd

def CreatepatternSuppourt(df: pd.DataFrame, ticker: str, db, period: str, current_price: float = None, channel=None, stock_data=None):

    if df.empty:
        return {
            "message": "No new candles to process",
            "Ticker": ticker,
            "Period": period
        }

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=True)

    # --- Identify patterns ---
    patterns = []
    for i in range(len(df)):
        row = df.iloc[i]
        data = identify_single_candle_pattern(row, period, channel)
        if not data and i > 0:
            prev_row = df.iloc[i - 1]
            data = identify_double_candle_patterns(prev_row, row, period, channel)
        if data:
            patterns.append(data)

    # --- Aggregate into support/resistance entries ---
    processed_levels = set()
    entries = []
    existing_map = {}  # key: rounded price, value: entry dict

    for data in patterns:
        price_level = data.get("Suppourt") or data.get("Resistance")
        if not price_level:
            continue

        if price_level in processed_levels:
            continue
        processed_levels.add(price_level)

        tolerance = 0.008 * price_level
        key = round(price_level, 2)

        if key in existing_map and abs(existing_map[key]["Price"] - price_level) <= tolerance:
            existing_map[key]["retests"] += 1
            existing_map[key]["Pattern"] = data["pattern"]
            existing_map[key]["timestamp"] = str(data["time"])
        else:
            entry = {
                "Price": price_level,
                "period": period,
                "Pattern": data["pattern"],
                "timestamp": str(data["time"]),
                "retests": 1
            }
            existing_map[key] = entry
            entries.append(entry)

    # --- Create SupportData instances in DB ---
    if stock_data is not None:
        for e in entries:
            existing = db.query(SupportData).filter(
                SupportData.stock_id == stock_data.id,
                SupportData.Price == float(e["Price"]),
                SupportData.period == period,
                SupportData.Pattern == e["Pattern"]
            ).first()

            if existing:
                existing.retests = int(e["retests"])
                existing.timestamp = e["timestamp"]
            else:
                supp_instance = SupportData(
                    stock_id=stock_data.id,
                    Price=float(e["Price"]),
                    period=period,
                    Pattern=e["Pattern"],
                    retests=int(e["retests"]),
                    timestamp=e["timestamp"]
                )
                db.add(supp_instance)
        db.commit()

    # --- Final support/resistance relative to current price ---
    support, resistance = None, None
    if current_price is not None:
        supports = [e for e in entries if e["Price"] < current_price]
        resistances = [e for e in entries if e["Price"] > current_price]
        support = max(supports, key=lambda x: x["Price"], default=None)
        resistance = min(resistances, key=lambda x: x["Price"], default=None)

    return {
        "Ticker": ticker,
        "Period": period,
        "Support": support["Price"] if support else None,
        "Resistance": resistance["Price"] if resistance else None,
        "Support_pattern": support["Pattern"] if support else None,
        "Resistance_pattern": resistance["Pattern"] if resistance else None,
        "Entries": entries
    }


def identify_single_candle_pattern(price, period, channels=None):
    body = abs(price.open_price - price.close_price)
    uppershadow = price.high_price - max(price.open_price, price.close_price)
    lowershadow = min(price.open_price, price.close_price) - price.low_price

    rsi = getattr(price, "RSI", None)

    # Detect trend using channel slopes
    lower_slope = channels.get("LowerChannelData", {}).get("Slope", 0) if channels else 0
    upper_slope = channels.get("UpperChannelData", {}).get("Slope", 0) if channels else 0

    downtrend = lower_slope < 0 and upper_slope < 0
    uptrend = lower_slope > 0 and upper_slope > 0

    # Hammer
    if downtrend and rsi is not None and rsi < 30 and body > 0 and uppershadow <= 0.02 * body and lowershadow >= 1.5 * body:
        return {"Suppourt": price.low_price, "pattern": "Hammer", "time": price.date, "period": period}

    # Shooting Star
    if uptrend and rsi is not None and rsi > 70 and body > 0 and uppershadow >= 2 * body and lowershadow <= 0.2 * body:
        return {"Resistance": price.high_price, "pattern": "Shooting Star", "time": price.date, "period": period}

    # Doji
    if body <= 0.1 * (price.high_price - price.low_price):
        if downtrend and rsi is not None and rsi < 30 and uppershadow == 0 and lowershadow > 0:
            return {"Suppourt": price.low_price, "pattern": "T", "time": price.date, "period": period}
        elif uptrend and rsi is not None and rsi > 70 and lowershadow == 0 and uppershadow > 0:
            return {"Resistance": price.high_price, "pattern": "Inverted T", "time": price.date, "period": period}
        elif uppershadow > 0 and lowershadow > 0:
            return {"Resistance": price.close_price, "pattern": "Doji", "time": price.date, "period": period}

    return None


def identify_double_candle_patterns(first, second, period, channels=None):
    o1, c1 = first.open_price, first.close_price
    o2, c2 = second.open_price, second.close_price

    # Detect trend using channel slopes
    lower_slope = channels.get("LowerChannelData", {}).get("Slope", 0) if channels else 0
    upper_slope = channels.get("UpperChannelData", {}).get("Slope", 0) if channels else 0

    downtrend = lower_slope < 0 and upper_slope < 0
    uptrend = lower_slope > 0 and upper_slope > 0

    # Bullish reversal (downtrend)
    if downtrend and (first.RSI < 30 or second.RSI < 30):
        if c1 < o1 and c2 > o2 and c1 > o2 and o1 < c2:  # Engulfing
            return {"Suppourt": min(second.low_price, first.low_price), "pattern": "Bullish Engulfing", "time": second.date, "period": period}
        midpoint = o1 + (c1 - o1) / 2
        if c1 < o1 and o2 < c1 and c2 > midpoint and c2 < o1:  # Piercing
            return {"Suppourt": min(second.low_price, first.low_price), "pattern": "Piercing Pattern", "time": second.date, "period": period}
        if second.low_price > first.high_price:  # Rising Window
            return {"Suppourt": second.low_price, "pattern": "Rising Window", "time": second.date, "period": period}

    # Bearish reversal (uptrend)
    if uptrend and (first.RSI > 70 or second.RSI > 70):
        if c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:  # Engulfing
            return {"Resistance": max(second.high_price, first.high_price), "pattern": "Bearish Engulfing", "time": second.date, "period": period}
        midpoint = o1 + (c1 - o1) / 2
        if c1 > o1 and o2 > c1 and c2 < midpoint and c2 > o1:  # Dark Cloud
            return {"Resistance": max(second.high_price, first.high_price), "pattern": "Dark Cloud Cover", "time": second.date, "period": period}
        if second.high_price < first.low_price:  # Falling Window
            return {"Resistance": second.high_price, "pattern": "Falling Window", "time": second.date, "period": period}

    return None

