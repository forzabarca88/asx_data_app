from datetime import datetime

from pydantic import BaseModel


class Company(BaseModel):
    code: str


class HistoryItem(BaseModel):
    symbol: str
    fetched_at: datetime
    isin: str
    priceClose: float
    priceDayHigh: float
    priceDayLow: float
    volume: int | None = None
