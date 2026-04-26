from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_root_returns_200_and_html(client: TestClient) -> None:
    """Ensure GET / returns status 200 and HTML content."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_home_lists_companies(client: TestClient) -> None:
    """Ensure home page lists companies from /health."""
    with patch("app.main.ApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get_companies = AsyncMock(return_value=[
            type("Company", (), {"code": "IAG"}),
            type("Company", (), {"code": "CBA"}),
        ])
        response = client.get("/")
        assert response.status_code == 200
        assert "IAG" in response.text
        assert "CBA" in response.text
