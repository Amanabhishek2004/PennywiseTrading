from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import  UploadFile, HTTPException, Depends , FastAPI
from sqlalchemy.orm import Session
import pandas as pd
from Database.databaseconfig import Base, engine, get_db
from Database.models import Stock, EarningMetric, Comparables, Expenses, Financials, ValuationMetrics
from uuid import uuid4
from Stock.Stock import *  
from Stock.StockDIctScehma import *
from Stock.StockCashFlow import  *
from Stock.StockForwardRatios import *
from Routers import StockRouters , ComparisonRouters , AdminRouter


 
 
app = FastAPI()
app.include_router(StockRouters.router)
app.include_router(ComparisonRouters.router)
app.include_router(AdminRouter.router)
 

 
@app.get("/CalculateForwardPe/{ticker}" , tags = ["Ratios And Forward Comparables"])
def FPE(ticker: str, db: Session = Depends(get_db)):
      
      forwardpe = CalculateForwardPe(ticker , db)
 
      return {
          "Ticker" : ticker , 
          "forwardpe" : forwardpe
      }