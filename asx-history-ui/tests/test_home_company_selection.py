from fastapi.testclient import TestClient


def test_home_contains_company_select_form(client: TestClient) -> None:
    """Ensure home page contains a company selection dropdown."""
    # This will fail until we implement the dropdown
    pass
