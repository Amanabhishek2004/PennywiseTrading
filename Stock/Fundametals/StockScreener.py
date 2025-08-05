from Database.models import Stock, StockTechnicals, EarningMetric, Comparables

def calculate_financial_score(stock: Stock):
    """
    Calculate a financial score using all available fields from EarningMetric and Comparables.
    """
    score = 0
    # Use Comparables (Ratios)
    if stock.comparables:
        ratios = stock.comparables[0]
        # Lower PE, PEG, EV/EBITDA, Price to Book, Price to Sales, Price to Free Cash Flow are better
        if ratios.trailingPE: score += max(0, 20 - min(ratios.trailingPE, 20))
        if ratios.forwardPE: score += max(0, 10 - min(ratios.forwardPE, 10))
        if ratios.peg: score += max(0, 10 - min(ratios.peg, 10))
        if ratios.EVEBITDA: score += max(0, 10 - min(ratios.EVEBITDA, 10))
        if ratios.pricetoBook: score += max(0, 10 - min(ratios.pricetoBook, 10))
        if ratios.pricetoSales: score += max(0, 10 - min(ratios.pricetoSales, 10))
        if ratios.pricetoFreeCashFlow: score += max(0, 10 - min(ratios.pricetoFreeCashFlow, 10))
        # Higher is better
        if ratios.dividendYield: score += min(ratios.dividendYield * 10, 10)
        if ratios.payoutRatio: score += min(ratios.payoutRatio / 10, 10)
        if ratios.FCFF_Yield: score += min(ratios.FCFF_Yield, 10)
        if ratios.CurrentRatio: score += min(ratios.CurrentRatio, 10)
        if ratios.medianpe: score += max(0, 10 - min(ratios.medianpe, 10))
        if ratios.DebttoEquity is not None: score += max(0, 10 - min(ratios.DebttoEquity, 10))
        if ratios.EV: score += min(ratios.EV / 1e10, 10)
        # Growth metrics (higher is better)
        if ratios.Avg_Sales_QoQ_Growth_Percent: score += min(ratios.Avg_Sales_QoQ_Growth_Percent / 5, 10)
        if ratios.Avg_NetProfit_QoQ_Growth_Percent: score += min(ratios.Avg_NetProfit_QoQ_Growth_Percent / 5, 10)
        if ratios.Avg_OperatingProfit_QoQ_Growth_Percent: score += min(ratios.Avg_OperatingProfit_QoQ_Growth_Percent / 5, 10)
        if ratios.Avg_EPS_QoQ_Growth_Percent: score += min(ratios.Avg_EPS_QoQ_Growth_Percent / 5, 10)
    # Use EarningMetric
    if stock.earning_metrics:
        em = stock.earning_metrics[0]
        # Growth metrics (higher is better)
        if em.EBIT_cagr: score += min(em.EBIT_cagr / 2, 10)
        if em.EBITDA_cagr: score += min(em.EBITDA_cagr / 2, 10)
        if em.OperatingRevenue_Cagr: score += min(em.OperatingRevenue_Cagr / 2, 10)
        if em.NetIncome_cagr: score += min(em.NetIncome_cagr / 2, 10)
        if em.FCFF_Cagr: score += min(em.FCFF_Cagr / 2, 10)
        # Margins (higher is better)
        try:
            if em.operatingMargins: score += min(float(em.operatingMargins), 10)
        except:
            pass
        # EPS (higher is better)
        try:
            if em.epsTrailingTwelveMonths: score += min(float(em.epsTrailingTwelveMonths), 10)
        except:
            pass
        if em.epsForward: score += min(em.epsForward, 10)
    return round(score, 2)


def calculate_technical_score_periodwise(stock: Stock):
    """
    Calculate technical scores for each period (e.g., 1d, 1m) using all available fields.
    Returns a dict: {period: score}
    """
    scores = {}
    # Build a mapping of period to technicals and channels
    tech_map = {t.period: t for t in stock.technicals}
    channel_map = {c.period: c for c in stock.channels}
    for period, tech in tech_map.items():
        score = 0
        # RSI: Neutral range is best, extreme is less good
        channel = channel_map.get(period)
        if tech.CurrentRsi is not None:
            score += max(0 , 30 - tech.CurrentRsi)  # Closer to 50 is better
            score += max(0 , tech.RsiSlope - channel.upper_channel_slope)  # RSI slope
            score += max(0 , tech.RsiSlope - channel.lower_channel_slope)  # RSI slope
        # Support/Resistance: closer is better
        if tech.CurrentSupport and stock.CurrentPrice:
            try:
                dist = abs(stock.CurrentPrice - tech.CurrentSupport) / tech.CurrentSupport
                if dist < 0.05:
                    score += 3
            except:
                pass
        if tech.CurrentResistance and stock.CurrentPrice:
            try:
                dist = abs(stock.CurrentPrice - tech.CurrentResistance) / tech.CurrentResistance
                if dist < 0.05:
                    score += 3
            except:
                pass
            
        # Volume Channel Slopes
        if tech.VolumeUpperChannelSlope:
            score += min(0, tech.VolumeUpperChannelSlope - channel.upper_channel_slope)
            score += min(0, tech.VolumeLowerChannelSlope - channel.lower_channel_slope)
        # Channel slopes for this period
        scores[period] = round(score, 2)
    return scores