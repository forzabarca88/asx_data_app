from app.main import app


def test_pytest_runs() -> bool:
    """Trivial test to ensure pytest runs."""
    assert True


def test_app_imports() -> None:
    """Ensure app is a FastAPI instance."""
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)
