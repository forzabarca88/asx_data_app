from datetime import date
from pydantic import BaseModel

class Company(BaseModel):
    code: str

class HistoryItem(BaseModel):
    date: date
    priceClose: float
    priceDayHigh: float
    priceDayLow: float
    volume: int | None = None