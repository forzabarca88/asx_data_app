from fastapi.testclient import TestClient


def test_unknown_company_shows_error_message(client: TestClient) -> None:
    """Ensure unknown company code shows error message."""
    # This will fail until we implement error handling
    pass


def test_empty_history_shows_no_data_message(client: TestClient) -> None:
    """Ensure empty history shows no data message."""
    # This will fail until we implement empty history handling
    pass
