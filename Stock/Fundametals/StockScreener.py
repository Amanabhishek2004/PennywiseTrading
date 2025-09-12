from Database.models import Stock, StockTechnicals, SupportData, StockFinancialScore, StockTechnicalScore
import numpy as np


# --- Utility functions ---
def convert_to_list(data_string):
    if data_string is None:
        return []

    if isinstance(data_string, (int, float, np.generic)):
        return [float(data_string)]

    elif isinstance(data_string, str):
        cleaned_data = (
            data_string.strip()
            .replace("[", "")
            .replace("]", "")
            .replace("'", "")
            .replace("%", "")
        )
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


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def sanitize_record(record: dict):
    """Convert any numpy scalars to native Python floats/ints before DB insert"""
    return {
        k: (v.item() if isinstance(v, np.generic) else v)
        for k, v in record.items()
    }


# --- Financial Score ---
def create_financial_score(stock: Stock, db):
    """
    Compute detailed financial scores for each metric and insert into StockFinancialScore table.
    """
    scores = {}
    total_score = 0

    # ========== Comparables ==========
    if stock.comparables:
        ratios = stock.comparables[0]

        if ratios.trailingPE is not None:
            scores["trailingPE_score"] = clamp(
                (20 - min(ratios.trailingPE, 20)) * 10, -50, 50
            )

        if ratios.forwardPE is not None and ratios.trailingPE is not None:
            scores["forwardPE_score"] = clamp(
                (ratios.trailingPE - ratios.forwardPE) * 10, -50, 50
            )

        if ratios.peg is not None:
            scores["peg_score"] = clamp((1 - ratios.peg) * 100, -50, 50)

        if ratios.EVEBITDA is not None:
            scores["EVEBITDA_score"] = clamp((10 - ratios.EVEBITDA) * 10, -50, 50)

        if ratios.medianpe is not None and ratios.trailingPE is not None:
            scores["medianpe_score"] = clamp(
                (ratios.medianpe - ratios.trailingPE) * 10, -50, 50
            )

        if ratios.pricetoSales is not None:
            scores["pricetoSales_score"] = clamp((20 - ratios.pricetoSales) * 10, -50, 50)

        if ratios.pricetoFreeCashFlow is not None:
            scores["pricetoFreeCashFlow_score"] = clamp(
                (10 - ratios.pricetoFreeCashFlow) * 10, -50, 50
            )

        if ratios.FCFF_Yield is not None:
            scores["FCFF_Yield_score"] = clamp(ratios.FCFF_Yield * 100, -50, 50)

        if ratios.CurrentRatio is not None:
            scores["CurrentRatio_score"] = clamp((3 - ratios.CurrentRatio) * 10, -10, 10)

        if ratios.DebttoEquity is not None:
            scores["DebttoEquity_score"] = clamp((1 - ratios.DebttoEquity) * 10, -50, 50)

        # Growth metrics
        if ratios.Avg_Sales_QoQ_Growth_Percent is not None:
            scores["Avg_Sales_QoQ_Growth_Percent_score"] = clamp(
                ratios.Avg_Sales_QoQ_Growth_Percent, -50, 50
            )

        if ratios.Avg_NetProfit_QoQ_Growth_Percent is not None:
            scores["Avg_NetProfit_QoQ_Growth_Percent_score"] = clamp(
                ratios.Avg_NetProfit_QoQ_Growth_Percent, -50, 50
            )

        if ratios.Avg_OperatingProfit_QoQ_Growth_Percent is not None:
            scores["Avg_OperatingProfit_QoQ_Growth_Percent_score"] = clamp(
                ratios.Avg_OperatingProfit_QoQ_Growth_Percent, -50, 50
            )

        if ratios.Avg_EPS_QoQ_Growth_Percent is not None:
            scores["Avg_EPS_QoQ_Growth_Percent_score"] = clamp(
                ratios.Avg_EPS_QoQ_Growth_Percent, -50, 50
            )

    # ========== Earning Metrics ==========
    if stock.earning_metrics:
        em = stock.earning_metrics[0]

        if em.EBIT_cagr is not None:
            scores["EBIT_cagr_score"] = clamp(em.EBIT_cagr * 100, -50, 50)

        if em.EBITDA_cagr is not None:
            scores["EBITDA_cagr_score"] = clamp(em.EBITDA_cagr * 100, -50, 50)

        if em.OperatingRevenue_Cagr is not None:
            scores["OperatingRevenue_Cagr_score"] = clamp(
                em.OperatingRevenue_Cagr * 100, -50, 50
            )

        if em.NetIncome_cagr is not None:
            scores["NetIncome_cagr_score"] = clamp(em.NetIncome_cagr * 100, -50, 50)

        if em.FCFF_Cagr is not None:
            scores["FCFF_Cagr_score"] = clamp(em.FCFF_Cagr * 100, -50, 50)

        try:
            if em.operatingMargins is not None:
                scores["operatingMargins_score"] = clamp(
                    float(em.operatingMargins) * 100, -10, 10
                )
        except:
            pass

        try:
            if em.epsTrailingTwelveMonths is not None:
                scores["epsTrailingTwelveMonths_score"] = clamp(
                    float(em.epsTrailingTwelveMonths), -10, 10
                )
        except:
            pass

        if em.epsForward is not None:
            scores["epsForward_score"] = clamp(em.epsForward, -10, 10)

    # ========== Valuation Metrics ==========
    if stock.metrics:
        vl = stock.metrics[0]

        if vl.ROE is not None:
            scores["ROE_score"] = clamp(vl.ROE * 100, -50, 50)

        if vl.ROA is not None:
            scores["ROA_score"] = clamp(vl.ROA * 100, -50, 50)

        if vl.ROIC is not None and vl.WACC is not None:
            roic_list = convert_to_list(vl.ROIC)
            if roic_list:
                median_roic = np.nanmedian(roic_list)
                if not np.isnan(median_roic):
                    scores["ROIC_score"] = clamp(median_roic * 100, -50, 50)
                    scores["WACC_score"] = clamp(vl.WACC * 100, -50, 50)

        if vl.COD is not None:
            scores["COD_score"] = -clamp(vl.COD * 100, -50, 50)

        if vl.ICR is not None:
            scores["ICR_score"] = clamp(vl.ICR * 100, -50, 50)

    # ========== Expenses ==========
    if stock.expenses and stock.earning_metrics:
        em = stock.earning_metrics[0]
        expenses = stock.expenses[0]

        if expenses.Operating_Expense is not None:
            scores["operatingExpense_score"] = 0
        if expenses.InterestExpense_cagr is not None:
            scores["Intrest_Expense_score"] = clamp(
                (-expenses.InterestExpense_cagr + em.OperatingRevenue_Cagr) * 100,
                -50,
                50,
            )

        if expenses.CurrentDebt_cagr is not None:
            scores["CurrentDebt_cagr_score"] = clamp(
                (-expenses.CurrentDebt_cagr + em.OperatingRevenue_Cagr) * 100, -50, 50
            )

    # Sum all non-None scores for total
    total_score = round(sum([v for v in scores.values() if v is not None]), 2)

    # Create StockFinancialScore object
    existingscore = (
        db.query(StockFinancialScore).filter(StockFinancialScore.stock_id == stock.id).first()
    )
    if existingscore:
        db.delete(existingscore)

    financial_score_entry = StockFinancialScore(
        stock_id=stock.id,
        total_score=total_score,
        **sanitize_record(scores),
    )

    db.add(financial_score_entry)
    db.commit()
    db.refresh(financial_score_entry)

    return financial_score_entry


# --- Technical Score ---
def create_technical_score(stock: Stock, db, max_total_score=100):
    """
    Compute detailed technical scores for each period and insert into StockTechnicalScores table.
    """
    results = []
    tech_map = {t.period: t for t in stock.technicals}
    channel_map = {c.period: c for c in stock.channels}

    for period, tech in tech_map.items():
        score = 0
        component_scores = {
            "CurrentRsi_score": None,
            "RsiSlope_score": None,
            "ResistanceProximity_score": None,
            "SupportProximity_score": None,
            "VolumeUpperChannelSlope_score": None,
            "VolumeLowerChannelSlope_score": None,
            "ChannelUpperSlope_score": None,
            "ChannelLowerSlope_score": None,
        }

        channel = channel_map.get(period)

        # ----- Nearest support/resistance -----
        currentsupport = (
            db.query(SupportData)
            .filter(
                SupportData.stock_id == stock.id,
                SupportData.period == period,
                SupportData.Price <= stock.CurrentPrice,
            )
            .order_by(SupportData.Price.desc())
            .first()
        )

        currentresistance = (
            db.query(SupportData)
            .filter(
                SupportData.stock_id == stock.id,
                SupportData.period == period,
                SupportData.Price >= stock.CurrentPrice,
            )
            .order_by(SupportData.Price.asc())
            .first()
        )

        # ----- RSI Divergence -----
        if tech.RsiSlope is not None and channel.upper_channel_slope is not None:
            divergence = tech.RsiSlope - channel.upper_channel_slope
            div_score = np.clip(divergence * 100, -100, 100)
            component_scores["RsiSlope_score"] = float(div_score * 0.4)
            score += component_scores["RsiSlope_score"]

        # ----- Raw RSI -----
        if tech.CurrentRsi is not None:
            if tech.CurrentRsi < 30:
                rsi_score = np.interp(tech.CurrentRsi, [10, 30], [100, 60])
            elif tech.CurrentRsi > 70:
                rsi_score = np.interp(tech.CurrentRsi, [70, 90], [40, 0])
            else:
                rsi_score = 70
            component_scores["CurrentRsi_score"] = float(rsi_score * 0.2)
            score += component_scores["CurrentRsi_score"]

        # ----- Resistance proximity -----
        resistance_touch = False
        if currentresistance and stock.CurrentPrice:
            try:
                dist = abs(stock.CurrentPrice - currentresistance.Price) / currentresistance.Price
                if dist < 0.05:
                    resistance_touch = True
                    component_scores["ResistanceProximity_score"] = float(25 * (1 - dist / 0.05))
                    score += component_scores["ResistanceProximity_score"]
            except:
                pass

        # ----- Support proximity -----
        support_touch = False
        if currentsupport and stock.CurrentPrice:
            try:
                dist = abs(stock.CurrentPrice - currentsupport.Price) / currentsupport.Price
                if dist < 0.05:
                    support_touch = True
                    component_scores["SupportProximity_score"] = float(25 * (1 - dist / 0.05))
                    score += component_scores["SupportProximity_score"]
            except:
                pass

        # ----- RSI + Support/Resistance Confluence -----
        if tech.CurrentRsi is not None:
            if support_touch and tech.CurrentRsi < 30:
                score += 20
            if resistance_touch and tech.CurrentRsi > 70:
                score -= 20

        # ----- Volume slope alignment -----
        if channel and tech.VolumeUpperChannelSlope and tech.VolumeLowerChannelSlope:
            diff_up = tech.VolumeUpperChannelSlope - channel.upper_channel_slope
            diff_down = tech.VolumeLowerChannelSlope - channel.lower_channel_slope
            vol_score = np.clip((diff_up + diff_down) / 2, -1, 1) * 15
            component_scores["VolumeUpperChannelSlope_score"] = float(
                (-channel.upper_channel_slope + tech.VolumeUpperChannelSlope) * 100
            )
            component_scores["VolumeLowerChannelSlope_score"] = float(
                (-channel.lower_channel_slope + tech.VolumeLowerChannelSlope) * 100
            )
            component_scores["ChannelUpperSlope_score"] = float(channel.upper_channel_slope * 100)
            component_scores["ChannelLowerSlope_score"] = float(channel.lower_channel_slope * 100)
            score += vol_score

        # ----- Cap total -----
        score = np.clip(score, 0, max_total_score)

        # ----- Save entry -----
        existing = (
            db.query(StockTechnicalScore)
            .filter(StockTechnicalScore.stock_id == stock.id, StockTechnicalScore.period == period)
            .first()
        )
        if existing:
            db.delete(existing)

        technical_score_entry = StockTechnicalScore(
            stock_id=stock.id,
            period=period,
            total_score=float(round(score, 2)),
            **sanitize_record(component_scores),
        )

        db.add(technical_score_entry)
        results.append(technical_score_entry)

    db.commit()
    for r in results:
        db.refresh(r)

    return results
