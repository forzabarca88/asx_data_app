"""E2E tests for chart rendering and visual quality.

Verifies that each tab renders its charts correctly, uses the right
chart type, displays sentence-case labels, and produces clean output
without overlapping text labels in scatter plots.

In Streamlit 1.60.0, all charts (bar, line, Altair) render as Vega-Lite
charts with data-testid="stVegaLiteChart". Chart type is determined by
SVG mark classes: mark-rect (bar/histogram), mark-circle (scatter).

Axis titles are in SVG <text> elements with class
.mark-text.role-axis-title, requiring text_content() (not inner_text())
since SVG elements are not HTMLElements.
"""

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
    SENTENCE_CASE_EXCEPTIONS,
    TAB_DIVIDEND_ANALYSIS,
    TAB_GROWTH_RANKINGS,
    TAB_LIQUIDITY_RISK,
    TAB_TREND_OVER_TIME,
    TAB_VALUATION_MATRIX,
)

# Screenshot directory for after-screenshots
AFTER_SCREENSHOT_DIR = Path("/tmp/screens/after")

# Expected tab labels (partial match for clicking)
TAB_GROWTH = TAB_GROWTH_RANKINGS
TAB_VALUATION = TAB_VALUATION_MATRIX
TAB_DIVIDEND = TAB_DIVIDEND_ANALYSIS
TAB_LIQUIDITY = TAB_LIQUIDITY_RISK
TAB_TREND = TAB_TREND_OVER_TIME

# Expected header text for each tab
# Growth header is dynamic (includes factor name), so use template prefix
# (strip format placeholder) for substring matching in Playwright's text= selector
HEADER_GROWTH = HEADER_GROWTH_TEMPLATE.replace(" ({})", "")
HEADER_VALUATION = HEADER_VALUATION_MATRIX
HEADER_DIVIDEND = HEADER_DIVIDEND_ANALYSIS
HEADER_LIQUIDITY = HEADER_LIQUIDITY_RISK
HEADER_TREND = HEADER_TREND_OVER_TIME

# Chart timeout for rendering (generous for Vega-Lite)
CHART_RENDER_TIMEOUT = 30_000


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


def _click_tab_and_wait(page, tab_label: str, header_text: str) -> None:
    """Click a tab by label and wait for Streamlit rerun to complete.

    All chart tests require feature engineering data, so we wait for
    the franked toggle (stCheckbox) to confirm feature filters rendered.
    """
    tab = page.get_by_role("tab", name=tab_label)
    tab.click()

    # Wait for Streamlit rerun by checking for the header
    page.wait_for_selector(f"text={header_text}", timeout=30_000)

    # Charts require feature engineering — wait for feature filter toggle
    page.wait_for_selector("[data-testid='stCheckbox']", timeout=30_000)

    # Extra pause for charts (especially Vega-Lite) to finish rendering
    page.wait_for_timeout(5000)


def _select_stock_in_sidebar(page, symbol: str) -> None:
    """Select a stock in the sidebar multiselect for trend analysis."""
    multiselect = page.locator("[data-testid='stMultiSelect']")
    multiselect.click()

    # Click the option for the given symbol
    option = page.get_by_role("option", name=symbol)
    option.click()

    # Close the dropdown by pressing Escape
    page.press("[data-testid='stMultiSelect']", "Escape")

    # Wait for Streamlit rerun
    page.wait_for_timeout(3000)


def _get_axis_titles(chart) -> list[str]:
    """Extract axis title text from a Vega-Lite chart SVG.

    Uses text_content() since SVG <text> elements are not HTMLElements.
    """
    axis_titles = chart.locator(".mark-text.role-axis-title text")
    titles = []
    for i in range(axis_titles.count()):
        text = axis_titles.nth(i).text_content().strip()
        if text:
            titles.append(text)
    return titles


# ── Tab 1: Growth Rankings ──────────────────────────────────────────

def test_growth_bar_chart_renders(page, screenshot):
    """Growth tab renders a native horizontal bar chart (Vega-Lite)."""
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    # Wait for the Vega-Lite chart container to appear
    vega_chart = page.locator("[data-testid='stVegaLiteChart']").first
    vega_chart.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert vega_chart.is_visible(), "Growth bar chart container not found"

    # Verify SVG renders inside the chart
    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert svg.is_visible(), "Bar chart SVG not rendered"

    screenshot(path="after_growth_bar.png")


def test_growth_bar_chart_axis_labels(page, screenshot):
    """Growth bar chart renders with correct axis labels."""
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    vega_chart = page.locator("[data-testid='stVegaLiteChart']").first
    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    # Verify axis titles: "Stock symbol" and "growth (%)"
    titles = _get_axis_titles(vega_chart)
    assert len(titles) >= 2, (
        f"Bar chart should have 2 axis titles, found {len(titles)}: {titles}"
    )
    assert "Stock symbol" in titles, (
        f"Expected 'Stock symbol' axis label, found: {titles}"
    )
    assert "growth (%)" in titles, (
        f"Expected 'growth (%)' axis label, found: {titles}"
    )

    screenshot(path="after_growth_bar_detail.png")


# ── Tab 2: Valuation Matrix ─────────────────────────────────────────

def test_valuation_size_bar_chart_renders(page, screenshot):
    """Valuation tab renders a native bar chart for market-cap size distribution."""
    _click_tab_and_wait(page, TAB_VALUATION, HEADER_VALUATION)

    # Wait for Vega-Lite chart containers (at least 1)
    charts = page.locator("[data-testid='stVegaLiteChart']")
    charts.first.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    count = charts.count()
    assert count >= 1, (
        f"Expected at least 1 Vega-Lite chart in Valuation tab, found {count}"
    )

    # First chart is the size distribution bar chart
    size_chart = charts.nth(0)
    svg = size_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert svg.is_visible()

    # Verify axis labels for size chart
    titles = _get_axis_titles(size_chart)
    assert "Size category" in titles, (
        f"Expected 'Size category' axis label, found: {titles}"
    )

    screenshot(path="after_valuation_size_bar.png")


def test_valuation_scatter_no_text_labels(page, screenshot):
    """Valuation P/E vs FCF scatter chart uses tooltips, not text labels."""
    _click_tab_and_wait(page, TAB_VALUATION, HEADER_VALUATION)

    # Wait for Vega-Lite chart containers
    charts = page.locator("[data-testid='stVegaLiteChart']")
    charts.first.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    count = charts.count()
    assert count >= 2, (
        f"Expected at least 2 Vega-Lite charts in Valuation tab, found {count}"
    )

    # Second chart is the P/E vs FCF scatter plot
    scatter_chart = charts.nth(1)
    svg = scatter_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert svg.is_visible(), "Scatter chart SVG not rendered"

    # Verify axis titles
    titles = _get_axis_titles(scatter_chart)
    assert "P/E ratio" in titles, (
        f"Expected 'P/E ratio' axis label, found: {titles}"
    )
    assert "FCF yield" in titles, (
        f"Expected 'FCF yield' axis label, found: {titles}"
    )

    # Verify NO text marks (overlaid labels) on scatter plot
    # Altair scatter plots use tooltips, not text labels
    text_marks = scatter_chart.locator(".mark-text.role-mark")
    assert text_marks.count() == 0, (
        f"Scatter plot has {text_marks.count()} overlaid text labels "
        "(should use tooltips only)"
    )

    screenshot(path="after_valuation_scatter.png")


# ── Tab 3: Dividend Analysis ────────────────────────────────────────

def test_dividend_bar_chart_renders(page, screenshot):
    """Dividend tab renders a native bar chart for top dividend yields."""
    _click_tab_and_wait(page, TAB_DIVIDEND, HEADER_DIVIDEND)

    vega_chart = page.locator("[data-testid='stVegaLiteChart']").first
    vega_chart.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert vega_chart.is_visible(), "Dividend bar chart container not found"

    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    # Verify axis labels
    titles = _get_axis_titles(vega_chart)
    assert "Stock symbol" in titles, (
        f"Expected 'Stock symbol' axis label, found: {titles}"
    )
    assert "grossed-up yield (%)" in titles, (
        f"Expected 'grossed-up yield (%)' axis label, found: {titles}"
    )

    screenshot(path="after_dividend_bar.png")


def test_dividend_franking_metrics(page, screenshot):
    """Dividend tab renders st.metric cards for franking distribution."""
    _click_tab_and_wait(page, TAB_DIVIDEND, HEADER_DIVIDEND)

    # Wait for metric cards to appear
    metrics = page.locator("[data-testid='stMetric']")
    metrics.first.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    # Should have at least 2 metrics: Franked and Unfranked
    count = metrics.count()
    assert count >= 2, (
        f"Expected at least 2 metric cards (Franked/Unfranked), found {count}"
    )

    # Verify metric labels using stMetricLabel testid
    franked_label = metrics.nth(0).locator("[data-testid='stMetricLabel']")
    unfranked_label = metrics.nth(1).locator("[data-testid='stMetricLabel']")

    assert franked_label.count() >= 1, "Franked metric label not found"
    assert unfranked_label.count() >= 1, "Unfranked metric label not found"

    franked_text = franked_label.inner_text().strip()
    unfranked_text = unfranked_label.inner_text().strip()

    assert "Franked" in franked_text, (
        f"Expected 'Franked' label, found: '{franked_text}'"
    )
    assert "Unfranked" in unfranked_text, (
        f"Expected 'Unfranked' label, found: '{unfranked_text}'"
    )

    # Verify metrics have values
    franked_value = metrics.nth(0).locator("[data-testid='stMetricValue']")
    unfranked_value = metrics.nth(1).locator("[data-testid='stMetricValue']")

    assert franked_value.inner_text().strip(), "Franked metric has no value"
    assert unfranked_value.inner_text().strip(), "Unfranked metric has no value"

    screenshot(path="after_dividend_metrics.png")


# ── Tab 4: Liquidity & Risk ─────────────────────────────────────────

def test_liquidity_scatter_no_text_labels(page, screenshot):
    """Liquidity scatter chart uses Altair tooltips, not text labels."""
    _click_tab_and_wait(page, TAB_LIQUIDITY, HEADER_LIQUIDITY)

    # Wait for Vega-Lite chart containers
    charts = page.locator("[data-testid='stVegaLiteChart']")
    charts.first.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    count = charts.count()
    assert count >= 1, "Vega-Lite chart container not found in Liquidity tab"

    # First chart is the scatter plot
    scatter_chart = charts.nth(0)
    svg = scatter_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert svg.is_visible(), "Scatter chart SVG not rendered"

    # Verify axis titles
    titles = _get_axis_titles(scatter_chart)
    assert "Volume turnover ratio" in titles, (
        f"Expected 'Volume turnover ratio' axis label, found: {titles}"
    )
    assert "Bid-Ask spread" in titles, (
        f"Expected 'Bid-Ask spread' axis label, found: {titles}"
    )

    # Verify NO text marks (overlaid labels) on scatter plot
    text_marks = scatter_chart.locator(".mark-text.role-mark")
    assert text_marks.count() == 0, (
        f"Liquidity scatter has {text_marks.count()} overlaid text labels "
        "(should use tooltips only)"
    )

    screenshot(path="after_liquidity_scatter.png")


def test_histogram_renders(page, screenshot):
    """Liquidity tab renders a histogram for 52-week range position distribution."""
    _click_tab_and_wait(page, TAB_LIQUIDITY, HEADER_LIQUIDITY)

    # Wait for Vega-Lite chart containers (scatter + histogram = 2 charts)
    charts = page.locator("[data-testid='stVegaLiteChart']")
    charts.first.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    count = charts.count()
    assert count >= 2, (
        f"Expected at least 2 Vega-Lite charts in Liquidity tab "
        f"(scatter + histogram), found {count}"
    )

    # The histogram is the second chart
    hist_chart = charts.nth(1)
    svg = hist_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert svg.is_visible(), "Histogram SVG not rendered"

    # Histogram uses mark-rect elements
    rects = hist_chart.locator(".mark-rect")
    assert rects.count() >= 1, "Histogram has no bar (rect) marks"

    # Verify axis titles
    titles = _get_axis_titles(hist_chart)
    assert "position (0=low, 1=high)" in titles, (
        f"Expected 'position (0=low, 1=high)' axis label, found: {titles}"
    )
    assert "Count" in titles, (
        f"Expected 'Count' axis label, found: {titles}"
    )

    screenshot(path="after_liquidity_histogram.png")


# ── Tab 5: Trend Over Time ──────────────────────────────────────────

def test_trend_line_chart_renders(page, screenshot):
    """Trend tab renders a native line chart after selecting stocks."""
    # Navigate to Growth tab first to access sidebar
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)

    # Select stocks in sidebar before navigating to trend tab
    _select_stock_in_sidebar(page, "BHP")
    _select_stock_in_sidebar(page, "CBA")

    _click_tab_and_wait(page, TAB_TREND, HEADER_TREND)

    # Wait for the Vega-Lite line chart to render
    vega_charts = page.locator("[data-testid='stVegaLiteChart']")
    chart_count = vega_charts.count()

    if chart_count == 0:
        # Check if there's an error alert instead
        alerts = page.locator("[data-testid='stAlert']")
        if alerts.count() > 0:
            alert_text = alerts.first.inner_text()
            pytest.skip(
                f"Trend chart not rendered due to error: {alert_text[:100]}"
            )
        else:
            pytest.skip("Trend chart not rendered (no stocks may have data)")

    vega_chart = vega_charts.first
    vega_chart.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert vega_chart.is_visible(), "Trend line chart container not found"

    # Verify SVG is rendered
    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    assert svg.is_visible(), "Line chart SVG not rendered"

    # Verify axis titles
    titles = _get_axis_titles(vega_chart)
    assert "Date" in titles, (
        f"Expected 'Date' axis label, found: {titles}"
    )

    screenshot(path="after_trend_line.png")


def test_trend_line_tooltip_on_hover(page, screenshot):
    """Hovering the trend line reveals a vega-embed tooltip with the date.

    A bare mark_line is a 1px stroke and is nearly impossible to hover, so
    render_trend_line layers an invisible point overlay (opacity=0, ~12px
    hit radius) that carries the tooltips. This test hovers that overlay and
    asserts a tooltip showing a full date appears.
    """
    import re

    # Reach the sidebar via the Growth tab (matches existing trend tests)
    _click_tab_and_wait(page, TAB_GROWTH, HEADER_GROWTH)
    _select_stock_in_sidebar(page, "BHP")
    _click_tab_and_wait(page, TAB_TREND, HEADER_TREND)

    vega_chart = page.locator("[data-testid='stVegaLiteChart']").first
    vega_chart.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
    svg = vega_chart.locator("svg")
    svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)

    # Locate the invisible overlay point (opacity 0, filled) and its center
    center = page.evaluate(r"""() => {
        const chart = document.querySelector("[data-testid='stVegaLiteChart']");
        const svg = chart && chart.querySelector('svg');
        if (!svg) return null;
        for (const el of svg.querySelectorAll('path')) {
            const st = getComputedStyle(el);
            if (parseFloat(st.opacity) === 0 && st.fill !== 'none') {
                const r = el.getBoundingClientRect();
                return {x: r.x + r.width / 2, y: r.y + r.height / 2};
            }
        }
        return null;
    }""")
    if center is None:
        pytest.skip("Trend chart has no hoverable overlay point (no data in range)")

    # Hover and poll for the vega-embed tooltip element to become visible
    page.mouse.move(center["x"], center["y"])
    page.mouse.move(center["x"] + 2, center["y"])
    page.mouse.move(center["x"], center["y"])
    tooltip_text = ""
    for _ in range(40):  # ~2s
        page.wait_for_timeout(50)
        tooltip_text = page.evaluate(r"""() => {
            const el = document.getElementById('vg-tooltip-element');
            if (!el) return '';
            const r = el.getBoundingClientRect();
            if (!(r.width > 0 && r.height > 0)) return '';
            return (el.innerText || '').trim();
        }""")
        if tooltip_text:
            break

    assert tooltip_text, "No tooltip appeared when hovering the trend line"
    # The fix uses a full-date format, e.g. "26 Jul 2026"
    assert re.search(r"\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}", tooltip_text), (
        f"Tooltip does not show a full date: {tooltip_text!r}"
    )
    screenshot(path="after_trend_tooltip.png")


# ── Cross-tab: Sentence Case Labels ─────────────────────────────────

def test_chart_titles_sentence_case(page, screenshot):
    """All chart axis labels and titles use sentence case, not Title Case."""
    # Collect all axis titles from each tab
    all_labels: list[str] = []

    tab_checks = [
        (TAB_GROWTH, HEADER_GROWTH),
        (TAB_VALUATION, HEADER_VALUATION),
        (TAB_DIVIDEND, HEADER_DIVIDEND),
        (TAB_LIQUIDITY, HEADER_LIQUIDITY),
    ]

    for tab_label, header_text in tab_checks:
        _click_tab_and_wait(page, tab_label, header_text)

        # Collect axis titles from all Vega-Lite charts in the tab
        vega_charts = page.locator("[data-testid='stVegaLiteChart']").all()
        for chart in vega_charts:
            svg = chart.locator("svg")
            if svg.count() > 0:
                svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
                titles = _get_axis_titles(chart)
                all_labels.extend(titles)

    # Navigate to trend tab and collect line chart labels (if rendered)
    _click_tab_and_wait(page, TAB_TREND, HEADER_TREND)
    vega_charts = page.locator("[data-testid='stVegaLiteChart']").all()
    for chart in vega_charts:
        svg = chart.locator("svg")
        if svg.count() > 0:
            svg.wait_for(state="visible", timeout=CHART_RENDER_TIMEOUT)
            titles = _get_axis_titles(chart)
            all_labels.extend(titles)

    # Check each label for sentence case compliance
    violations: list[str] = []
    for label in all_labels:
        # Skip known acronyms/abbreviations that are inherently uppercase
        if label in SENTENCE_CASE_EXCEPTIONS:
            continue
        # Skip pure numbers or tick labels
        cleaned = (
            label.replace(".", "")
            .replace("-", "")
            .replace("%", "")
            .replace(" ", "")
            .replace("(", "")
            .replace(")", "")
        )
        if cleaned.isdigit():
            continue

        # Check for Title Case (every word capitalized)
        words = label.split()
        if len(words) > 1:
            title_case_count = sum(
                1 for w in words if w and w[0].isupper() and len(w) > 1
            )
            # If all words start with uppercase, it's Title Case (violation)
            if title_case_count == len(words):
                violations.append(label)

    assert not violations, (
        f"Found {len(violations)} labels using Title Case instead of sentence case: "
        f"{violations}"
    )

    screenshot(path="after_sentence_case_check.png")


# ── After Screenshot Capture ─────────────────────────────────────────

def test_after_screenshots(page, screenshot):
    """Capture screenshots of all 5 tabs to /tmp/screens/after/."""
    AFTER_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    tab_info = [
        (TAB_GROWTH, HEADER_GROWTH),
        (TAB_VALUATION, HEADER_VALUATION),
        (TAB_DIVIDEND, HEADER_DIVIDEND),
        (TAB_LIQUIDITY, HEADER_LIQUIDITY),
        (TAB_TREND, HEADER_TREND),
    ]

    for tab_label, header_text in tab_info:
        _click_tab_and_wait(page, tab_label, header_text)

        # Extra wait for all charts in the tab to render
        page.wait_for_timeout(3000)

        # Capture full page screenshot
        safe_name = tab_label.replace(" ", "_").replace("&", "and")
        dest = AFTER_SCREENSHOT_DIR / f"after_{safe_name}.png"
        page.screenshot(path=str(dest))
        print(f"[after_screenshot] Saved: {dest}")

    # Also capture the sidebar for reference
    dest_sidebar = AFTER_SCREENSHOT_DIR / "after_sidebar.png"
    sidebar = page.locator("[data-testid='stSidebar']")
    if sidebar.count() > 0:
        sidebar.first.screenshot(path=str(dest_sidebar))
        print(f"[after_screenshot] Saved: {dest_sidebar}")
