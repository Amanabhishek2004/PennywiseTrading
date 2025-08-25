from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from Database.databaseconfig import get_db

from Database.databaseconfig import SessionLocal
from Database.models import (
    Stock, StockTechnicals, Channel, SupportData, SwingPoints, PriceData,
    Comparables, StockFinancialScore, StockTechnicalScore, EarningMetric,
    Financials, Expenses, ValuationMetrics, Quaterlyresult, Shareholding
)

router = APIRouter(prefix="/ai", tags=["AI"])



# --- Response schema ---
class PromptResponse(BaseModel):
    ticker: str
    period: str
    system_prompt: List[str]
    user_prompt: List[str]
    context: Dict[str, Any] = Field(
        description="Structured context the LLM may use (also useful for debugging or tool-use)."
    )

def _safe(v, default=None):
    return default if v is None else v

def _float_or_none(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None

def _collect_price_window(
    db: Session, stock_id: str, period: str, limit: int
) -> List[Dict[str, Any]]:
    q = (
        db.query(PriceData)
        .filter(PriceData.stock_id == stock_id, PriceData.period == period)
        .order_by(desc(PriceData.date))
        .limit(limit)
        .all()
    )
    # Return newest->oldest as stored, but many LLMs prefer oldest->newest for sequences
    return [
        {
            "date": p.date,
            "open": _float_or_none(p.open_price),
            "high": _float_or_none(p.high_price),
            "low": _float_or_none(p.low_price),
            "close": _float_or_none(p.close_price),
            "volume": p.volume,
            "rsi": _float_or_none(p.RSI),
            "obv": _float_or_none(p.OnbalanceVolume),
        }
        for p in reversed(q)
    ]

def _latest_technical(db: Session, stock_id: str, period: str) -> Optional[StockTechnicals]:
    return (
        db.query(StockTechnicals)
        .filter(StockTechnicals.stock_id == stock_id, StockTechnicals.period == period)
        .order_by(desc(StockTechnicals.id))
        .first()
    )

def _latest_channel(db: Session, stock_id: str, period: str) -> Optional[Channel]:
    return (
        db.query(Channel)
        .filter(Channel.stock_id == stock_id, Channel.period == period)
        .order_by(desc(Channel.id))
        .first()
    )

def _latest_supports(db: Session, stock_id: str, period: str, limit: int = 10) -> List[Dict[str, Any]]:
    rows = (
        db.query(SupportData)
        .filter(SupportData.stock_id == stock_id, SupportData.period == period)
        .order_by(desc(SupportData.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {
            "price": _float_or_none(r.Price),
            "timestamp": r.timestamp,
            "pattern": r.Pattern,
            "retests": r.retests,
        }
        for r in rows
    ]

def _latest_swingpoints(db: Session, stock_id: str, period: str, limit: int = 10) -> List[Dict[str, Any]]:
    rows = (
        db.query(SwingPoints)
        .filter(SwingPoints.stock_id == stock_id, SwingPoints.period == period)
        .order_by(desc(SwingPoints.time))
        .limit(limit)
        .all()
    )
    return [{"pattern": r.pattern, "time": r.time, "tag": r.tag} for r in rows]

def _latest_ratios(db: Session, stock_id: str) -> Optional[Comparables]:
    return (
        db.query(Comparables)
        .filter(Comparables.stock_id == stock_id)
        .order_by(desc(Comparables.id))
        .first()
    )

def _latest_fin_scores(db: Session, stock_id: str) -> Optional[StockFinancialScore]:
    return (
        db.query(StockFinancialScore)
        .filter(StockFinancialScore.stock_id == stock_id)
        .order_by(desc(StockFinancialScore.id))
        .first()
    )

def _latest_tech_scores(db: Session, stock_id: str, period: str) -> Optional[StockTechnicalScore]:
    return (
        db.query(StockTechnicalScore)
        .filter(StockTechnicalScore.stock_id == stock_id, StockTechnicalScore.period == period)
        .order_by(desc(StockTechnicalScore.id))
        .first()
    )

def _to_dict(model_obj) -> Dict[str, Any]:
    if not model_obj:
        return {}
    # Manually map only fields we care about (prevents accidental huge payloads)
    if isinstance(model_obj, StockTechnicals):
        return {
            "rsi": _float_or_none(model_obj.CurrentRsi),
            "rsi_slope": _float_or_none(model_obj.RsiSlope),
            "rsi_intercept": _float_or_none(model_obj.Rsiintercept),
            "support": _float_or_none(model_obj.CurrentSupport),
            "resistance": _float_or_none(model_obj.CurrentResistance),
            "vol_upper_slope": _float_or_none(model_obj.VolumeUpperChannelSlope),
            "vol_lower_slope": _float_or_none(model_obj.VolumeLowerChannelSlope),
            "vol_upper_intercept": _float_or_none(model_obj.VolumeUpperChannelIntercept),
            "vol_lower_intercept": _float_or_none(model_obj.VolumeLowerChannelIntercept),
        }
    if isinstance(model_obj, Channel):
        return {
            "upper_slope": _float_or_none(model_obj.upper_channel_slope),
            "upper_intercept": _float_or_none(model_obj.upper_channel_intercept),
            "lower_slope": _float_or_none(model_obj.lower_channel_slope),
            "lower_intercept": _float_or_none(model_obj.lower_channel_intercept),
        }
    if isinstance(model_obj, Comparables):
        return {
            "trailingPE": _float_or_none(model_obj.trailingPE),
            "forwardPE": _float_or_none(model_obj.forwardPE),
            "medianPE": _float_or_none(model_obj.medianpe),
            "PEG": _float_or_none(model_obj.peg),
            "EV_EBITDA": _float_or_none(model_obj.EVEBITDA),
            "P_S": _float_or_none(model_obj.pricetoSales),
            "P_FCF": _float_or_none(model_obj.pricetoFreeCashFlow),
            "P_B": _float_or_none(model_obj.pricetoBook),
            "FCFF_Yield": _float_or_none(model_obj.FCFF_Yield),
            "CurrentRatio": _float_or_none(model_obj.CurrentRatio),
            "DebtToEquity": _float_or_none(model_obj.DebttoEquity),
            "DividendYield": _float_or_none(model_obj.dividendYield),
            "EV": _float_or_none(model_obj.EV),
            "QoQ_Sales_Growth_Avg_%": _float_or_none(model_obj.Avg_Sales_QoQ_Growth_Percent),
            "QoQ_NP_Growth_Avg_%": _float_or_none(model_obj.Avg_NetProfit_QoQ_Growth_Percent),
            "QoQ_OP_Growth_Avg_%": _float_or_none(model_obj.Avg_OperatingProfit_QoQ_Growth_Percent),
            "QoQ_EPS_Growth_Avg_%": _float_or_none(model_obj.Avg_EPS_QoQ_Growth_Percent),
        }
    if isinstance(model_obj, StockFinancialScore):
        # Only the headline fields to keep prompt tight
        return {
            "pe": _float_or_none(model_obj.trailingPE_score),
            "forwardPE": _float_or_none(model_obj.forwardPE_score),
            "peg": _float_or_none(model_obj.peg_score),
            "evebitda": _float_or_none(model_obj.EVEBITDA_score),
            "medianpe": _float_or_none(model_obj.medianpe_score),
            "ps": _float_or_none(model_obj.pricetoSales_score),
            "pfcf": _float_or_none(model_obj.pricetoFreeCashFlow_score),
            "fcff_yield": _float_or_none(model_obj.FCFF_Yield_score),
            "current_ratio": _float_or_none(model_obj.CurrentRatio_score),
            "dte": _float_or_none(model_obj.DebttoEquity_score),
            "growth_sales": _float_or_none(model_obj.Avg_Sales_QoQ_Growth_Percent_score),
            "growth_np": _float_or_none(model_obj.Avg_NetProfit_QoQ_Growth_Percent_score),
            "growth_op": _float_or_none(model_obj.Avg_OperatingProfit_QoQ_Growth_Percent_score),
            "growth_eps": _float_or_none(model_obj.Avg_EPS_QoQ_Growth_Percent_score),
            "roe": _float_or_none(model_obj.ROE_score),
            "roa": _float_or_none(model_obj.ROA_score),
            "roic": _float_or_none(model_obj.ROIC_score),
            "wacc": _float_or_none(model_obj.WACC_score),
            "icr": _float_or_none(model_obj.ICR_score),
            "total": _float_or_none(model_obj.total_score),
        }
    if isinstance(model_obj, StockTechnicalScore):
        return {
            "rsi_now": _float_or_none(model_obj.CurrentRsi_score),
            "rsi_slope": _float_or_none(model_obj.RsiSlope_score),
            "resistance_px": _float_or_none(model_obj.ResistanceProximity_score),
            "support_px": _float_or_none(model_obj.SupportProximity_score),
            "vol_up_slope": _float_or_none(model_obj.VolumeUpperChannelSlope_score),
            "vol_dn_slope": _float_or_none(model_obj.VolumeLowerChannelSlope_score),
            "ch_up_slope": _float_or_none(model_obj.ChannelUpperSlope_score),
            "ch_dn_slope": _float_or_none(model_obj.ChannelLowerSlope_score),
            "total": _float_or_none(model_obj.total_score),
        }
    return {}

def _build_prompts(
    stock: Stock,
    period: str,
    technicals: Dict[str, Any],
    channels: Dict[str, Any],
    supports: List[Dict[str, Any]],
    swings: List[Dict[str, Any]],
    ratios: Dict[str, Any],
    fin_scores: Dict[str, Any],
    tech_scores: Dict[str, Any],
    weights: Dict[str, float]
) -> Dict[str, str]:
    # A compact, instruction-heavy system prompt to keep the model on rails
    system_prompt = [
    "You are a disciplined equity analyst blending technicals and fundamentals.",
    "Output must be concise, structured, and decision-oriented.",
    "Use only the provided context; do not invent data.",
    "If data is missing, state it explicitly.",
    "Prioritize:",
    f"- RSI divergence & oversold/overbought with weight {weights.get('rsi_divergence', 2.0)}",
    f"- Support/resistance proximity with RSI filter weight {weights.get('sr_rsi', 1.5)}",
    f"- Channel slope regime (trend) weight {weights.get('channel_trend', 1.25)}",
    f"- Valuation sanity (PE/PEG/EV/EBITDA) weights {weights.get('valuation', 1.0)}",
    f"- Quality/profitability (ROE/ROIC vs WACC/ICR) weights {weights.get('quality', 1.0)}"
]

    user_prompt = [
    f"Ticker: {stock.Ticker} | Company: {stock.CompanyName or 'N/A'} | Period: {period}",
    "## Data",
    f"- Technicals: {technicals}",
    f"- Channels: {channels}",
    f"- Supports/Resistances (recent): {supports}",
    f"- Swing Points: {swings}",
    f"- Valuation Ratios: {ratios}",
    f"- Financial Scores: {fin_scores}",
    f"- Technical Scores: {tech_scores}",
    "## Tasks",
    "1) Technical Read:",
    "   - Identify trend by channel slopes and price structure.",
    "   - Check RSI regime and slope; call out any likely bullish/bearish divergence.",
    "   - Flag proximity to support/resistance; note RSI filter (<=30 near support, >=70 near resistance).",
    "2) Fundamental Read:",
    "   - Comment on valuation (PE, PEG, EV/EBITDA, P/S, P/FCF) vs growth and leverage (D/E, ICR).",
    "   - Comment on quality (ROE/ROIC vs WACC), liquidity (Current Ratio), and income yield (DividendYield if present).",
    "3) Weighted View (0–100):",
    "   - Produce TECH score and FUND score (0–100) based on the weights.",
    "   - Produce a FINAL score (0–100) = 0.55*TECH + 0.45*FUND (unless data missing; then reweight).",
    "4) Actionable:",
    "   - One-line stance: Strong Buy / Buy / Neutral / Sell / Strong Sell with 1–2 reasons.",
    "   - 2 risks and 2 validation checkpoints (what would confirm/negate the view).",
    "## Output Format (strict JSON)",
    "{",
    '  "technical_summary": "...",',
    '  "fundamental_summary": "...",',
    '  "scores": {"technical": 0, "fundamental": 0, "final": 0},',
    '  "stance": "Strong Buy|Buy|Neutral|Sell|Strong Sell",',
    '  "reasons": ["...", "..."],',
    '  "risks": ["...", "..."],',
    '  "validation_checkpoints": ["...", "..."]',
    "}",
    "Respond with JSON only."
]   
    
    return {
        "system_prompt": system_prompt , 
        "user_prompt": user_prompt
    }

@router.get("/prompts/{ticker}", response_model=PromptResponse)
def build_ai_prompts_for_ticker(
    ticker: str,
    period: str = Query("1d", regex="^(1m|1d)$"),
    price_lookback: int = Query(200, ge=30, le=2000),
    supports_limit: int = Query(10, ge=1, le=50),
    swings_limit: int = Query(10, ge=1, le=50),
    # Tunable weights to reflect your earlier preference: higher weight to RSI divergence & SR with RSI
    rsi_divergence_w: float = Query(2.0, ge=0.0, le=5.0),
    sr_rsi_w: float = Query(1.5, ge=0.0, le=5.0),
    channel_trend_w: float = Query(1.25, ge=0.0, le=5.0),
    valuation_w: float = Query(1.0, ge=0.0, le=5.0),
    quality_w: float = Query(1.0, ge=0.0, le=5.0),
    db: Session = Depends(get_db),
):
    # 1) Locate stock
    stock = (
        db.query(Stock)
        .filter(Stock.Ticker == ticker)
        .first()
    )
    if not stock:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

    # 2) Gather data
    tech = _latest_technical(db, stock.id, period)
    ch = _latest_channel(db, stock.id, period)
    supports = _latest_supports(db, stock.id, period, supports_limit)
    swings = _latest_swingpoints(db, stock.id, period, swings_limit)
    ratios = _latest_ratios(db, stock.id)
    fin_scores = _latest_fin_scores(db, stock.id)
    tech_scores = _latest_tech_scores(db, stock.id, period)
    # 3) Convert to dicts for compact promp
    technicals_d = _to_dict(tech)
    channels_d = _to_dict(ch)
    ratios_d = _to_dict(ratios)
    fin_scores_d = _to_dict(fin_scores)
    tech_scores_d = _to_dict(tech_scores)

    # 4) Build prompts
    weights = {
        "rsi_divergence": rsi_divergence_w,
        "sr_rsi": sr_rsi_w,
        "channel_trend": channel_trend_w,
        "valuation": valuation_w,
        "quality": quality_w,
    }
    prompts = _build_prompts(
        stock=stock,
        period=period,
        technicals=technicals_d,
        channels=channels_d,
        supports=supports,
        swings=swings,
        ratios=ratios_d,
        fin_scores=fin_scores_d,
        tech_scores=tech_scores_d,
        weights=weights,
    )

    # 5) Return
    return PromptResponse(
        ticker=stock.Ticker,
        period=period,
        system_prompt=prompts["system_prompt"],
        user_prompt=prompts["user_prompt"],
        context={
            "stock": {
                "name": stock.CompanyName,
                "sector": stock.sector,
                "industry": stock.Industry,
                "updated": stock.updated,
                "price": _float_or_none(stock.CurrentPrice),
                "pctChange": _float_or_none(stock.pctChange),
                "marketCap": _float_or_none(stock.marketCap),
            },
            "weights": weights,
        },
    )
