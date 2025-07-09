from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
import pandas as pd
import yfinance
from Database.models import * 
from typing import List
from Database.Schemas.StockSchema import *
import math
from Stock.Technicals.rsiStrategy import CalculateRSI
from Stock.Technicals.StockChannels import *    
from Stock.Technicals.SignalGenerator import * 
from Routers.AdminRouter import * 
from Stock.Technicals.SuppourtResistance import * 
from Routers.UserAccountRoutes import get_current_user

router = APIRouter(prefix="/Stock", tags=["Stocks"])



@router.get("/stocks", response_model=List[StockSchema])
def get_all_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()[:20]
    return stocks





class PeersRequest(BaseModel):
    tickers: List[str]

@router.post("/peerstocks/", response_model=List[StockSchema])
def GetPeers(request: PeersRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tickers = request.tickers
    print(tickers) 
    # Validate all tickers exist
    for stock in tickers:
        if not isinstance(stock, str):
            raise HTTPException(status_code=400, detail="Ticker must be a string")
        if db.query(Stock).filter(Stock.Ticker == stock).first() is None:
            raise HTTPException(status_code=400, detail=f"Stock not found: {stock}")

        data = db.query(Stock).filter(Stock.Ticker == stock).first()
        if len(data.pricedata) == 0:
            update_single_ticker(stock, db)
        if len(data.technicals) == 0:
            print("Channels done")
            CreateChannel(db , stock , period="1m")
            CreateChannel(db , stock , period="1d")
            CreateChannel(db , stock , period="30m")

            print(" Rsi Channels done")

            CalculateRSI( stock,db , period = "1m")
            CalculateRSI( stock,db , period = "1d")
            CalculateRSI( stock,db , period = "30m")



        # CREATE LEVELS  



            MakeStrongSupportResistance(stock , db , "1m")
            MakeStrongSupportResistance(stock , db , "1d")
            MakeStrongSupportResistance(stock , db , "30m")


            #  levels due to patterns  
            CreateNewLevels(stock  , db )



        else:
               UpdateAllTechnicaldata(stock, db)

    stocks = db.query(Stock).filter(Stock.Ticker.in_(tickers)).all()

    if not stocks:
        raise HTTPException(status_code=404, detail="No stocks found")

    return stocks



# Assuming StockSchema is defined like this:


@router.patch("/update/{ticker}", response_model=dict)
def UpdateStockPrice(ticker: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Fetch stock from the database
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Fetch current price
    data = yfinance.Ticker(f"{ticker}.NS").info
    stock.CurrentPrice = data.get("currentPrice")

    #  Update the rsi 
    stock.technicals.RsiSlope = CalculateRSI(ticker)["trend"]
    stock.technicals.Rsiintercept = CalculateRSI(ticker)["intercept"]
    stock.technicals.CurrentRsi = CalculateRSI(ticker)["Current RSI"]
    #  Update the trendline 
    stock.trendlines.slope = CalculatePricetrend(ticker)["Trend"] 
    stock.trendlines.intercept = CalculatePricetrend(ticker)["intercept"]  
    #  Update the channels
    stock.channels.upper_channel_slope , stock.channels.upper_channel_intercept = CreateUpperChannel(stock.ticker)
    stock.channels.lower_channel_slope , stock.channels.lower_channel_intercept = CreateLowerChannel(stock.ticker)
    
      
    # Fetch historical data
    yfinance_data = yfinance.Ticker(f"{ticker}.NS").history(period="2d")

    # Calculate percentage change if data is available
    pct_change = None
    if not yfinance_data.empty and "Close" in yfinance_data.columns:
        yfinance_data["Close"] = yfinance_data["Close"].pct_change(1)
        pct_change = yfinance_data["Close"].iloc[-1] if not yfinance_data.empty else None
    
    # signal = 

    # Handle invalid pct_change (e.g., NaN)
    if pct_change is not None and (pd.isna(pct_change) or pd.isnull(pct_change)):
        pct_change = None

    # Commit changes to the database
    db.commit()
    db.refresh(stock)

    # Serialize the stock object
    stock_data = {
        "id": stock.id,
        "Ticker": stock.Ticker,
        "CurrentPrice": stock.CurrentPrice,
        "pct_change": pct_change,
    }

    return {"stock": stock_data}


@router.post("/update/comparables/")
def update_all_comparables(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()
    updated = []
    failed = []

    for stock in stocks:
        try:
            result = update_comparables(stock, db)
            updated.append(stock.Ticker)
        except Exception as e:
            print(f"Failed to update comparables for {stock.Ticker}: {e}")
            failed.append({"Ticker": stock.Ticker, "error": str(e)})

    return {
        "message": "Comparables update complete",
        "updated_stocks": updated,
        "failed_stocks": failed,
        "success_count": len(updated),
        "failure_count": len(failed)
    }

