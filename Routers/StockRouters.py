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
from Routers.UserAccountRoutes import get_current_user , verify_premium_access
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


router = APIRouter(prefix="/Stock", tags=["Stocks"] 
                #    dependencies= [Depends(verify_premium_access)]
                   )


@router.get("/", response_model=List[StockSearchschema])
def get_all_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()
    return stocks




@router.get("/StockDetails", response_model=List[StockSearchschema])
def get_all_stocks(db: Session = Depends(get_db)):
    stocks = db.query(Stock).all()

    def is_valid(stock):
        try:
            return not any(
                math.isnan(getattr(stock, field))
                for field in [
                    "TechnicalIntradayScore",
                    "FinancialScore",
                    "TechnicalDailyScore"
                ]
            )
        except TypeError:
            # If any field is None (not float), skip NaN check and allow it
            return True

    # Filter out stocks with any NaN float field
    valid_stocks = list(filter(is_valid, stocks))
    return valid_stocks


@router.get("/{ticker}", response_model=StockSchema)
def get_all_stocks(ticker: str , db: Session = Depends(get_db)):
    print(ticker)
    stocks = db.query(Stock).filter(Stock.Ticker == ticker).first()
    return stocks



class PeersRequest(BaseModel):
    tickers: List[str]

@router.post("/peerstocks/", response_model=List[StockSchema])
def GetPeers(request: PeersRequest,
              db: Session = Depends(get_db)):
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

            print(" Rsi Channels done")

            CalculateRSI( stock,db , period = "1m")
            CalculateRSI( stock,db , period = "1d")

        # CREATE LEVELS  


            MakeStrongSupportResistance(stock , db , "1m")
            MakeStrongSupportResistance(stock , db , "1d")



            #  levels due to patterns  
            CreateNewLevels(stock  , db )
        else:
               UpdateAllTechnicaldata(stock, db)

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

