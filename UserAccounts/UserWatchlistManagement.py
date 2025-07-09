from Database.models import * 
from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional



class WatchlistPostSchema(BaseModel):
    stock_id: str
    user_id: str

    class Config: 
        orm_mode = True

def AddStockToWatchlist(stock_id, user_id, db):
    """
    Add a stock to the user's watchlist.
    """

    user = db.query(User).filter_by(id=user_id).first()
    stock = db.query(Stock).filter_by(id=stock_id).first()
    if not user or not stock:
        return {"success": False, "message": "User or Stock not found."}
    if stock in user.watchlist:
        return {"success": False, "message": "Stock already in watchlist."}
    user.watchlist.append(stock)
    db.commit()
    return {"success": True, "message": "Stock added to watchlist."}

def RemoveStockFromWatchlist(stock_id, user_id, db):
    """
    Remove a stock from the user's watchlist.
    """
    user = db.query(User).filter_by(id=user_id).first()
    stock = db.query(Stock).filter_by(id=stock_id).first()
    if not user or not stock:
        return {"success": False, "message": "User or Stock not found."}
    if stock not in user.watchlist:
        return {"success": False, "message": "Stock not in watchlist."}
    user.watchlist.remove(stock)
    db.commit()
    return {"success": True, "message": "Stock removed from watchlist."}
       

