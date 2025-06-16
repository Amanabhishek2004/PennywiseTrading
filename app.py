from pydantic import BaseModel
from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import  UploadFile, HTTPException, Depends , FastAPI
from sqlalchemy.orm import Session
import pandas as pd
from Database.databaseconfig import Base, engine, get_db
from Database.models import Stock 
from uuid import uuid4
from Stock.Fundametals.Stock import *  
from Stock.Fundametals.StockDIctScehma import *
from Stock.Fundametals.StockCashFlow import  *
from Stock.Fundametals.StockForwardRatios import *
from Stock.Fundametals.StockReturnsCalculation import *
from Routers import StockRouters , ComparisonRouters , AdminRouter , TechnicalRoutes
from fastapi.middleware.cors import CORSMiddleware


 
app = FastAPI()
app.include_router(StockRouters.router)
app.include_router(ComparisonRouters.router)
app.include_router(AdminRouter.router)
app.include_router(TechnicalRoutes.router)
 


origins = [
    "http://localhost:5173",  # React dev server
    "http://localhost:5174",  # React dev server
    "http://127.0.0.1:3000",  # Alternative localhost
    "https://your-frontend-domain.com"  # Your production frontend
]

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allowed origins
    allow_credentials=True,  # Allow cookies for cross-origin requests
    allow_methods=["*"],  # HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # HTTP headers
)
 
@app.get("/CalculateGrowthRatios/{ticker}" , tags = ["Ratios And Forward Comparables"])
def FPE(ticker: str, db: Session = Depends(get_db)):
      
      forwardpe = CalculateForwardPe(ticker , db)
      Pegs = CalculateMedianpe(ticker)
 
      return {
          "Ticker" : ticker , 
          "forwardpe" : forwardpe , 
          "Peg" : Pegs["PEG"].value, 
          "TTMPE" : Pegs["TTMPE"]
      }


@app.get("/CashflowMidean/{ticker}" , tags = ["Ratios And Forward Comparables"])
def PCF(ticker:str , db:Session =  Depends(get_db) ) :
           '''
           We Are utilizing Free Cashflow To Firm And Calculating The Ratio Price /FCFF
           
           '''
           FCFF = CalculateFCFF(ticker , db) 
           stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
           marketcap = stock.marketCap 

           return {
           "PFCF" : marketcap / FCFF[0]
           }


@app.get("/Returns/{ticker}" , tags = ["Ratios And Forward Comparables"])
def Returns(ticker:str , db:Session =  Depends(get_db) ) :
        data = CalculateReturns(ticker) 
        return data



class PortfolioRequest(BaseModel):
    stocks: List[str]




@app.post("/portfolio/returns" , tags = ["Portfolio Details And Correlation"])
async def get_portfolio_returns(request: PortfolioRequest):
    stocksarray = request.stocks

    if not stocksarray:
        raise HTTPException(status_code=400, detail="The stocks list cannot be empty.")

    try:
        result = CalculatePortfolioReturns(stocksarray)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))