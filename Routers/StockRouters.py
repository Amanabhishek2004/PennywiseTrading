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



@router.get("/stocks", response_model=List[StockSearchschema])
def get_all_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()
    return stocks



@router.get("/stocks/{ticker}", response_model=StockSchema)
def get_all_stocks(ticker: str , db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.Ticker == ticker).first()
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
               UpdateAllTechnicaldata(stock, db , current_user=current_user)

    stocks = db.query(Stock).filter(Stock.Ticker.in_(tickers)).all()

    if not stocks:
        raise HTTPException(status_code=404, detail="No stocks found")

    return stocks



# Assuming StockSchema is defined like this:



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

