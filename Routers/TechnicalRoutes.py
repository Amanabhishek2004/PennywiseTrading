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
from Stock.Technicals.rsiStrategy import *
from Stock.Technicals.SuppourtResistance import CreatepatternSuppourt , MakeStrongSupportResistance , IdentifyDoubleCandleStickPatterns , IdentifySingleCandleStickPattern
from Database.Schemas.PriceSchema import *
from Stock.Technicals.SignalGenerator import *
from Stock.Technicals.DynamicSuppourtResistance import *
from pydantic import BaseModel

from typing import Optional, Dict, Any, List
from Routers.UserAccountRoutes import *

router = APIRouter(prefix="/Stock", tags=["Technical Routes"])


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


class InputData(BaseModel):
    ticker: str
    period: str = "1m"
    timeperiod: int = 30


class responseData(BaseModel):
    channels: List[float] = []


class ChannelData(BaseModel):
    Slope: float
    Intercept: float
    Channel: List[float]


class ChannelResponse(BaseModel):
    UpperChannelData: ChannelData
    LowerChannelData: ChannelData


ADMINAPIKEY = [
    "0UGhhKVqW1ofy0osb1dOcvabBS1vQZQHi4hKATs73an5pZY2xvv50xtnk0U",
    "RqKwwgDKIgRSeSIN9F5LoKnUPSPbY6aZoVYh7gFaSSqzD6DgGeyJNRx9gBA",
]


@router.post("/StockChannels/", response_model=ChannelResponse)
def GetStockChannels(
    apikey: str,
    input_data: InputData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException()

    channels = CreateChannel(
        db,
        Ticker=input_data.ticker,
        period=input_data.period,
        timeperiod=input_data.timeperiod,
    )
    track_read_and_data_usage(db, current_user.id, channels)
    return channels


@router.get("/GetSupportResistances/{ticker}", response_model=Dict[str, Any] )
def GetSupportResistance(
    ticker: str,
    period,
    apikey: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):   
    # raise HTTPException(status_code=404, detail="Stock not found")
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    DATA = CreatepatternSuppourt(ticker, db, period)
    print("data" , DATA)
    track_read_and_data_usage(db, current_user.id, DATA)
    return {"data" : DATA}


@router.get("/allSuppourts/{ticker}")
def get_all_supports(ticker: str, db: Session = Depends(get_db) , period: str = "1d"    ):
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    supports = db.query(SupportData).filter(SupportData.stock_id == stock.id , SupportData.period == period ).all()
    
    return supports


@router.post("/SuppourtResistance")
def CreateSuppourtResistances(
    ticker: str,
    apikey: str,
    db: Session = Depends(get_db),
    period: str = "1d",
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    data = MakeStrongSupportResistance(ticker, db, period)
    track_read_and_data_usage(db, current_user.id, data)
    return {"detail": "success"}


@router.patch("/CreateSuppourtResistances/")
def CreateNewLevels(
    ticker: str,
    apikey: str,
    db: Session = Depends(get_db),
    period: str = "1d",
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    data = CreatepatternSuppourt(ticker, db, period)
    track_read_and_data_usage(db, current_user.id, data)

    return {"Data": data}


@router.get("/GetPrices/", response_model=List[PriceDataResponse])
def getallPrices(
    ticker: str,
    period: str,
    apikey: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    prices = (
        db.query(PriceData)
        .join(Stock)
        .filter(PriceData.period == period, Stock.Ticker == ticker)
        .offset(skip)
        .limit(limit)
        .all()
    )
    track_read_and_data_usage(db, current_user.id, prices)
    return prices


@router.get("/GenerateSignals/{ticker}", response_model=SignalResponseSchema)
def GenerateBuySellSignals(
    ticker: str,
    apikey: str,
    db: Session = Depends(get_db),
    period: str = "1d",
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    prices = (
        db.query(PriceData)
        .join(Stock)
        .filter(PriceData.period == period, Stock.Ticker == ticker)
        .all()
    )
    signal = GenrateSignals(ticker, db, period)
    stock_data = db.query(Stock).filter(Stock.Ticker == ticker).first()
    currentprice = float(stock_data.CurrentPrice)
    tolerance = 0.008 * currentprice
    
    support = (
        db.query(SupportData)
        .filter(
            SupportData.stock_id == stock_data.id,
            SupportData.period == period,
            SupportData.Price >= currentprice - tolerance,
            SupportData.Price <= currentprice + tolerance,
        )
        .first()
    )

    message = None
    if support and signal["RSI Signal"]["Rsi"] < 35:
        message = f"Buy at {float(support.Price)}"
    if signal["RSI Signal"].get("rsipeak_min") and signal["RSI Signal"]["Rsi"] < 35:
        message = (
            f"Buy at {currentprice} or {float(support.Price) if support else None}"
        )

    patterdata = IdentifyDoubleCandleStickPatterns(prices[-2:], period)
    patterdata2 = IdentifySingleCandleStickPattern(prices[-1], period)

    def to_py(val):
        return val.item() if hasattr(val, "item") else val


    result = SignalResponseSchema(
        Signal={k: {ik: to_py(iv) for ik, iv in v.items()} for k, v in signal.items()},
        message=message,
        Support=float(support.Price) if support else None,
        PriceAction=[to_py(patterdata), to_py(patterdata2)],
    )

    track_read_and_data_usage(db, current_user.id, result)
    return result


@router.get("/SwingPoints/{ticker}" )
def GetSwingPoints(
    ticker: str,
    apikey: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan), 
    period : str ="1d"
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    data = CalculateSwingPoints(ticker, db , period)
    track_read_and_data_usage(db, current_user.id, data)
    return data[0]


@router.get("/Vwap/{ticker}")
def CalculateVwap(
    ticker: str,
    apikey: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    expiredplans: list[Plan] = Depends(CheckForPremiumExpiry),
    utilizedplan: Plan = Depends(CheckForTechnicalApiPlan),
):
    if apikey not in ADMINAPIKEY and utilizedplan in expiredplans:
        raise HTTPException(status_code=403, detail="Your premium plan has expired.")

    return { 
        "detail" : "Route Comming Soon"
    } 


