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
    period : int  = 20  

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
def GetStockChannels(input_data: InputData, db: Session = Depends(get_db)):
    """
    Get stock channels for a given ticker.
    """
    try:
        channels = CreateChannel(input_data.ticker, input_data.period)  # Example time period from input
        print(channels)
        return channels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 


``
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

@router.get("/GenerateSignals/")
def GenerateBuySellSignals(db: Session = Depends(get_db)) : 
      ticker = "20MICRONS"
      signal =  GenrateSignals(ticker , db , "1d") 
      return signal
 
