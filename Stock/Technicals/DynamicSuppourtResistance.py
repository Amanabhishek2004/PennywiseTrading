def CalculateSwingPoints(ticker, db, period):
    import pandas as pd
    import pytz
    from sqlalchemy import types as satypes
    from Database.models import PriceData, SwingPoints, Stock

    records = (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.period == period)
        .order_by(PriceData.date.asc())
        .all()
    )
    if not records:
        return None, None

    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    stock_id = stock.id if stock else None
    if not stock_id:
        return None, None

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

    window = 10
    is_min = (data['Low'] == data['Low'].rolling(window * 2 ).min())
    is_max = (data['High'] == data['High'].rolling(window * 2 ).max())

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
        pattern_type.append(detect_candle_pattern(data.iloc[i], data.iloc[i - 1]))
    data['Pattern'] = pattern_type

    swing_lows_all = data[is_min & (data['RSI20'] < 35)]
    swing_highs_all = data[is_max & (data['RSI20'] > 70)]
    swing_lows_pattern = swing_lows_all[swing_lows_all['Pattern'] == 'bullish']
    swing_highs_pattern = swing_highs_all[swing_highs_all['Pattern'] == 'bearish']

    all_bullish_divergence_idx = []
    for curr_idx in swing_lows_all.index.unique():
        curr_positions = data.index.get_indexer_for([curr_idx])
        for curr_pos in curr_positions:
            curr_close = data.iloc[curr_pos]['Close']
            curr_rsi = data.iloc[curr_pos]['RSI20']
            for j in range(1, window + 1):
                prev_pos = curr_pos - j
                if prev_pos < 0:
                    break
                prev_close = data.iloc[prev_pos]['Close']
                prev_rsi = data.iloc[prev_pos]['RSI20']
                if curr_close < prev_close and curr_rsi > prev_rsi:
                    all_bullish_divergence_idx.append(data.index[curr_pos])
                    break

    all_bearish_divergence_idx = []
    for curr_idx in swing_highs_all.index.unique():
        curr_positions = data.index.get_indexer_for([curr_idx])
        for curr_pos in curr_positions:
            curr_close = data.iloc[curr_pos]['Close']
            curr_rsi = data.iloc[curr_pos]['RSI20']
            for j in range(1, window + 1):
                prev_pos = curr_pos - j
                if prev_pos < 0:
                    break
                prev_close = data.iloc[prev_pos]['Close']
                prev_rsi = data.iloc[prev_pos]['RSI20']
                if curr_close > prev_close and curr_rsi < prev_rsi:
                    all_bearish_divergence_idx.append(data.index[curr_pos])
                    break

    col_type = SwingPoints.__table__.c.time.type  # sqlalchemy column type object

    def normalize_for_db(ts):
        ts = pd.Timestamp(ts)
        if isinstance(col_type, satypes.Time):
            return ts.time()

        if isinstance(col_type, satypes.DateTime):
            if getattr(col_type, "timezone", False):

                if ts.tzinfo is None:
                    ts = ts.tz_localize('UTC')
                else:
                    ts = ts.tz_convert('UTC')
                return ts.to_pydatetime()
            else:

                if ts.tzinfo is not None:
                    ts = ts.tz_convert('UTC').tz_localize(None)
                return ts.to_pydatetime()

        return ts.to_pydatetime()

    existing_raw = db.query(SwingPoints.time).filter(SwingPoints.stock_id == stock_id).all()
    existing_times_raw = [r[0] for r in existing_raw]
    existing_norm = set(normalize_for_db(t) for t in existing_times_raw)

    new_entries = []

    def add_if_new(idx, pattern, tag):
        n = normalize_for_db(idx)
        if n not in existing_norm:
            new_entries.append(SwingPoints(pattern=pattern, time=n, period=period, tag=tag, stock_id=stock_id))
            existing_norm.add(n)  # avoid duplicates within this run

    for idx in swing_lows_all.index:
        add_if_new(idx, "Weak", "SwingLow")
    for idx in swing_highs_all.index:
        add_if_new(idx, "Weak", "SwingHigh")
    for idx in all_bullish_divergence_idx:
        add_if_new(idx, "BullishDivergence", "SwingLow")
    for idx in all_bearish_divergence_idx:
        add_if_new(idx, "BearishDivergence", "SwingHigh")

    if new_entries:
        db.add_all(new_entries)
        db.commit()

    swingpoints = {
        "BullishDivergingSwing": all_bullish_divergence_idx,
        "BearishDiverganceSwing": all_bearish_divergence_idx,
        "SwingLows": swing_lows_all.to_dict(),
        "SwingHighs": swing_highs_all.to_dict(),
        "SwingLowsPattern": swing_lows_pattern.to_dict(),
        "SwingHighsPattern": swing_highs_pattern.to_dict()
    }

    return swingpoints, data
