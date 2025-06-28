from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
import pandas as pd
import yfinance
from Database.models import * 
from Stock.Technicals.StockChannels import CreateChannel
from typing import List
from Database.Schemas.StockSchema import *
import math
from Stock.Fundametals.Stock import * 
from Stock.Technicals.rsiStrategy import *
from Stock.Technicals.SuppourtResistance import *
from Database.Schemas.PriceSchema import *
from Stock.Technicals.SignalGenerator  import * 
# Pennywise


router = APIRouter(prefix="/Stock", tags=["Technical Routes"])



class InputData(BaseModel):
    ticker: str
    period : str = "1m"
    timeperiod : int = 30     


class responseData(BaseModel):
    channels: List[float] = []


class ChannelData(BaseModel):
    Slope: float
    Intercept: float
    Channel: List[float]

class ChannelResponse(BaseModel):
    UpperChannelData: ChannelData
    LowerChannelData: ChannelData

@router.post("/StockChannels/", response_model=ChannelResponse) 
def GetStockChannels(input_data: InputData, db: Session = Depends(get_db) ):
    """
    Get stock channels for a given ticker.
    """
    try:
        channels = CreateChannel(db , Ticker=input_data.ticker, period =input_data.period , timeperiod=input_data.timeperiod)  # Example time period from input
        print(channels)
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 


@router.get("/GetSuppourtResistance" , response_model=dict )
def GetSupportResistance(ticker: str, db: Session = Depends(get_db) , period :str = "1d"):
    """
    Get support and resistance levels for a given ticker.
    """
    try:
        stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")

        DATA = UpdateSuppourt(ticker , db , period)
        return DATA
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.post("/SuppourtResistance" , response_model=dict )
def CreateSuppourtResistances(ticker: str, db: Session = Depends(get_db) , period :str = "1d"):  
    data = MakeStrongSupportResistance(ticker , db , period)
    return {"detail" : "success"}



#  ALGO  
@router.patch("/CreateSuppourtResistances/")
def CreateNewLevels(db: Session = Depends(get_db) , period : str = "1d"):
    data = CreatepatternSuppourt("RELIANCE" , db ,  period)
    return {
        "DATA":data
    }

@router.get("/GetPrices/" , response_model = List[PriceDataResponse])
def getallPrices(ticker , period , db: Session = Depends(get_db)) :
        prices = (
        db.query(PriceData).join(Stock)
        .filter(PriceData.period == period, Stock.Ticker == ticker)
        .all()
    )      
        return prices




from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class RSISignalSchema(BaseModel):
    Buy: bool
    Sell: bool
    StrongSell: bool
    StrongBuy: bool
    rsipeak: Optional[float]
    Rsi: Optional[float]

class MASignalSchema(BaseModel):
    Buy: bool
    Sell: bool

class VolumeSignalSchema(BaseModel):
    peakDIv: Optional[bool]
    Suppourt: Optional[float]
    Resistance: Optional[float]
    normalizedobv: Optional[float]
    CurrentObv: Optional[float]
    lowerchannel: Optional[float]

class SignalResponseSchema(BaseModel):
    Signal: Dict[str, Any]
    message: Optional[str]
    Support: Optional[float]
    PriceAction: Optional[Any]






@router.get("/GenerateSignals/{ticker}", response_model=SignalResponseSchema)
def GenerateBuySellSignals(ticker: str, db: Session = Depends(get_db), period: str = "1d"):
    prices = (
        db.query(PriceData).join(Stock)
        .filter(PriceData.period == period, Stock.Ticker == ticker)
        .all())
    signal = GenrateSignals(ticker, db, period)
    print(signal)
    stock_data = db.query(Stock).filter(Stock.Ticker == ticker).first()
    currentprice = float(stock_data.CurrentPrice)
    tolerance = 0.008 * currentprice
    support = (
        db.query(SupportData).filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price >= currentprice - tolerance,
            SupportData.Price <= currentprice + tolerance
        ).first())
    message = None
    if support and signal["RSI Signal"]["Rsi"] < 35:
        message = f"Buy at {float(support.Price)}"
    if signal["RSI Signal"]["rsipeak"] and signal["RSI Signal"]["Rsi"] < 35:
        message = f"Buy at {currentprice} or {float(support.Price) if support else None}"
    if signal["RSI Signal"]["Sell"] and signal["MA Signal"]["Sell"]:
        message = f"Sell at {currentprice}"

    patterdata = IdentifyDoubleCandleStickPatterns(prices[-2:], period)
    patterdata2 = IdentifySingleCandleStickPattern(prices[-1], period)
    def to_py(val):
        # Convert numpy types to Python native types
        if hasattr(val, "item"):
            return val.item()
        return val
    return SignalResponseSchema(
        Signal={k: {ik: to_py(iv) for ik, iv in v.items()} for k, v in signal.items()},
        message=message,
        Support=float(support.Price) if support else None,
        PriceAction=[to_py(patterdata), to_py(patterdata2)]
    )