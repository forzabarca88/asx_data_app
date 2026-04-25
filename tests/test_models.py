from datetime import date
from app.models import Company, HistoryItem

def test_company_code_model_parses_health_item():
    # Given a sample /health payload
    health_payload = [{"code": "IAG"}, {"code": "CBA"}]
    # Pydantic model extracts code
    companies = [Company(**item) for item in health_payload]
    assert companies[0].code == "IAG"
    assert companies[1].code == "CBA"

def test_history_item_model_parses_prices():
    # Given sample history JSON
    history_payload = [{
        "date": "2023-01-01",
        "priceClose": 100.5,
        "priceDayHigh": 105.0,
        "priceDayLow": 99.0,
        "volume": 1000000
    }]
    # Model exposes priceClose, priceDayHigh, etc. as floats and date as a date/datetime
    item = HistoryItem(**history_payload[0])
    assert item.date == date(2023, 1, 1)
    assert item.priceClose == 100.5
    assert item.priceDayHigh == 105.0
    assert item.priceDayLow == 99.0
    assert item.volume == 1000000