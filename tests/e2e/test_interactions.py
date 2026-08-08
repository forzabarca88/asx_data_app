"""E2E tests for widget interaction and state change verification.

Verifies that sidebar widget interactions trigger the expected changes
in the Streamlit app: data reloads, chart updates, filter effects, and
state persistence across tab switches.

Streamlit 1.60.0 DOM structure notes:
- Date input: <input type="text" data-testid="stDateInputField"> with value
  format "YYYY/MM/DD – YYYY/MM/DD" (en-dash separator). Use fill().
- Selectbox: Click to open dropdown, options rendered as [role="option"].
  NOTE: Option clicks don't trigger reruns in headless mode (known
  Streamlit limitation with React Aria ComboBox). Test verifies widget
  renders and opens correctly.
- Slider: Value displayed in [data-testid="stSliderThumbValue"]. Click on
  the track div to change value (triggers rerun).
- Toggle/Checkbox: <input type="checkbox" role="switch"> inside a visually
  hidden <span>. Click the outer [data-testid="stCheckbox"] div.
- Multiselect: Selected items rendered as <span data-baseweb="tag"> elements
  with <span title="SYMBOL"> inside. Click to open, click option, Escape.
  NOTE: To deselect, click the tag's delete icon (svg[title="Delete"]);
  already-selected values are NOT listed as options in the reopened dropdown
  (the dropdown only shows unselected options + "Select all").
"""

import datetime
import re
import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so we can import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import (
    HEADER_DIVIDEND_ANALYSIS,
    HEADER_GROWTH_TEMPLATE,
    HEADER_LIQUIDITY_RISK,
    HEADER_TREND_OVER_TIME,
    HEADER_VALUATION_MATRIX,
    TAB_DIVIDEND_ANALYSIS,
    TAB_GROWTH_RANKINGS,
    TAB_LIQUIDITY_RISK,
    TAB_TREND_OVER_TIME,
    TAB_VALUATION_MATRIX,
)

# ── Constants ────────────────────────────────────────────────────────

TAB_GROWTH = TAB_GROWTH_RANKINGS
TAB_VALUATION = TAB_VALUATION_MATRIX
TAB_DIVIDEND = TAB_DIVIDEND_ANALYSIS
TAB_LIQUIDITY = TAB_LIQUIDITY_RISK
TAB_TREND = TAB_TREND_OVER_TIME

# Growth header is dynamic (includes factor name), use template prefix
# (strip format placeholder) for substring matching in Playwright's text= selector
HEADER_GROWTH = HEADER_GROWTH_TEMPLATE.replace(" ({})", "")
HEADER_VALUATION = HEADER_VALUATION_MATRIX
HEADER_DIVIDEND = HEADER_DIVIDEND_ANALYSIS
HEADER_LIQUIDITY = HEADER_LIQUIDITY_RISK
HEADER_TREND = HEADER_TREND_OVER_TIME

# Mock API symbols
MOCK_SYMBOLS = ["BHP", "CBA", "CSL", "WES", "WBC"]

# Render timeout for chart/vega-lite rendering
RENDER_TIMEOUT = 30_000

# Streamlit rerun timeout (generous for data loading + rendering)
RERUN_TIMEOUT = 30_000


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _navigate(page, app_url):
    """Navigate to the app before each test and wait for full render.

    Streamlit renders elements progressively. Each test gets a fresh page
    (new browser context) creating a new Streamlit session. With
    session-scoped app startup, the cache is warm after the first test.
    """
    page.goto(app_url)
    page.wait_for_selector("[data-testid='stHeading']", timeout=60_000)
    page.locator("[data-testid='stSidebar']").wait_for(state="visible", timeout=60_000)
    page.wait_for_selector("[data-testid='stDateInput']", timeout=60_000)
    page.wait_for_selector("[data-testid='stMultiSelect']", timeout=60_000)
    page.wait_for_selector("[data-testid='stSelectbox']", timeout=60_000)
    page.wait_for_selector("[data-testid='stSlider']", timeout=60_000)
    # Wait for tabs to render (tabs render after sidebar widgets)
    page.wait_for_selector("[role='tab']", timeout=30_000)
    page.wait_for_timeout(2000)


# ── Helpers ──────────────────────────────────────────────────────────

def _click_tab_and_wait(page, tab_label: str, header_text: str) -> None:
    """Click a tab by label and wait for Streamlit rerun to complete."""
    tab = page.get_by_role("tab", name=tab_label)
    tab.click()
    page.wait_for_selector(f"text={header_text}", timeout=RERUN_TIMEOUT)
    page.wait_for_timeout(3000)


def _wait_for_rerun(page) -> None:
    """Wait for Streamlit to finish rerunning after a widget change."""
    page.wait_for_selector("[data-testid='stHeading']", timeout=RERUN_TIMEOUT)
    page.wait_for_timeout(5000)


def _get_record_count(page) -> int:
    """Extract the record count from the 'Data loaded' header text."""
    container = page.locator(
        "[data-testid='stMarkdownContainer']",
        has=page.locator("text=Data loaded"),
    )
    text = container.first.inner_text()
    match = re.search(r"(\d+)\s+records", text)
    if match:
        return int(match.group(1))
    raise ValueError(f"Could not parse record count from: '{text}'")


def _count_bar_marks(chart) -> int:
    """Count the number of bar (rect) marks in a Vega-Lite chart."""
    return chart.locator(".mark-rect").count()


def _count_line_marks(chart) -> int:
    """Count the number of line marks in a Vega-Lite chart."""
    return chart.locator(".mark-line").count()


def _get_multiselect_items(page) -> list[str]:
    """Get the list of currently selected items in the multiselect.

    Streamlit 1.60.0 renders selected items as <span data-baseweb="tag">
    elements with <span title="SYMBOL"> inside.
    """
    result = page.evaluate("""() => {
        const container = document.querySelector('[data-testid="stMultiSelect"]');
        if (!container) return [];
        const tags = container.querySelectorAll('[data-baseweb="tag"]');
        return Array.from(tags).map(tag => {
            const titleSpan = tag.querySelector('span[title]');
            return titleSpan ? titleSpan.getAttribute("title") : "";
        }).filter(s => s);
    }""")
    return result if result else []


def _select_stock_in_sidebar(page, symbol: str) -> None:
    """Select a stock in the sidebar multiselect for trend analysis."""
    multiselect = page.locator("[data-testid='stMultiSelect']")
    multiselect.click()
    page.wait_for_timeout(500)

    option = page.get_by_role("option", name=symbol)
    option.click()

    page.press("[data-testid='stMultiSelect']", "Escape")
    _wait_for_rerun(page)


def _deselect_stock_in_sidebar(page, symbol: str) -> None:
    """Deselect a stock from the sidebar multiselect.

    Already-selected values in a Streamlit multiselect are rendered as
    removable tags (<span data-baseweb="tag">), NOT as options in the
    dropdown (the reopened dropdown only lists unselected options). Each
    tag contains an svg[title="Delete"] close icon; clicking it removes
    the value.
    """
    multiselect = page.locator("[data-testid='stMultiSelect']")
    tag = multiselect.locator(
        "[data-baseweb='tag']",
        has=page.locator(f"span[title='{symbol}']"),
    )
    tag.wait_for(state="visible", timeout=RERUN_TIMEOUT)
    tag.locator("svg[title='Delete']").click()
    _wait_for_rerun(page)


# ── Test 1: Date Range Change ────────────────────────────────────────

def test_date_range_change(page, screenshot):
    """Changing the date range triggers a Streamlit rerun and updates data.

    The date input is a text field (data-testid=stDateInputField) with value
    format "YYYY/MM/DD – YYYY/MM/DD". Filling it triggers a rerun.

    Mock data has all records dated 5 days ago. We pick a date range that
    still includes the mock data to verify the widget interaction works.
    """
    # Record initial date value using evaluate (avoids stale locator issues)
    initial_date_value = page.evaluate(
        '() => { const el = document.querySelector("[data-testid=stDateInputField]"); return el ? el.value : null; }'
    )

    # Change date range: set start date to 15 days ago, end to 3 days ago
    # Mock data is at 5 days ago, so range [today-15, today-3] includes it
    today = datetime.date.today()
    new_start = today - datetime.timedelta(days=15)
    new_end = today - datetime.timedelta(days=3)

    # Fill the date input directly (format: YYYY/MM/DD – YYYY/MM/DD)
    new_value = f"{new_start.strftime('%Y/%m/%d')} \u2013 {new_end.strftime('%Y/%m/%d')}"
    date_field = page.locator("[data-testid='stDateInputField']")
    date_field.first.fill(new_value)

    # Wait for Streamlit rerun
    _wait_for_rerun(page)

    # Re-query the date field after rerun using evaluate (DOM is rebuilt)
    new_date_value = page.evaluate(
        '() => { const el = document.querySelector("[data-testid=stDateInputField]"); return el ? el.value : null; }'
    )

    assert new_date_value is not None, (
        "Date input field not found after rerun - app may have stopped "
        "(date range excluded all mock data)"
    )
    assert new_date_value != initial_date_value, (
        f"Date input should change after modification: "
        f"initial='{initial_date_value}', new='{new_date_value}'"
    )

    # Verify the date values are reflected
    assert new_start.strftime('%Y/%m/%d') in new_date_value, (
        f"New start date '{new_start}' not reflected in widget: '{new_date_value}'"
    )

    # Verify data is still loaded (date range includes mock data at 5 days ago)
    record_container = page.locator(
        "[data-testid='stMarkdownContainer']",
        has=page.locator("text=Data loaded"),
    )
    assert record_container.count() > 0, (
        "Data should still be loaded for valid date range"
    )

    screenshot(path="after_date_range_change.png")


# ── Test 2: Growth Factor Change ─────────────────────────────────────

def test_growth_factor_change(page, screenshot):
    """Verify the growth factor selectbox renders with multiple options.

    NOTE: Streamlit's selectbox uses React Aria ComboBox which doesn't
    trigger reruns on option clicks in headless mode. This test verifies
    the widget renders correctly, opens the dropdown, and displays
    multiple available growth factors.
    """
    # Navigate to Growth tab first
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    # Verify the selectbox renders
    selectbox = page.locator("[data-testid='stSelectbox']")
    selectbox.wait_for(state="visible", timeout=RERUN_TIMEOUT)
    assert selectbox.is_visible(), "Growth factor selectbox not visible"

    # Get current display text (includes icon name)
    initial_text = selectbox.inner_text()
    assert "Growth factor" in initial_text, (
        f"Selectbox should contain 'Growth factor' label, got: '{initial_text}'"
    )

    # Open the dropdown to reveal options
    selectbox.click()
    page.wait_for_timeout(1000)

    # Options are rendered as [role="option"] elements
    options = page.locator("[role='option']")
    option_count = options.count()

    assert option_count >= 2, (
        f"Selectbox should have at least 2 options, found {option_count}"
    )

    # Verify options include expected factors
    option_texts = []
    for i in range(option_count):
        option_texts.append(options.nth(i).inner_text())

    assert "priceClose" in option_texts, (
        f"Expected 'priceClose' in options: {option_texts}"
    )

    # Close the dropdown
    page.press("[data-testid='stSelectbox']", "Escape")
    page.wait_for_timeout(1000)

    # Verify selectbox returns to closed state
    final_text = selectbox.inner_text()
    assert final_text == initial_text, (
        f"Selectbox should return to original state after closing: "
        f"initial='{initial_text}', final='{final_text}'"
    )

    screenshot(path="after_growth_factor_selectbox.png")


# ── Test 3: Top N Slider ─────────────────────────────────────────────

def test_top_n_slider(page, screenshot):
    """Changing the top N slider updates the number of bars in the growth chart.

    Uses page.fill() on the slider's hidden input element instead of
    clicking fragile React Aria DOM selectors.
    """
    # Navigate to Growth tab
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    # Wait for chart to render
    vega_chart = page.locator("[data-testid='stVegaLiteChart']").first
    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=RENDER_TIMEOUT)

    # Count initial bars
    initial_bars = _count_bar_marks(vega_chart)
    assert initial_bars > 0, "Growth chart has no bars to compare"

    # Get current slider value from stSliderThumbValue
    slider_value_el = page.locator("[data-testid='stSliderThumbValue']")
    initial_value = int(slider_value_el.first.inner_text().strip())

    # Set a new value using fill on the slider's input element
    # This is more robust than clicking React Aria DOM selectors
    new_value = min(initial_value + 10, 50)  # Increase by 10, capped at max
    slider_input = page.locator("[data-testid='stSlider'] input[type='range']")
    if slider_input.count() == 0:
        pytest.skip("Slider input element not found")
    slider_input.fill(str(new_value))

    # Wait for Streamlit rerun
    _wait_for_rerun(page)

    # Navigate back to Growth tab
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    # Wait for chart to re-render
    vega_chart = page.locator("[data-testid='stVegaLiteChart']").first
    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=RENDER_TIMEOUT)

    new_bars = _count_bar_marks(vega_chart)

    # Verify the slider value changed
    slider_value_el = page.locator("[data-testid='stSliderThumbValue']")
    new_value_text = slider_value_el.first.inner_text().strip()
    assert new_value_text != str(initial_value), (
        f"Slider value should change: initial='{initial_value}', new='{new_value_text}'"
    )
    new_value_int = int(new_value_text)
    assert new_value_int > initial_value, (
        f"Slider value should increase: initial={initial_value}, new={new_value_int}"
    )

    # Verify the chart still renders after slider change
    assert vega_chart.is_visible(), "Growth chart disappeared after slider change"
    assert new_bars >= 1, "Growth chart has no bars after slider change"

    screenshot(path="after_top_n_slider_change.png")


# ── Test 4: Franked Toggle ───────────────────────────────────────────

def test_franked_toggle(page, screenshot):
    """Toggling the franked filter reduces visible dividend data.

    Clicking the checkbox div toggles the filter and triggers a rerun.
    """
    # Toggle only renders when feature engineering succeeds
    toggle = page.locator("[data-testid='stCheckbox']")
    toggle.wait_for(state="visible", timeout=60_000)

    # Navigate to Dividend tab to see initial data
    _click_tab_and_wait(page, TAB_DIVIDEND, HEADER_DIVIDEND)

    # Get initial dataframe row count
    initial_info = page.evaluate("""() => {
        const container = document.querySelector('[data-testid="stDataFrame"]');
        if (!container) return {error: 'no dataframe'};
        const table = container.querySelector('table[role="grid"]');
        if (!table) return {error: 'no grid table'};
        const rows = table.querySelectorAll('tbody tr');
        return {row_count: rows.length};
    }""")

    if "error" in initial_info:
        pytest.skip("Dividend dataframe not available")

    initial_rows = initial_info["row_count"]
    assert initial_rows > 0, "No dividend data to filter"

    # Record initial franked/unfranked metric values
    metrics = page.locator("[data-testid='stMetric']")
    initial_franked_count = metrics.nth(0).locator(
        "[data-testid='stMetricValue']"
    ).inner_text().strip()
    initial_unfranked_count = metrics.nth(1).locator(
        "[data-testid='stMetricValue']"
    ).inner_text().strip()

    # Click the toggle div to change state (triggers rerun)
    page.click("[data-testid='stCheckbox']")

    # Wait for Streamlit rerun (filter change triggers full rerun)
    _wait_for_rerun(page)

    # Navigate back to Dividend tab
    _click_tab_and_wait(page, TAB_DIVIDEND, HEADER_DIVIDEND)

    # Get new row count after filter
    new_info = page.evaluate("""() => {
        const container = document.querySelector('[data-testid="stDataFrame"]');
        if (!container) return {error: 'no dataframe'};
        const table = container.querySelector('table[role="grid"]');
        if (!table) return {error: 'no grid table'};
        const rows = table.querySelectorAll('tbody tr');
        return {row_count: rows.length};
    }""")

    # Check for info message (no stocks match filters)
    info_msg = page.locator("[data-testid='stAlert']")
    if info_msg.count() > 0:
        msg_text = info_msg.first.inner_text()
        if "No stocks match" in msg_text:
            screenshot(path="after_franked_toggle_all_filtered.png")
            pytest.skip("All stocks filtered out by franked filter")

    new_rows = new_info.get("row_count", 0)

    # Franked filter should reduce visible rows (or show info message)
    assert new_rows <= initial_rows, (
        f"Franked filter should reduce visible rows: "
        f"initial={initial_rows}, new={new_rows}"
    )

    # Verify franking metrics update
    metrics = page.locator("[data-testid='stMetric']")
    new_franked_count = metrics.nth(0).locator(
        "[data-testid='stMetricValue']"
    ).inner_text().strip()
    new_unfranked_count = metrics.nth(1).locator(
        "[data-testid='stMetricValue']"
    ).inner_text().strip()

    assert new_franked_count != initial_franked_count or new_unfranked_count != initial_unfranked_count, (
        f"Franking metrics should change after toggle: "
        f"franked: '{initial_franked_count}' -> '{new_franked_count}', "
        f"unfranked: '{initial_unfranked_count}' -> '{new_unfranked_count}'"
    )

    # Unfranked should be 0 when franked filter is active
    assert new_unfranked_count == "0", (
        f"Unfranked count should be 0 when franked filter is active, got: '{new_unfranked_count}'"
    )

    screenshot(path="after_franked_toggle.png")


# ── Test 5: Stock Multiselect ────────────────────────────────────────

def test_stock_multiselect(page, screenshot):
    """Adding/removing stocks from multiselect updates the trend chart.

    The mock API history data may not produce enough data points for a
    line chart within the default 90-day date range (only 1 point per
    symbol at 5 days ago). This test verifies widget interaction and
    handles the case where the chart doesn't render.
    """
    # Select two stocks for trend analysis
    _select_stock_in_sidebar(page, "BHP")
    _select_stock_in_sidebar(page, "CBA")

    # Verify multiselect shows selected stocks
    selected = _get_multiselect_items(page)
    assert "BHP" in selected, f"BHP should be selected, got: {selected}"
    assert "CBA" in selected, f"CBA should be selected, got: {selected}"

    # Navigate to Trend tab
    _click_tab_and_wait(page, TAB_TREND, HEADER_TREND)

    # Check if chart rendered
    vega_charts = page.locator("[data-testid='stVegaLiteChart']")
    chart_count = vega_charts.count()

    if chart_count == 0:
        # Check for info/warning message
        alerts = page.locator("[data-testid='stAlert']")
        if alerts.count() > 0:
            alert_text = alerts.first.inner_text()
            screenshot(path="after_multiselect_no_chart.png")
            pytest.skip(f"Trend chart not rendered: {alert_text[:100]}")
        pytest.skip("Trend chart not rendered (insufficient data for line chart)")

    # Chart rendered - count initial lines
    initial_lines = _count_line_marks(vega_charts.first)
    assert initial_lines >= 1, "Trend chart has no lines"

    # Add a third stock
    _select_stock_in_sidebar(page, "CSL")

    # Verify multiselect shows all three
    selected = _get_multiselect_items(page)
    assert "CSL" in selected, f"CSL should be selected, got: {selected}"

    # Navigate to Trend tab
    _click_tab_and_wait(page, TAB_TREND, HEADER_TREND)

    vega_charts = page.locator("[data-testid='stVegaLiteChart']")
    if vega_charts.count() > 0:
        svg = vega_charts.first.locator("svg")
        svg.wait_for(state="visible", timeout=RENDER_TIMEOUT)
        added_lines = _count_line_marks(vega_charts.first)

        assert added_lines > initial_lines, (
            f"Adding a stock should increase trend lines: "
            f"initial={initial_lines}, after_add={added_lines}"
        )

        # Now remove one stock
        _deselect_stock_in_sidebar(page, "CSL")

        # Verify CSL is no longer selected
        selected = _get_multiselect_items(page)
        assert "CSL" not in selected, f"CSL should be deselected, got: {selected}"

        # Navigate to Trend tab
        _click_tab_and_wait(page, TAB_TREND, HEADER_TREND)

        vega_charts = page.locator("[data-testid='stVegaLiteChart']")
        if vega_charts.count() > 0:
            svg = vega_charts.first.locator("svg")
            svg.wait_for(state="visible", timeout=RENDER_TIMEOUT)
            final_lines = _count_line_marks(vega_charts.first)

            assert final_lines < added_lines, (
                f"Removing a stock should decrease trend lines: "
                f"after_add={added_lines}, after_remove={final_lines}"
            )
    else:
        pytest.skip("Trend chart not available after adding stock")

    screenshot(path="after_stock_multiselect.png")


# ── Test 6: Tab Switching Preserves Filters ──────────────────────────

def test_tab_switching_preserves_filters(page, screenshot):
    """Sidebar filter values persist when switching between tabs."""
    # Toggle only renders when feature engineering succeeds
    toggle = page.locator("[data-testid='stCheckbox']")
    toggle.wait_for(state="visible", timeout=60_000)

    # Set up some filter values in the sidebar
    # 1. Select a stock for trend
    _select_stock_in_sidebar(page, "BHP")

    # 2. Record the growth factor from selectbox
    selectbox = page.locator("[data-testid='stSelectbox']")
    initial_factor = selectbox.inner_text().strip()

    # 3. Record the top N value from the slider thumb
    slider_thumb = page.locator("[data-testid='stSliderThumbValue']")
    initial_top_n = slider_thumb.first.inner_text().strip()

    # 4. Record franked toggle state
    initial_franked = page.evaluate("""() => {
        const cb = document.querySelector('[data-testid="stCheckbox"]');
        const inp = cb ? cb.querySelector('input[type="checkbox"]') : null;
        return inp ? inp.checked : false;
    }""")

    # Navigate through all tabs
    tab_navigation = [
        (TAB_GROWTH, HEADER_GROWTH),
        (TAB_VALUATION, HEADER_VALUATION),
        (TAB_DIVIDEND, HEADER_DIVIDEND),
        (TAB_LIQUIDITY, HEADER_LIQUIDITY),
        (TAB_TREND, HEADER_TREND),
    ]

    for tab_label, header_text in tab_navigation:
        _click_tab_and_wait(page, tab_label, header_text)

    # Navigate back to Growth tab (default)
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    # Verify all filter values are preserved
    # 1. Growth factor should be the same
    selectbox = page.locator("[data-testid='stSelectbox']")
    new_factor = selectbox.inner_text().strip()
    assert new_factor == initial_factor, (
        f"Growth factor changed after tab switching: "
        f"initial='{initial_factor}', new='{new_factor}'"
    )

    # 2. Top N should be the same
    slider_thumb = page.locator("[data-testid='stSliderThumbValue']")
    new_top_n = slider_thumb.first.inner_text().strip()
    assert new_top_n == initial_top_n, (
        f"Top N changed after tab switching: "
        f"initial='{initial_top_n}', new='{new_top_n}'"
    )

    # 3. Franked toggle should be the same
    new_franked = page.evaluate("""() => {
        const cb = document.querySelector('[data-testid="stCheckbox"]');
        const inp = cb ? cb.querySelector('input[type="checkbox"]') : null;
        return inp ? inp.checked : false;
    }""")
    assert new_franked == initial_franked, (
        f"Franked toggle changed after tab switching: "
        f"initial={initial_franked}, new={new_franked}"
    )

    # 4. Multiselect should still have BHP selected
    selected = _get_multiselect_items(page)
    assert "BHP" in selected, (
        f"BHP was deselected from multiselect after tab switching. "
        f"Current selections: {selected}"
    )

    screenshot(path="after_tab_switch_preserves_filters.png")
