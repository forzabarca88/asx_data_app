def test_pytest_runs():
    assert True


def test_app_imports():
    from app.main import app
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)