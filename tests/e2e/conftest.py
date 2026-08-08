"""Playwright fixture setup for E2E tests.

Provides:
  - Headless Chromium browser (session-scoped)
  - Fresh page per test with 1920x1080 viewport
  - Streamlit app launcher (starts before tests, stops after)
  - Mock API server (intercepts ASX API calls for reliable tests)
  - Screenshot utility for debugging failures
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from typing import Iterator

# Ensure project root is on sys.path so absolute imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from tests.e2e.mock_api_server import MOCK_PORT

# ── Configuration ───────────────────────────────────────────────────

APP_PORT = 8501
APP_URL = f"http://localhost:{APP_PORT}"
MOCK_API_URL = f"http://127.0.0.1:{MOCK_PORT}"
SCREENSHOT_DIR = Path("/tmp/screens/e2e")
# Use the Python executable's directory for launching subprocesses
# (avoids hardcoded .venv paths; works with any virtualenv layout)
VENV_BIN = Path(sys.executable).parent

# Generous timeouts for Streamlit + chart rendering
PAGE_TIMEOUT = 60_000  # ms -- page load / navigation
CHART_TIMEOUT = 30_000  # ms -- Plotly/Altair rendering


# ── Mock API Server ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mock_api_server() -> Iterator[subprocess.Popen]:
    """Start the mock ASX API server before all tests, stop after all tests.

    The server intercepts requests at MOCK_PORT, so we set
    ASX_API_BASE_URL to point the Streamlit app at it.
    """
    env = os.environ.copy()
    proc = subprocess.Popen(
        [
            str(sys.executable),
            "-m",
            "tests.e2e.mock_api_server",
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    _wait_for_server(MOCK_PORT, timeout=10)
    print(f"[conftest] Mock API server started on port {MOCK_PORT}")

    yield proc

    # Cleanup
    print("[conftest] Stopping mock API server...")
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("[conftest] Mock API server stopped")


def _wait_for_server(port: int, timeout: int = 10) -> None:
    """Block until the server accepts connections on the given port."""
    import socket

    deadline = time.time() + timeout
    while time.time() < deadline:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("127.0.0.1", port))
            sock.close()
            return
        except OSError:
            sock.close()
            time.sleep(0.2)
    raise RuntimeError(f"Mock API server did not start within {timeout}s")


def _wait_for_app_ready(url: str, timeout: int = 30) -> None:
    """Poll until the Streamlit app responds with HTTP 200."""
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Streamlit app did not become ready within {timeout}s")


# ── Streamlit App ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def start_app(mock_api_server: subprocess.Popen) -> Iterator[subprocess.Popen]:
    """Start the Streamlit app once for the test session, stop after all tests.

    Sets ASX_API_BASE_URL so the app connects to the mock server.
    Uses session scope so the app (and its cache) persists across all tests.
    Each test gets a fresh Playwright page (new browser context), which
    creates a new Streamlit session while benefiting from warm cache.

    Streamlit serves a React SPA shell via HTTP, with actual app content
    rendered client-side through WebSocket deltas. The initial render
    requires time for: Python script execution, UI delta generation,
    WebSocket transmission, and React DOM rendering.

    IMPORTANT: --server.fileWatcherType must NOT be set to 'none' as it
    prevents proper Streamlit initialization and causes rendering failures.
    """
    env = os.environ.copy()
    env["ASX_API_BASE_URL"] = MOCK_API_URL

    proc = subprocess.Popen(
        [
            str(VENV_BIN / "streamlit"),
            "run",
            str(PROJECT_ROOT / "app.py"),
            "--server.port",
            str(APP_PORT),
            "--server.headless",
            "true",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to accept connections on the port
    _wait_for_server(APP_PORT, timeout=30)

    # Poll until the Streamlit app responds with HTTP 200, confirming
    # the server is ready to serve requests. This avoids a hardcoded
    # delay and adapts to varying startup times.
    _wait_for_app_ready(APP_URL, timeout=30)
    print(f"[conftest] Streamlit app started on port {APP_PORT}")

    yield proc

    # Cleanup
    print("[conftest] Stopping Streamlit app...")
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    print("[conftest] Streamlit app stopped")


# ── Playwright Browser ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser(playwright_config: dict) -> Iterator[Browser]:
    """Launch a Chromium browser for the test session.

    Uses playwright_config to respect --headed and --slow-mo CLI flags.
    """
    with sync_playwright() as pw:
        browser_instance = pw.chromium.launch(**playwright_config)
        yield browser_instance
        browser_instance.close()


@pytest.fixture(scope="function")
def page(browser: Browser, start_app: subprocess.Popen) -> Iterator[Page]:
    """Create a fresh page for each test with configured viewport and timeout.

    Depends on `start_app` to ensure the Streamlit app is running.
    """
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    context.set_default_timeout(PAGE_TIMEOUT)
    pg = context.new_page()
    yield pg
    context.close()


# ── Screenshot Utility ──────────────────────────────────────────────

@pytest.fixture
def screenshot(page: Page, request: pytest.FixtureRequest):
    """Return a callable that captures a screenshot and saves it.

    Usage in tests:
        screenshot()                          # auto-named by test
        screenshot(path="my_custom_name.png") # custom name
    """
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def _capture(path: str = None) -> Path:
        test_name = request.node.name.replace(" ", "_")
        filename = path or f"{test_name}.png"
        dest = SCREENSHOT_DIR / filename
        page.screenshot(path=str(dest))
        print(f"[screenshot] Saved: {dest}")
        return dest

    return _capture


# ── Helpers ─────────────────────────────────────────────────────────

@pytest.fixture
def app_url() -> str:
    """Return the base URL of the Streamlit app."""
    return APP_URL


@pytest.fixture
def mock_api_url() -> str:
    """Return the base URL of the mock API server."""
    return MOCK_API_URL


# ── Pytest Configuration ────────────────────────────────────────────

def pytest_configure(config):
    """Register custom markers for E2E tests."""
    config.addinivalue_line(
        "markers",
        "screenshot: mark test to capture screenshot on failure",
    )


def pytest_addoption(parser):
    """Add CLI options for E2E test control."""
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed (visible) mode instead of headless",
    )
    parser.addoption(
        "--slow-mo",
        type=int,
        default=0,
        help="Slow down playwright operations by N milliseconds (for debugging)",
    )


@pytest.fixture(scope="session")
def playwright_config(request) -> dict:
    """Browser launch configuration based on CLI options."""
    return {
        "headless": not request.config.getoption("--headed"),
        "slow_mo": request.config.getoption("--slow-mo"),
    }
