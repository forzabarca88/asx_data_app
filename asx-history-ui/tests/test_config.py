import sys
sys.path.insert(0, "src")

from app.config import settings


def test_default_base_url():
    assert settings.base_api_url == "http://192.168.0.50:30181"
