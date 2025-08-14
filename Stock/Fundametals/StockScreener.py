from Database.models import Stock, StockTechnicals, EarningMetric, Comparables , SupportData
import numpy as np 
def convert_to_list(data_string):
    if data_string is None:
        return []

    if isinstance(data_string, (int, float)):
        return [float(data_string)]

    elif isinstance(data_string, str):
        cleaned_data = data_string.strip().replace("[", "").replace("]", "").replace("'", "").replace("%", "")
        elements = cleaned_data.split(",")
        result = []

        for element in elements:
            element = element.strip()
            if element == "":
                element = "0"
            try:
                number = float(element.replace(",", ""))
                result.append(number)
            except ValueError:
                result.append(element)
        return result

    else:
        return []


import numpy as np

def calculate_financial_score(stock: Stock):
    """
    Calculate a financial score using all available fields from EarningMetric and Comparables.
    Caps all metric contributions to avoid extreme scores.
    """
    score = 0
    
    def clamp(value, min_val, max_val):
        return max(min_val, min(value, max_val))
    
    # Use Comparables (Ratios)
    if stock.comparables:
        ratios = stock.comparables[0]
        
        if ratios.trailingPE is not None:
            score += clamp((20 - min(ratios.trailingPE, 20)) * 10, -50, 50)
        
        if ratios.forwardPE is not None and ratios.trailingPE is not None:
            score += clamp((ratios.trailingPE - ratios.forwardPE) * 10, -50, 50)
        
        if ratios.peg is not None:
            score += clamp((1 - ratios.peg) * 100, -50, 50)
        
        if ratios.EVEBITDA is not None:
            score += clamp((10 - ratios.EVEBITDA) * 10, -50, 50)
        
        if ratios.medianpe is not None and ratios.trailingPE is not None:
            score += clamp((ratios.medianpe - ratios.trailingPE) * 10, -50, 50)
        
        if ratios.pricetoSales is not None:
            score += clamp((20 - ratios.pricetoSales) * 10, -50, 50)
        
        if ratios.pricetoFreeCashFlow is not None:
            score += clamp((10 - ratios.pricetoFreeCashFlow) * 10, -50, 50)
        
        if ratios.FCFF_Yield is not None:
            score += clamp(ratios.FCFF_Yield * 100, -50, 50)
        
        if ratios.CurrentRatio is not None:
            score += clamp((3 - ratios.CurrentRatio) * 10, -10, 10)
        
        if ratios.DebttoEquity is not None:
            score += clamp((1 - ratios.DebttoEquity) * 10, -50, 50)
        
        # Growth metrics (higher is better)
        for growth_metric in [
            ratios.Avg_Sales_QoQ_Growth_Percent,
            ratios.Avg_NetProfit_QoQ_Growth_Percent,
            ratios.Avg_OperatingProfit_QoQ_Growth_Percent,
            ratios.Avg_EPS_QoQ_Growth_Percent
        ]:
            if growth_metric is not None:
                score += clamp(growth_metric, -50, 50)

    # Use EarningMetric
    if stock.earning_metrics:
        em = stock.earning_metrics[0]
        
        for cagr in [
            em.EBIT_cagr, em.EBITDA_cagr,
            em.OperatingRevenue_Cagr, em.NetIncome_cagr,
            em.FCFF_Cagr
        ]:
            if cagr is not None:
                score += clamp(cagr * 100, -50, 50)
        
        try:
            if em.operatingMargins is not None:
                score += clamp(float(em.operatingMargins) * 100, -10, 10)
        except:
            pass
        
        try:
            if em.epsTrailingTwelveMonths is not None:
                score += clamp(float(em.epsTrailingTwelveMonths), -10, 10)
        except:
            pass
        
        if em.epsForward is not None:
            score += clamp(em.epsForward, -10, 10)

    # Use Valuation Metrics
    if stock.metrics:
        vl = stock.metrics[0]    
        
        if vl.ROE is not None:
            score += clamp(vl.ROE * 100, -50, 50)
        
        if vl.ROA is not None:
            score += clamp(vl.ROA * 100, -50, 50)
        
        if vl.ROIC is not None and vl.WACC is not None:
            roic_list = convert_to_list(vl.ROIC)
            if roic_list:
                median_roic = np.nanmedian(roic_list)
                if not np.isnan(median_roic):
                    score += clamp((median_roic - vl.WACC) * 100, -50, 50)
        
        if vl.COD is not None:
            score -= clamp(vl.COD * 100, -50, 50)
        
        if vl.ICR is not None:
            score += clamp(vl.ICR * 100, -50, 50)

    return round(score, 2)



def calculate_technical_score_periodwise(stock: Stock, db, max_score_per_metric=200, max_total_score=500):
    """
    Calculate technical scores for each period (e.g., 1d, 1m) using all available fields.
    Caps per-metric contributions and total score per period.
    Returns a dict: {period: score}
    """
    scores = {}
    tech_map = {t.period: t for t in stock.technicals}
    channel_map = {c.period: c for c in stock.channels}
    
    for period, tech in tech_map.items():
        score = 0
        currentsupport = db.query(SupportData).filter(
            SupportData.stock_id == stock.id,
            SupportData.period == period,
            SupportData.Price <= stock.CurrentPrice
        ).order_by(SupportData.Price.desc()).first()

        currentresistance = db.query(SupportData).filter(
            SupportData.stock_id == stock.id,
            SupportData.period == period,
            SupportData.Price >= stock.CurrentPrice
        ).order_by(SupportData.Price.asc()).first()

        channel = channel_map.get(period)

        # RSI score
        if tech.CurrentRsi is not None:
            rsi_score = max(0, 30 - tech.CurrentRsi)
            score += min(rsi_score, max_score_per_metric)

            if channel:
                rsi_slope_score1 = tech.RsiSlope - channel.upper_channel_slope
                rsi_slope_score2 = tech.RsiSlope - channel.lower_channel_slope
                score += min(max(rsi_slope_score1, 0), max_score_per_metric)
                score += min(max(rsi_slope_score2, 0), max_score_per_metric)

        # Resistance proximity
        if currentresistance and stock.CurrentPrice:
            try:
                dist = abs(stock.CurrentPrice - currentresistance.Price) / currentresistance.Price
                if dist < 0.05:
                    score += min(10, max_score_per_metric)
            except:
                pass

        # Support proximity
        if currentsupport and stock.CurrentPrice:
            try:
                dist = abs(stock.CurrentPrice - currentsupport.Price) / currentsupport.Price
                if dist < 0.05:
                    score += min(10, max_score_per_metric)
            except:
                pass

        # Volume slope
        if tech.VolumeUpperChannelSlope and channel:
            vol_score1 = tech.VolumeUpperChannelSlope - channel.upper_channel_slope
            vol_score2 = tech.VolumeLowerChannelSlope - channel.lower_channel_slope
            score += min(max(vol_score1, 0), max_score_per_metric)
            score += min(max(vol_score2, 0), max_score_per_metric)

        # Cap the total score
        score = min(score, max_total_score)

        scores[period] = round(score, 2)

    return scores
