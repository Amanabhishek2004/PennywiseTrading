# Calculate RSI
def CalculateSwingPoints(ticker, db):
    import pandas as pd
    from Database.models import PriceData, SwingPoints, Stock

    # Query PriceData for the ticker and period "30m"
    records = (
        db.query(PriceData)
        .filter(PriceData.ticker == ticker, PriceData.period == "30m")
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

    window = 5
    is_min = (data['Low'] == data['Low'].rolling(window*2+1 , center=True).min())
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

    bullish_pinbars = data.apply(is_bullish_pinbar, axis=1)
    bearish_pinbars = data.apply(is_bearish_pinbar, axis=1)

    swing_lows = data[is_min & bullish_pinbars & (data['RSI20'] < 30)]
    swing_highs = data[is_max & bearish_pinbars & (data['RSI20'] > 70)]



    for idx in swing_lows.index:
        # Only add if no SwingPoint exists for this time and stock_id
        if not db.query(SwingPoints).filter_by(time=idx, stock_id=stock_id).first():
            db.add(SwingPoints(
                pattern="Weak",
                time=idx,
                tag="SwingLow",
                stock_id=stock_id
            ))

    for idx in swing_highs.index:
        if not db.query(SwingPoints).filter_by(time=idx, stock_id=stock_id).first():
            db.add(SwingPoints(
                pattern="Weak",
                time=idx,
                tag="SwingHigh",
                stock_id=stock_id
            ))
    bullish_divergence_idx = []
    for i in range(len(swing_lows)):
        curr_idx = swing_lows.index[i]
        curr_pos = data.index.get_loc(curr_idx)
        for j in range(1, 30):
            prev_pos = curr_pos - j
            if prev_pos < 0:
                break
            prev_idx = data.index[prev_pos]
            if swing_lows.loc[curr_idx, 'Close'] < data.loc[prev_idx, 'Close'] and \
               swing_lows.loc[curr_idx, 'RSI20'] > data.loc[prev_idx, 'RSI20']:
                bullish_divergence_idx.append(curr_idx)
                if not db.query(SwingPoints).filter_by(time=curr_idx, stock_id=stock_id).first():
                    db.add(SwingPoints(
                        pattern="BullishDivergence",
                        time=curr_idx,
                        tag="SwingLow",
                        stock_id=stock_id
                    ))
                break

    bearish_divergence_idx = []
    for i in range(len(swing_highs)):
        curr_idx = swing_highs.index[i]
        curr_pos = data.index.get_loc(curr_idx)
        for j in range(1, 30 ):
            prev_pos = curr_pos - j
            if prev_pos < 0:
                break
            prev_idx = data.index[prev_pos]
            if swing_highs.loc[curr_idx, 'Close'] > data.loc[prev_idx, 'Close'] and \
            swing_highs.loc[curr_idx, 'RSI20'] < data.loc[prev_idx, 'RSI20']:
                bearish_divergence_idx.append(curr_idx)

                if not db.query(SwingPoints).filter_by(time=curr_idx, stock_id=stock_id).first():
                    db.add(SwingPoints(
                        pattern="BearishDivergence",
                        time=curr_idx,
                        tag="SwingHigh",
                        stock_id=stock_id
                    ))
                break

    db.commit()

    divergences = {
        "BullishDivergingSwing": bullish_divergence_idx,
        "BearishDiverganceSwing": bearish_divergence_idx,
        "SwingLows": swing_lows.to_dict(),
        "SwingHighs": swing_highs.to_dict()
    }
    print(divergences)

    return divergences, data


def GetVWAPsFromLatestDivergences(ticker, db, periods=["1m", "30m",  "1d"]):
    from Database.models import PriceData, SwingPoints, Stock
    import pandas as pd

    # Get stock_id
    stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
    if not stock:
        return {}

    stock_id = stock.id
    results = {}

    for period in periods:
        # Query all PriceData for this ticker and period
        records = (
            db.query(PriceData)
            .filter(PriceData.ticker == ticker, PriceData.period == period)
            .order_by(PriceData.date.asc())
            .all()
        )

        if not records:
            results[period] = {"bullish": (None, None), "bearish": (None, None)}
            continue

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

        # Query latest bullish and bearish divergence swing points for this stock and period
        latest_bullish = (
            db.query(SwingPoints)
            .filter_by(stock_id=stock_id, pattern="BullishDivergence")
            .order_by(SwingPoints.time.desc())
            .first()
        )
        latest_bearish = (
            db.query(SwingPoints)
            .filter_by(stock_id=stock_id, pattern="BearishDivergence")
            .order_by(SwingPoints.time.desc())
            .first()
        )


        if latest_bullish:
            if period == "1d":
                match_dates = pd.to_datetime(data.index).normalize()
                anchor_mask = match_dates == pd.to_datetime(latest_bullish.time).normalize()
                if anchor_mask.any():
                    anchor_idx_bullish = data.index[anchor_mask][0]
                    anchor_pos_bullish = data.index.get_loc(anchor_idx_bullish)
                    anchored_bullish = data.iloc[anchor_pos_bullish:]
                    vwap_bullish = (anchored_bullish['Close'] * anchored_bullish['Volume']).cumsum() / anchored_bullish['Volume'].cumsum()
                    vwap_bullish.index = anchored_bullish.index
                else:
                    vwap_bullish, anchor_idx_bullish = None, None
            else:
                if latest_bullish.time in data.index:
                    print(latest_bullish.time)
                    anchor_idx_bullish = latest_bullish.time
                    anchor_pos_bullish = data.index.get_loc(anchor_idx_bullish)
                    anchored_bullish = data.iloc[anchor_pos_bullish:]
                    vwap_bullish = (anchored_bullish['Close'] * anchored_bullish['Volume']).cumsum() / anchored_bullish['Volume'].cumsum()
                    vwap_bullish.index = anchored_bullish.index
                else:
                    vwap_bullish, anchor_idx_bullish = None, None
        else:
            vwap_bullish, anchor_idx_bullish = None, None

        # ---------------------
        # Bearish VWAP
        # ---------------------
        if latest_bearish:
            if period == "1d":
                match_dates = pd.to_datetime(data.index).normalize()
                anchor_mask = match_dates == pd.to_datetime(latest_bearish.time).normalize()
                if anchor_mask.any():
                    anchor_idx_bearish = data.index[anchor_mask][0]
                    anchor_pos_bearish = data.index.get_loc(anchor_idx_bearish)
                    anchored_bearish = data.iloc[anchor_pos_bearish:]
                    vwap_bearish = (anchored_bearish['Close'] * anchored_bearish['Volume']).cumsum() / anchored_bearish['Volume'].cumsum()
                    vwap_bearish.index = anchored_bearish.index
                else:
                    vwap_bearish, anchor_idx_bearish = None, None
            else:
                print(latest_bearish.time)
                if latest_bearish.time in data.index :
                    
                    anchor_idx_bearish = latest_bearish.time
                    anchor_pos_bearish = data.index.get_loc(anchor_idx_bearish)
                    anchored_bearish = data.iloc[anchor_pos_bearish:]
                    vwap_bearish = (anchored_bearish['Close'] * anchored_bearish['Volume']).cumsum() / anchored_bearish['Volume'].cumsum()
                    vwap_bearish.index = anchored_bearish.index
                else:
                    vwap_bearish, anchor_idx_bearish = None, None
        else:
            vwap_bearish, anchor_idx_bearish = None, None

        # Add results for this period
        results[period] = {
            "bullish": (vwap_bullish, anchor_idx_bullish),
            "bearish": (vwap_bearish, anchor_idx_bearish)
        }

    return results
