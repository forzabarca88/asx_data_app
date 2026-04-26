from app.config import settings


def test_default_base_url() -> None:
    """Ensure base_api_url is set correctly."""
    assert settings.base_api_url == "http://192.168.0.50:30181"
