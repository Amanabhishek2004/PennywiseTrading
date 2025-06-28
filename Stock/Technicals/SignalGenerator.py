from .rsiStrategy import *
from .Meanreversion import *


# RSI DIVERGANCE WITH PRICE ABOVE UPPER BBAND STRONG SELL
# RSI DIVERGANCE  -- SELL OR BUY BUT WITH RSI BELOW 30 OR ABOVE 70 STRONG SIGNALS
#  sell at resistance and buy at suppourt

from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np


def GenrateSignals(ticker, db, period):
    """
    Generate trading signals based on RSI divergence, channel data, and volume analysis for a given stock ticker.
    """
    # Fetch price data from the database
    Prices = (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.period == period)
        .all()
    )
  
    closingprices = [price.close_price for price in Prices]
    obvs = [price.OnbalanceVolume for price in Prices[:-1]]

    if not closingprices or not obvs:
        return {"error": "Insufficient data for the ticker."}

    Currentobv = Prices[-1].OnbalanceVolume

    # Fetch technical and channel data
    technicaldata = (
        db.query(StockTechnicals)
        .join(Stock)
        .filter(Stock.Ticker == ticker, StockTechnicals.period == period)
        .first()
    )
    channel = (
        db.query(Channel)
        .join(Stock)
        .filter(Stock.Ticker == ticker, Channel.period == period)
        .first()
    )

    if not technicaldata or not channel:
        return {"error": "Required data not found in database."}

    # Fetch live price data
    try:
        data = yf.Ticker(f"{ticker}.NS").history(period="1d", interval="1m")
    except Exception as e:
        return {"error": f"Failed to fetch data from Yahoo Finance: {e}"}

    price = data.iloc[-1]["Close"]
    rsislope = technicaldata.RsiSlope
    currentrsi = technicaldata.CurrentRsi
    lowerchannelslope = channel.lower_channel_slope
    lowervaolumechannel = technicaldata.VolumeLowerChannelSlope
    # Moving Averages
    closingprices_series = pd.Series(closingprices)
    DMA20 = (
        closingprices_series.rolling(20).mean().iloc[-1]
        if len(closingprices) >= 20
        else None
    )
    DMA50 = (
        closingprices_series.rolling(50).mean().iloc[-1]
        if len(closingprices) >= 50
        else None
    )

    # Normalized OBV
    std = np.std(obvs[-20:])
    mean = np.mean(obvs[-20:])
    normalized_volscore = (Currentobv - mean) / std

    # RSI Signals
    rsipeak = CalculateRSIpeakMaxmin(
        db, price, currentrsi, datetime.now().isoformat(), period, interval=70
    )
    Rsisignal = {
        "Buy": False,
        "Sell": False,
        "StrongSell": False,
        "StrongBuy": False,
        "rsipeak": rsipeak, 
        "Rsi" : currentrsi
    }
    masignal = {
        "Buy": DMA20 > DMA50 if DMA20 and DMA50 else False,
        "Sell": DMA50 > DMA20 if DMA20 and DMA50 else False,
    }
    #  create volume profiles        

    if lowerchannelslope > 0:
        if not rsipeak and rsislope < 0 and currentrsi > 70:
            Rsisignal["Sell"] = True
            Rsisignal["StrongSell"] = True
        if rsipeak and rsislope < 0:
            Rsisignal["Buy"] = True
        if rsipeak and currentrsi <= 30:
            Rsisignal["Buy"] = True
    elif lowerchannelslope < 0:
        if not rsipeak and rsislope > 0 and currentrsi < 30:
            Rsisignal["Buy"] = True
            Rsisignal["StrongBuy"] = True
        if rsipeak and rsislope > 0:
            Rsisignal["Sell"] = True

    # Volume Signals
    volumepeaks = CalculateVolumepeakmaxmin(
        db, datetime.now().isoformat(), ticker, period, 20
    )
    volumesignal = {
        "peakDIv": (lowervaolumechannel) * (lowerchannelslope) > 0,
        "Suppourt": volumepeaks.get("min") if volumepeaks else None,
        "Resistance": volumepeaks.get("max") if volumepeaks else None,
        "normalizedobv": normalized_volscore,
        "CurrentObv": Currentobv,
        "lowerchannel" : lowervaolumechannel
    }
    return {
        "RSI Signal": Rsisignal,
        "MA Signal": masignal,
        "Volume Signal": volumesignal,
    }
