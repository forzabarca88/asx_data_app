import sys
sys.path.insert(0, "src")

from datetime import datetime

from app.models import Company, HistoryItem


def test_company_code_model_parses_health_item():
    sample = {"code": "IAG"}
    company = Company(**sample)
    assert company.code == "IAG"


def test_history_item_model_parses_prices():
    sample = {
        "fetched_at": "2024-01-15T00:00:00",
        "priceClose": 100.50,
        "priceDayHigh": 102.00,
        "priceDayLow": 99.00,
        "volume": 1000000,
    }
    item = HistoryItem(**sample)
    assert item.priceClose == 100.50
    assert item.priceDayHigh == 102.00
    assert item.priceDayLow == 99.00
    assert item.volume == 1000000
