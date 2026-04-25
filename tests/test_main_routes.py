from fastapi.testclient import TestClient
from app.main import app
from app.models import Company
from unittest.mock import patch, AsyncMock

def test_root_returns_200_and_html():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_home_lists_companies():
    # Mock ApiClient.get_companies to return Company objects
    with patch("app.main.ApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_companies.return_value = [
            Company(code="IAG"),
            Company(code="CBA")
        ]
        mock_client_class.return_value = mock_client
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        assert "IAG" in response.text
        assert "CBA" in response.text
        # Check for href attributes (accounting for potential extra whitespace)
        assert 'href="/company/IAG"' in response.text
        assert 'href="/company/CBA"' in response.text