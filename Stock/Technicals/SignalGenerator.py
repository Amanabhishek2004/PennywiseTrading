from .rsiStrategy import *
from .Meanreversion import *
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

def GenrateSignals(ticker, db, period):
    """
    Generate trading signals based on RSI divergence, channel data, and volume analysis for a given stock ticker.
    Handles missing data gracefully.
    """
    from Database.models import PriceData, StockTechnicals, Stock, Channel, SupportData, SwingPoints

    Prices = (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.period == period)
        .order_by(PriceData.date.desc())
        .all()
    )

    if not Prices:
        return {
            "error": "No price data found for the ticker.",
            "RSI Signal": {},
            "MA Signal": {},
            "messages": [],
            "channel_signals": {},
            "Volume Signal": {}
        }

    latest_price = Prices[-1]

    closingprices = [price.close_price for price in Prices]
    obvs = [price.OnbalanceVolume for price in Prices[:-1]]

    if not closingprices or not obvs:
        return {
            "error": "Insufficient price or OBV data for the ticker.",
            "RSI Signal": {},
            "MA Signal": {},
            "messages": [],
            "channel_signals": {},
            "Volume Signal": {}
        }

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
    messages = []
    if not technicaldata or not channel:
        return {
            "error": "Required technical/channel data not found in database.",
            "RSI Signal": {},
            "MA Signal": {},
            "messages": [],
            "channel_signals": {},
            "Volume Signal": {}
        }

    # Fetch live price data
    try:
        import yfinance as yf
        data = yf.Ticker(f"{ticker}.NS").history(period="1d", interval="5m")
        price = float(data.iloc[-1]["Close"])
    except Exception as e:
        return {
            "error": f"Failed to fetch data from Yahoo Finance: {e}",
            "RSI Signal": {},
            "MA Signal": {},
            "messages": [],
            "channel_signals": {},
            "Volume Signal": {}
        }

    rsislope = technicaldata.RsiSlope
    currentrsi = technicaldata.CurrentRsi
    lowerchannelslope = channel.lower_channel_slope
    lowervaolumechannel = technicaldata.VolumeLowerChannelSlope
    upperchannelintercept = channel.upper_channel_intercept
    upperchannelslope = channel.upper_channel_slope
    lowerchannelintercept = channel.lower_channel_intercept

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

    support = db.query(SupportData).filter(
        SupportData.stock_id == technicaldata.stock_id,
        SupportData.period == period,
        SupportData.Price <= price,
    ).order_by(desc(SupportData.Price)).first()

    resistance = db.query(SupportData).filter(
        SupportData.stock_id == technicaldata.stock_id,
        SupportData.period == period,
        SupportData.Price >= price,
    ).order_by(SupportData.Price.asc()).first()

    # Normalized OBV
    std = np.std(obvs[-20:]) if len(obvs[-20:]) > 0 else 1
    mean = np.mean(obvs[-20:]) if len(obvs[-20:]) > 0 else 0
    normalized_volscore = (Currentobv - mean) / std if std != 0 else 0
    if abs(normalized_volscore) > 2:
        if normalized_volscore < 0:
            messages.append(
                f"High negative volume anomaly detected for {ticker} in period {period}."
            )
        else:
            messages.append(
                f"High Positive volume anomaly detected for {ticker} in period {period}."
            )

    if rsislope is not None and currentrsi is not None:
        if rsislope < 0 and upperchannelslope > 0 and currentrsi > 70:
            messages.append(
                f"Very Strong Sell conviction for {ticker} in period {period}."
            )
            SwingPoints(
                stock_id=technicaldata.stock_id,
                period=period,
                time=latest_price.date if latest_price else None,
                tag="BearsEntering"
            )

        elif rsislope > 0 and lowerchannelslope < 0 and currentrsi < 30:
            messages.append(
                f"Very Strong Buy conviction for {ticker} in period {period}."
            )
            SwingPoints(
                stock_id=technicaldata.stock_id,
                period=period,
                time=latest_price.date if latest_price else None,
                tag="BullsEntering"
            )

    # Calculate support proximity only if support exists
    suppourt_proximity = ((support.Price - price) / price) * 100 if support else None
    resistance_proximity = ((price - resistance.Price) / price) * 100 if resistance else None

    if suppourt_proximity is not None and suppourt_proximity < 0.05:
        if currentrsi is not None and currentrsi < 30:
            messages.append(
                f"It is a good chance that {ticker} will bounce back from the support level in period {period}."
            )
            SwingPoints(
                stock_id=technicaldata.stock_id,
                period=period,
                pattern="Support Touch and Bounce",
                time=latest_price.date if latest_price else None,
                tag="Support Touch and Bounce"
            )

    if resistance_proximity is not None and resistance_proximity < 0.05:
        if currentrsi is not None and currentrsi > 70:
            messages.append(
                f"It is a good chance that {ticker} will reverse from the resistance level in period {period}."
            )
            SwingPoints(
                stock_id=technicaldata.stock_id,
                period=period,
                pattern="Resistance Touch and Reversal",
                time=latest_price.date if latest_price else None,
                tag="Resistance Touch and Reversal"
            )
    rsipeak_max, rsipeak_min = False, False
    # RSI Signals
    if currentrsi is not None:
        # rsipeak_max, rsipeak_min = CalculateRSIpeakMaxmin(
        #     db, price, currentrsi, ticker, period, interval=30
        # )
        pass
    else:
        rsipeak_max, rsipeak_min = False, False

    channel_signals = {
        "upperchannel_break": upperchannelslope * 22 + upperchannelintercept < price if upperchannelslope is not None and upperchannelintercept is not None else None,
        "lowerchannel_break": lowerchannelslope * 22 + lowerchannelintercept > price if lowerchannelslope is not None and lowerchannelintercept is not None else None,
        "upperchannel_slope": upperchannelslope if upperchannelslope is not None else None,
    }

    Rsisignal = {
        "rsipeak_max": rsipeak_max,
        "rsipeak_min": rsipeak_min,
        "rsidivergenceforbuy": lowerchannelslope * rsislope > 0 if lowerchannelslope is not None and rsislope is not None else None,
        "rsidivergenceforsell": upperchannelslope * rsislope < 0 if upperchannelslope is not None and rsislope is not None else None,
        "Rsi": currentrsi
    }
    masignal = {
        "Buy": DMA20 > DMA50 if DMA20 is not None and DMA50 is not None else None,
        "Sell": DMA50 > DMA20 if DMA20 is not None and DMA50 is not None else None,
    }

    if lowervaolumechannel is not None and lowerchannelslope is not None:
        peak_div = (lowervaolumechannel * lowerchannelslope) > 0
    else:
        peak_div = None

    volumesignal = {
        "peakDIv": peak_div,
        "Suppourt": support.Price if support else None,
        "Resistance": resistance.Price if resistance else None,
        "normalizedobv": normalized_volscore,
        "CurrentObv": Currentobv,
        "lowerchannel": lowervaolumechannel
    }

    return {
        "RSI Signal": Rsisignal,
        "MA Signal": masignal,
        "messages": messages,
        "channel_signals": channel_signals,
        "Volume Signal": volumesignal,
    }