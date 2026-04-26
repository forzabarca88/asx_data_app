from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Company(BaseModel):
    code: Optional[str] = None


class HistoryItem(BaseModel):
    date: Optional[date] = None
    priceClose: Optional[float] = None
    priceDayHigh: Optional[float] = None
    priceDayLow: Optional[float] = None
    volume: Optional[int] = None

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return None
        return v
