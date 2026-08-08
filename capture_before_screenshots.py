"""Capture before screenshots of the ASX Dashboard for before/after comparison.

Takes screenshots of the default view and each of the 5 tabs.
Saves to /tmp/screens/before/ with descriptive names.
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREEN_DIR = "/tmp/screens/before"
APP_URL = "http://localhost:8501"
VIEWPORT = {"width": 1440, "height": 900}

TAB_NAMES = [
    "Growth Rankings",
    "Valuation Matrix",
    "Dividend Analysis",
    "Liquidity & Risk",
    "Trend Over Time",
]

def wait_for_streamlit_ready(url: str, timeout: int = 60) -> bool:
    """Wait for Streamlit to be ready by polling the URL."""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False

def capture_screenshots():
    os.makedirs(SCREEN_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()

        # Wait for app to be ready
        print("Waiting for Streamlit app to be ready...")
        if not wait_for_streamlit_ready(APP_URL):
            print("ERROR: Streamlit app did not become ready in time", file=sys.stderr)
            browser.close()
            sys.exit(1)
        print("Streamlit app is ready!")

        # Navigate to the app
        page.goto(APP_URL)
        # Wait for the app to fully load (Streamlit needs time to render)
        page.wait_for_load_state("networkidle")
        time.sleep(3)  # Extra wait for Plotly charts to render

        # 1. Capture default view (sidebar + first tab)
        print("Capturing: default_view (sidebar + Growth Rankings default tab)")
        page.screenshot(path=os.path.join(SCREEN_DIR, "00_default_view.png"), full_page=False)

        # 2. Capture each tab
        for i, tab_name in enumerate(TAB_NAMES, 1):
            print(f"Capturing: {i:02d}_{tab_name.replace(' ', '_').lower()}.png")

            # Click the tab - Streamlit uses role="tab" elements
            tab_element = page.query_selector(f'[role="tab"]:has-text("{tab_name}")')
            if not tab_element:
                print(f"  WARNING: Could not find tab for '{tab_name}'")
                continue
            tab_element.click()

            # Wait for Streamlit to rerun after tab click
            page.wait_for_load_state("networkidle")
            time.sleep(4)  # Extra wait for Plotly charts to render

            filename = f"{i:02d}_{tab_name.replace(' ', '_').lower()}.png"
            page.screenshot(path=os.path.join(SCREEN_DIR, filename), full_page=False)
            print(f"  Saved: {filename}")

        browser.close()

    # Verify screenshots
    screenshots = sorted(os.listdir(SCREEN_DIR))
    print(f"\nCaptured {len(screenshots)} screenshots:")
    for s in screenshots:
        size = os.path.getsize(os.path.join(SCREEN_DIR, s))
        print(f"  {s} ({size:,} bytes)")

    if len(screenshots) < 6:  # 1 default + 5 tabs
        print("WARNING: Expected 6 screenshots, got fewer.", file=sys.stderr)
        sys.exit(1)

    print("\nAll screenshots captured successfully!")

if __name__ == "__main__":
    capture_screenshots()
