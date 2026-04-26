from app.models import Company, HistoryItem


def test_company_code_model_parses_health_item() -> None:
    """Ensure Company model extracts code from health payload."""
    data = {"code": "IAG"}
    company = Company(**data)
    assert company.code == "IAG"


from datetime import date


def test_history_item_model_parses_prices() -> None:
    """Ensure HistoryItem model parses price fields correctly."""
    data = {
        "date": "2024-01-01",
        "priceClose": 100.5,
        "priceDayHigh": 102.0,
        "priceDayLow": 99.0,
        "volume": 1000000,
    }
    item = HistoryItem(**data)
    assert item.priceClose == 100.5
    assert item.priceDayHigh == 102.0
    assert item.priceDayLow == 99.0
    assert item.volume == 1000000
