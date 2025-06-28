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
from Stock.Fundametals.StockComparables import *
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
      
      forwardpe = calculate_forward_pe(ticker , db)
    #   Pegs = CalculateMedianpe(ticker)
 
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
def PCF(ticker:str , db:Session =  Depends(get_db) ) :
           '''
           We Are utilizing Free Cashflow To Firm And Calculating The Ratio Price /FCFF
           
           '''
           stock = db.query(Stock).filter(Stock.Ticker == ticker).first()
           if not stock:
                return {"error": "Stock not found"}
           ratios = calculate_ratios_from_annual_data(stock)
           return ratios




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