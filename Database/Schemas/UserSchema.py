from pydantic import BaseModel
from typing import List, Optional



class StockSchema(BaseModel):
    id: str
    Ticker: str
    CurrentPrice: int
    marketCap: Optional[float]
    Description: Optional[str]
    CompanyName: Optional[str]
    sector: Optional[str]
    beta: Optional[float]
    Industry: Optional[str]
    updated: Optional[str]

    class Config:
        orm_mode = True


class PlanSchema(BaseModel):
    id: str
    plan_type: Optional[str]
    timeperiod: Optional[str]
    Price: Optional[int]

    class Config:
        orm_mode = True


class InvoiceSchema(BaseModel):
    id: str
    transaction_id: Optional[str]
    plan: Optional[PlanSchema]

    class Config:
        orm_mode = True


class AlertSchema(BaseModel):
    id: str
    Ticker: Optional[str]
    Macross: Optional[float]
    lowerchannelSlope: Optional[float]
    upperchannelSlope: Optional[float]
    RsiSlope: Optional[float]
    time: Optional[str]
    period: Optional[str]
    tag: Optional[str]

    class Config:
        orm_mode = True


class ReadHistorySchema(BaseModel):
    id: str
    reads: int
    date: str
    dataused: float

    class Config:
        orm_mode = True


class ApiKeyUsageSchema(BaseModel):
    id: str
    apikey: str
    date: str

    class Config:
        orm_mode = True


# ----------------------------------
# Main User Schema
# ----------------------------------

class UserWithAllDataSchema(BaseModel):
    id: str
    username: str
    name: Optional[str]
    email: Optional[str]
    phonenumber: Optional[str]
    reads: Optional[int]
    Dataused: Optional[float]
    AuthToken: Optional[str]
    Apikey: Optional[str]

    watchlist: List[StockSchema] = []
    invoices: List[InvoiceSchema] = []
    alerts: List[AlertSchema] = []
    plans: List[PlanSchema] = []
    read_history: List[ReadHistorySchema] = []
    apikey_usage: List[ApiKeyUsageSchema] = []

    class Config:
        orm_mode = True
