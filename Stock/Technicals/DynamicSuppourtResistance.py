import numpy as np
import matplotlib.pyplot as plt
import vectorbt as vbt
import  yfinance as yf 

# Calculate RSI
def CalculateSwingPoints(Ticker):
    stock_data = yf.Ticker(f"{Ticker}.NS")
    data = stock_data.history(period="60d", interval="30m")
    data['RSI20'] = vbt.RSI.run(data['Close'], window=20).rsi

    window = 10
    is_min = (data['Low'] == data['Low'].rolling(window*2+1, center=True).min())
    is_max = (data['High'] == data['High'].rolling(window*2+1, center=True).max())

    def is_bullish_pinbar(row):
        open_ = float(row['Open'])
        close = float(row['Close'])
        high = float(row['High'])
        low = float(row['Low'])
        body = abs(close - open_)
        lower_wick = open_ - low if open_ < close else close - low
        upper_wick = high - close if open_ < close else high - open_
        return (lower_wick > 2 * body) and (lower_wick > upper_wick)

    def is_bearish_pinbar(row):
        open_ = float(row['Open'])
        close = float(row['Close'])
        high = float(row['High'])
        low = float(row['Low'])
        body = abs(close - open_)
        upper_wick = high - open_ if open_ > close else high - close
        lower_wick = close - low if open_ > close else open_ - low
        return (upper_wick > 2 * body) and (upper_wick > lower_wick)

    data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])

    bullish_pinbars = data.apply(is_bullish_pinbar, axis=1)
    bearish_pinbars = data.apply(is_bearish_pinbar, axis=1)

    # Find swing lows and highs with pin bar and RSI conditions
    swing_lows = data[is_min & bullish_pinbars & (data['RSI20'] < 35)]
    swing_highs = data[is_max & bearish_pinbars & (data['RSI20'] > 65)]

    # Detect bullish divergence (price lower low, RSI higher low) in last 15 bars
    bullish_divergence_idx = []
    for i in range(len(swing_lows)):
        curr_idx = swing_lows.index[i]
        curr_pos = data.index.get_loc(curr_idx)
        for j in range(1, 16):
            prev_pos = curr_pos - j
            if prev_pos < 0:
                break
            prev_idx = data.index[prev_pos]
            if swing_lows.loc[curr_idx, 'Close'] < data.loc[prev_idx, 'Close'] and \
               swing_lows.loc[curr_idx, 'RSI20'] > data.loc[prev_idx, 'RSI20']:
                bullish_divergence_idx.append(curr_idx)
                break  # Only need to find one divergence in the last 15

    # Detect bearish divergence (price higher high, RSI lower high) in last 15 bars
    bearish_divergence_idx = []
    for i in range(len(swing_highs)):
        curr_idx = swing_highs.index[i]
        curr_pos = data.index.get_loc(curr_idx)
        for j in range(1, 16):
            prev_pos = curr_pos - j
            if prev_pos < 0:
                break
            prev_idx = data.index[prev_pos]
            if swing_highs.loc[curr_idx, 'Close'] > data.loc[prev_idx, 'Close'] and \
               swing_highs.loc[curr_idx, 'RSI20'] < data.loc[prev_idx, 'RSI20']:
                bearish_divergence_idx.append(curr_idx)
                break  

    divergences = {
        "BullishDivergingSwing": bullish_divergence_idx,
        "BearishDiverganceSwing": bearish_divergence_idx,
        "SwingLows": swing_lows.to_dict(),
        "SwingHighs": swing_highs.to_dict()
    }

    return divergences , data

def CalculateVWAPFromLatestDivergence(data, divergences):
    """
    Calculate VWAP anchored from the latest bullish or bearish divergence point.
    Returns (vwap_series, anchor_idx, anchor_type) or (None, None, None) if not found.
    """
    bullish = divergences.get("BullishDivergingSwing", [])
    bearish = divergences.get("BearishDiverganceSwing", [])
    latest_bullish = bullish[-1] if bullish else None
    latest_bearish = bearish[-1] if bearish else None

    # Decide which is latest
    anchor_idx = None
    anchor_type = None
    if latest_bullish and latest_bearish:
        if latest_bullish > latest_bearish:
            anchor_idx = latest_bullish
            anchor_type = "Bullish"
        else:
            anchor_idx = latest_bearish
            anchor_type = "Bearish"
    elif latest_bullish:
        anchor_idx = latest_bullish
        anchor_type = "Bullish"
    elif latest_bearish:
        anchor_idx = latest_bearish
        anchor_type = "Bearish"
    else:
        return None, None, None

    anchor_pos = data.index.get_loc(anchor_idx)
    anchored = data.iloc[anchor_pos:]
    vwap = (anchored['Close'] * anchored['Volume']).cumsum() / anchored['Volume'].cumsum()
    vwap.index = anchored.index
    return vwap, anchor_idx, anchor_type
      

     