from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

class PriceDataBase(BaseModel):
    stock_id: str = Field(..., description="ID of the associated stock")
    ticker: Optional[str] = Field(None, description="Ticker symbol of the stock")
    date: Optional[str] = Field(None, description="Date of the price data in YYYY-MM-DD format")
    open_price: Optional[float] = Field(None, description="Opening price of the stock")
    high_price: Optional[float] = Field(None, description="Highest price of the stock")
    low_price: Optional[float] = Field(None, description="Lowest price of the stock")
    close_price: Optional[float] = Field(None, description="Closing price of the stock")
    volume: Optional[int] = Field(None, description="Volume of stocks traded")
    RSI: Optional[float] = Field(None, description="Relative Strength Index")
    period: Optional[str] = Field(None, description="Time period for the data")


class PriceDataUpdate(PriceDataBase):
    stock_id: Optional[str] = None  # Allow optional updates to stock_id

class PriceDataResponse(PriceDataBase):
    id: UUID = Field(..., description="Unique identifier for the price data")

    class Config:
        orm_mode = True