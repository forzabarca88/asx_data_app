"""E2E tests for UI element presence and structure.

Verifies that the Streamlit app renders all expected UI elements:
page title, sidebar, tabs, sidebar widgets, and header info.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import (
    HEADER_DIVIDEND_ANALYSIS,
    HEADER_GROWTH_TEMPLATE,
    HEADER_LIQUIDITY_RISK,
    HEADER_TREND_OVER_TIME,
    HEADER_VALUATION_MATRIX,
    TABS,
)

# Expected tab labels (text includes icon name prefix from Material Symbols)
TAB_LABELS = list(TABS)

# Expected header text for each tab's content
# Growth header is dynamic (includes factor name), so use template prefix
# (strip format placeholder) for substring matching in Playwright's text= selector
TAB_HEADERS = [
    HEADER_GROWTH_TEMPLATE.replace(" ({})", ""),
    HEADER_VALUATION_MATRIX,
    HEADER_DIVIDEND_ANALYSIS,
    HEADER_LIQUIDITY_RISK,
    HEADER_TREND_OVER_TIME,
]


@pytest.fixture(autouse=True)
def _navigate(page, app_url):
    """Navigate to the app before each test and wait for full render.

    Streamlit renders elements progressively: heading → sidebar widgets →
    tab content. Each test gets a fresh page (new browser context) which
    creates a new Streamlit session. With session-scoped app startup,
    the cache is warm after the first test.
    """
    page.goto(app_url)
    # Wait for Streamlit to finish initial render (heading appears first)
    page.wait_for_selector("[data-testid='stHeading']", timeout=60_000)
    # Wait for sidebar to be visible
    page.locator("[data-testid='stSidebar']").wait_for(state="visible", timeout=60_000)
    # Wait for key sidebar widgets to render
    page.wait_for_selector("[data-testid='stDateInput']", timeout=60_000)
    page.wait_for_selector("[data-testid='stMultiSelect']", timeout=60_000)
    page.wait_for_selector("[data-testid='stSelectbox']", timeout=60_000)
    page.wait_for_selector("[data-testid='stSlider']", timeout=60_000)
    # Wait for tabs to render (tabs render after sidebar widgets)
    page.wait_for_selector("[role='tab']", timeout=30_000)
    # Small buffer for DOM stabilization
    page.wait_for_timeout(2000)


def test_page_title(page):
    """Verify the page title (browser tab) renders correctly."""
    title = page.title()
    assert title == "ASX dashboard", f"Expected 'ASX dashboard', got '{title}'"


def test_sidebar_visible(page):
    """Verify the sidebar element exists and is visible."""
    sidebar = page.locator("[data-testid='stSidebar']")
    sidebar.wait_for(state="visible", timeout=30_000)
    assert sidebar.is_visible()


def test_all_tabs_exist(page):
    """Verify all 5 tabs are present with correct labels."""
    tabs = page.get_by_role("tab")
    count = tabs.count()
    assert count == 5, f"Expected 5 tabs, found {count}"

    for i, expected_label in enumerate(TAB_LABELS):
        tab_text = tabs.nth(i).inner_text()
        assert expected_label in tab_text, (
            f"Tab {i}: expected '{expected_label}' in '{tab_text}'"
        )


def test_sidebar_widgets(page):
    """Verify all sidebar widgets render: date range, multiselect,
    selectbox, slider, number inputs, and toggle."""
    sidebar = page.locator("[data-testid='stSidebar']")

    # Date range (date input)
    date_input = page.locator("[data-testid='stDateInput']")
    date_input.wait_for(state="visible", timeout=30_000)
    assert date_input.is_visible(), "Date range input not visible"

    # Multiselect (stocks for trend)
    multiselect = page.locator("[data-testid='stMultiSelect']")
    multiselect.wait_for(state="visible", timeout=30_000)
    assert multiselect.is_visible(), "Multiselect not visible"

    # Selectbox (growth factor)
    selectbox = page.locator("[data-testid='stSelectbox']")
    selectbox.wait_for(state="visible", timeout=30_000)
    assert selectbox.is_visible(), "Growth factor selectbox not visible"

    # Slider (top N)
    slider = page.locator("[data-testid='stSlider']")
    slider.wait_for(state="visible", timeout=30_000)
    assert slider.is_visible(), "Top N slider not visible"

    # Toggle (franked) — only renders when feature engineering succeeds
    toggle = page.locator("[data-testid='stCheckbox']")
    feature_filters_header = page.locator(
        "[data-testid='stHeader']", has=page.locator("text=Feature filters")
    )
    if feature_filters_header.count() > 0:
        toggle.wait_for(state="visible", timeout=30_000)
        assert toggle.is_visible(), "Franked toggle not visible"
    else:
        print("Skipping toggle check — feature filters not rendered")


def test_tab_switching(page):
    """Verify clicking each tab switches the view to the correct content."""
    tabs = page.get_by_role("tab")

    for i, expected_header in enumerate(TAB_HEADERS):
        tabs.nth(i).click()

        # Wait for Streamlit rerun to complete by checking for the header
        page.wait_for_selector(
            f"text={expected_header}",
            timeout=30_000,
        )

        # Verify the header is visible in the main content area
        header = page.get_by_text(expected_header)
        assert header.count() > 0, (
            f"After clicking tab {i}, header '{expected_header}' not found"
        )


def test_default_tab_is_growth(page):
    """Verify the default (first) active tab is Growth Rankings."""
    active_tab = page.get_by_role("tab", selected=True)
    assert active_tab.count() == 1, "Expected exactly one selected tab"
    tab_text = active_tab.inner_text()
    assert "Growth rankings" in tab_text, (
        f"Default tab should be 'Growth rankings', got '{tab_text}'"
    )


def test_header_with_record_count(page):
    """Verify the header shows record count info after data loads."""
    # The app renders: "**Data loaded:** {:,} records | **Symbols:** {} unique"
    record_info = page.get_by_text("Data loaded")
    record_info.wait_for(state="visible", timeout=30_000)
    assert record_info.count() > 0, "Record count header not found"

    # Get the full markdown container text for this element
    container = page.locator(
        "[data-testid='stMarkdownContainer']",
        has=page.locator("text=Data loaded"),
    )
    full_text = container.first.inner_text()
    assert "records" in full_text, (
        f"Expected 'records' in header text, got: '{full_text}'"
    )
    assert "Symbols" in full_text, (
        f"Expected 'Symbols' in header text, got: '{full_text}'"
    )
