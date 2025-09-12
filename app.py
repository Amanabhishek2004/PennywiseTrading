from pydantic import BaseModel
from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import  UploadFile, HTTPException, Depends , FastAPI
from sqlalchemy.orm import Session
import pandas as pd
from Routers import StockFundamentalRoutes
from Database.databaseconfig import Base, engine, get_db
from Database.models import *
from uuid import uuid4 
from Stock.Fundametals.StockComparables import *
from Stock.Fundametals.StockDIctScehma import *
from Stock.Fundametals.StockCashFlow import  *
from Stock.Fundametals.StockForwardRatios import *
from Stock.Fundametals.StockReturnsCalculation import *
from Routers import StockRouters , ComparisonRouters , AdminRouter , TechnicalRoutes , UserAccountRoutes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy import event
from Routers.UserAccountRoutes import  get_current_user
from AIPrompts import Financial
from scipy.stats import gaussian_kde
# from D.models import StockTechnicals  # or the model you want to listen to

class NumpyJSONResponse(ORJSONResponse):
    def render(self, content) -> bytes:
        def default(obj):
            if isinstance(obj, (np.generic,)):
                return obj.item()
            if isinstance(obj, (np.ndarray,)):
                return obj.tolist()
            return str(obj)
        return ORJSONResponse.render(self, content)


app = FastAPI(default_response_class=NumpyJSONResponse)
app.include_router(Financial.router)
app.include_router(StockRouters.router)
app.include_router(ComparisonRouters.router)
app.include_router(AdminRouter.router)
app.include_router(TechnicalRoutes.router)
app.include_router(StockFundamentalRoutes.router)
app.include_router(UserAccountRoutes.router)
 


event.listen(StockTechnicals, "after_update", create_alert_on_stock_update)
# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allowed origins
    allow_credentials=True,  # Allow cookies for cross-origin requests
    allow_methods=["*"],  # HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # HTTP headers
)
 
@app.get("/CalculateGrowthRatios/{ticker}" , tags = ["Ratios And Forward Comparables"])
def FPE(ticker: str, db: Session = Depends(get_db)  , current_user: User = Depends(get_current_user)):
      
      forwardpe = calculate_forward_pe(ticker , db)
 
      return {"ForwardPe" : forwardpe  }
def parse_data(data_string):

    import ast
    if not data_string:
        return []
    
    try:
        parsed_list = ast.literal_eval(data_string)  # Convert string to list
        return [float(x) if x != 'nan' else float('nan') for x in parsed_list]
    except (ValueError, SyntaxError):
        raise ValueError(f"Invalid data format: {data_string}")

@app.get("/AllRatios/{ticker}" , tags = ["Ratios And Forward Comparables"])
def PCF(ticker:str , db:Session =  Depends(get_db) , current_user: User = Depends(get_current_user)  ) :
           '''
           We Are utilizing Free Cashflow To Firm And Calculating The Ratio Price /FCFF
           
           '''
           stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
           if not stock:
                return {"error": "Stock not found"}
           ratios = calculate_ratios_from_annual_data(stock)
           return ratios




@app.get("/Returns/{ticker}" , tags = ["Ratios And Forward Comparables"])
def Returns(ticker:str , db:Session =  Depends(get_db) , current_user: User = Depends(get_current_user) ) :
        data = CalculateReturns(ticker) 
        return data


class PortfolioRequest(BaseModel):
    stocks: List[str]




@app.post("/portfolio/returns" , tags = ["Portfolio Details And Correlation"])
async def get_portfolio_returns(request: PortfolioRequest ,current_user: User = Depends(get_current_user)):
    stocksarray = request.stocks

    if not stocksarray:
        raise HTTPException(status_code=400, detail="The stocks list cannot be empty.")

    try:
        result = CalculatePortfolioReturns(stocksarray)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/price-kde/1d" ,  tags = ["Portfolio Details And Correlation"])
def get_price_and_return_kde(
    request: PortfolioRequest, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)
):
    """
    Get KDE curves of prices and returns for the last 1 day for multiple tickers.
    """
    response = {}

    for ticker in request.stocks:
        # Last 1 day of price data
        prices = (
            db.query(PriceData)
            .filter(PriceData.ticker == ticker)
            .filter(PriceData.period == "1d")
            .order_by(PriceData.date.asc())
            .all()
        )

        if len(prices) < 2:
            response[ticker] = {"error": "Not enough price data to calculate KDE"}
            continue

        # Extract close prices
        closes = np.array([p.close_price for p in prices])

        # --- KDE for Prices ---
        kde_prices = gaussian_kde(closes)
        x_prices = np.linspace(closes.min(), closes.max(), 200)
        y_prices = kde_prices(x_prices)

        # --- KDE for Returns ---
        returns = np.diff(np.log(closes))  # log returns
        kde_returns = gaussian_kde(returns)
        x_returns = np.linspace(returns.min(), returns.max(), 200)
        y_returns = kde_returns(x_returns)

        # Store results per ticker
        response[ticker] = {
            "prices": {"x": x_prices.tolist(), "y": y_prices.tolist()},
            "returns": {"x": x_returns.tolist(), "y": y_returns.tolist()},
        }

    return response
