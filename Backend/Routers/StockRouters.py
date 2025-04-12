from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from Database.databaseconfig import *
from Database.models import * 
from typing import List
from Database.Schemas.StockSchema import *
import math
from Stock.Stock import * 

router = APIRouter(prefix="/Stock", tags=["Stocks"])


@router.get("/{ticker}" , response_model=List[StockSchema] )
def get_all_stocks(db: Session = Depends(get_db) ):
     stocks = db.query(Stock).all()
     for stock in stocks:
         for field, value in stock.__dict__.items():
             if isinstance(value, float) and math.isnan(value):  # NaN check
                 print(f"NaN detected in field: {field} for stock {stock.Ticker}")
     return stocks 



@router.post("/peerstocks/", response_model=List[StockSchema])
def GetPeers(ticker: List[str], db: Session = Depends(get_db)):
     for stock in ticker:
         if not isinstance(stock, str):
             raise HTTPException(status_code=400, detail="Ticker must be a string")
         elif db.query(Stock).filter(Stock.Ticker == stock).first() is None:
            data =  CreateStockDataBaseInstance(stock, db)
            print(data)
            if data.get("error"):
                 raise HTTPException(status_code=400, detail=data["error"])
     
     stocks = db.query(Stock).filter(Stock.Ticker.in_(ticker)).all()
     
     if not stocks:
         raise HTTPException(status_code=404, detail="No stocks found")
     
     return stocks