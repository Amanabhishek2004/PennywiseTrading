def CalculateSwingPoints(ticker, db , period):
    import pandas as pd
    import vectorbt as vbt
    from Database.models import PriceData, SwingPoints, Stock
    records = (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.period == period)
        .order_by(PriceData.date.asc())
        .all()
    )

    if not records:
        return None, None

    # Get stock_id for linking
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    stock_id = stock.id if stock else None

    # Convert to DataFrame
    data = pd.DataFrame([{
        "Open": r.open_price,
        "High": r.high_price,
        "Low": r.low_price,
        "Close": r.close_price,
        "Volume": r.volume,
        "RSI20": r.RSI,
        "Date": r.date
    } for r in records])

    data.set_index("Date", inplace=True)
    data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])

    # Calculate perfect swings using centered window and future data
    window = 10
    is_min = (data['Low'] == data['Low'].rolling(window * 2 + 1, center=True).min())
    is_max = (data['High'] == data['High'].rolling(window * 2 + 1, center=True).max())

    # Candlestick pattern detection
    def detect_candle_pattern(row, prev_row):
        open_, close, high, low = row['Open'], row['Close'], row['High'], row['Low']
        body = abs(close - open_)
        lower_wick = min(open_, close) - low
        upper_wick = high - max(open_, close)
        candle_range = high - low

        if candle_range == 0:
            return None

        is_bullish_pinbar = (lower_wick > 2 * body) and (lower_wick > upper_wick)
        is_bearish_pinbar = (upper_wick > 2 * body) and (upper_wick > lower_wick)
        is_doji = (body / candle_range < 0.1)

        if prev_row is not None:
            prev_open, prev_close = prev_row['Open'], prev_row['Close']
            is_bullish_engulfing = (
                prev_close < prev_open and
                close > open_ and
                open_ < prev_close and close > prev_open
            )
            is_bearish_engulfing = (
                prev_close > prev_open and
                close < open_ and
                open_ > prev_close and close < prev_open
            )
            is_piercing = (
                prev_close < prev_open and
                close > (prev_open + prev_close) / 2 and
                open_ < prev_close and close < prev_open
            )
            is_dark_cloud = (
                prev_close > prev_open and
                close < (prev_open + prev_close) / 2 and
                open_ > prev_close and close > prev_open
            )
        else:
            is_bullish_engulfing = is_bearish_engulfing = False
            is_piercing = is_dark_cloud = False

        if is_bullish_pinbar or is_bullish_engulfing or is_piercing:
            return "bullish"
        elif is_bearish_pinbar or is_bearish_engulfing or is_dark_cloud:
            return "bearish"
        elif is_doji:
            return "doji"
        else:
            return None

    pattern_type = [None]
    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]
        pattern_type.append(detect_candle_pattern(row, prev_row))
    data['Pattern'] = pattern_type

    # Swing points based only on RSI levels (for divergence detection)
    swing_lows_all = data[is_min & (data['RSI20'] < 35)]
    swing_highs_all = data[is_max & (data['RSI20'] > 70)]

    # Filter swings that also show valid patterns
    swing_lows_pattern = swing_lows_all[swing_lows_all['Pattern'] == 'bullish']
    swing_highs_pattern = swing_highs_all[swing_highs_all['Pattern'] == 'bearish']

    # Bullish Divergence (RSI ↑, Price ↓)
    all_bullish_divergence_idx = []
    for i in range(len(swing_lows_all)):
        curr_idx = swing_lows_all.index[i]
        curr_pos = data.index.get_loc(curr_idx)
        for j in range(1, window+1):
            prev_pos = curr_pos - j
            if prev_pos < 0:
                break
            prev_idx = data.index[prev_pos]
            if swing_lows_all.loc[curr_idx, 'Close'] < data.loc[prev_idx, 'Close'] and \
               swing_lows_all.loc[curr_idx, 'RSI20'] > data.loc[prev_idx, 'RSI20']:
                all_bullish_divergence_idx.append(curr_idx)
                break

    # Bearish Divergence (RSI ↓, Price ↑)
    all_bearish_divergence_idx = []
    for i in range(len(swing_highs_all)):
        curr_idx = swing_highs_all.index[i]
        curr_pos = data.index.get_loc(curr_idx)
        for j in range(1, window+1):
            prev_pos = curr_pos - j
            if prev_pos < 0:
                break
            prev_idx = data.index[prev_pos]
            if swing_highs_all.loc[curr_idx, 'Close'] > data.loc[prev_idx, 'Close'] and \
               swing_highs_all.loc[curr_idx, 'RSI20'] < data.loc[prev_idx, 'RSI20']:
                all_bearish_divergence_idx.append(curr_idx)
                break

    # Save swing points to DB (optional, can be commented out if not needed)
    for idx in swing_lows_all.index:
        if not db.query(SwingPoints).filter_by(time=idx, stock_id=stock_id).first():
            db.add(SwingPoints(
                pattern="Weak",
                time=idx,
                period = period , 
                tag="SwingLow",
                stock_id=stock_id
            ))
    for idx in swing_highs_all.index:
        if not db.query(SwingPoints).filter_by(time=idx, stock_id=stock_id).first():
            db.add(SwingPoints(
                pattern="Weak",
                time=idx,
                period = period , 
                tag="SwingHigh",
                stock_id=stock_id
            ))
    for idx in all_bullish_divergence_idx:
        if not db.query(SwingPoints).filter_by(time=idx, stock_id=stock_id).first():
            db.add(SwingPoints(
                pattern="BullishDivergence",
                time=idx,
                period = period , 
                tag="SwingLow",
                stock_id=stock_id
            ))
    for idx in all_bearish_divergence_idx:
        if not db.query(SwingPoints).filter_by(time=idx, stock_id=stock_id).first():
            db.add(SwingPoints(
                pattern="BearishDivergence",
                time=idx,
                period = period ,   
                tag="SwingHigh",
                stock_id=stock_id
            ))
    db.commit()

    # Return swing points and divergence indices
    swingpoints = {
        "BullishDivergingSwing": all_bullish_divergence_idx,
        "BearishDiverganceSwing": all_bearish_divergence_idx,
        "SwingLows": swing_lows_all.to_dict(),
        "SwingHighs": swing_highs_all.to_dict(),
        "SwingLowsPattern": swing_lows_pattern.to_dict(),
        "SwingHighsPattern": swing_highs_pattern.to_dict()
    }
    return swingpoints, data
