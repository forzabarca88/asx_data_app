def test_default_base_url():
    from app.config import settings
    assert settings.base_api_url == "http://192.168.0.50:30181"