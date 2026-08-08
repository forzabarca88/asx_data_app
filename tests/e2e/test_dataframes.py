"""E2E tests for data table rendering and formatting.

Verifies that all dataframes in the Streamlit app render correctly with
proper column headers from column_config, correct data, and no Pandas
Styler HTML artifacts.

Streamlit dataframes render using Glide Data Grid (Canvas-based virtual
rendering). The visible display is on a <canvas> element which Playwright
cannot read. However, Streamlit also maintains a hidden <table> element
with role="grid" for accessibility (screen readers). This hidden table
contains:
  - Column headers in <th role="columnheader"> (with display names from
    column_config)
  - Data cells in <td role="gridcell"> with data-testid="glide-cell-C-R"
    (C=column index, R=row index, 0-based)

The hidden table contains raw (unformatted) values. The formatted display
values are rendered on the Canvas and cannot be accessed via DOM queries.
These tests verify:
  1. Dataframe container is visible
  2. Column headers match column_config display names
  3. Data rows exist with correct symbols
  4. No Pandas Styler artifacts in the hidden table
"""

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so we can import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import (
    HEADER_DIVIDEND_ANALYSIS,
    HEADER_LIQUIDITY_RISK,
    HEADER_VALUATION_MATRIX,
    TAB_DIVIDEND_ANALYSIS,
    TAB_LIQUIDITY_RISK,
    TAB_VALUATION_MATRIX,
)

# Expected tab labels (partial match for clicking)
TAB_VALUATION = TAB_VALUATION_MATRIX
TAB_DIVIDEND = TAB_DIVIDEND_ANALYSIS
TAB_LIQUIDITY = TAB_LIQUIDITY_RISK

# Expected header text for each tab
HEADER_VALUATION = HEADER_VALUATION_MATRIX
HEADER_DIVIDEND = HEADER_DIVIDEND_ANALYSIS
HEADER_LIQUIDITY = HEADER_LIQUIDITY_RISK

# Render timeout
RENDER_TIMEOUT = 30_000

# ── Expected column headers per tab ──────────────────────────────────

# Tab 2: Valuation Matrix
VALUATION_HEADERS = [
    "Symbol",
    "Market cap ($M)",
    "P/E ratio",
    "Earnings yield",
    "Price/cash",
    "FCF yield",
]

# Tab 3: Dividend Analysis
DIVIDEND_HEADERS = [
    "Symbol",
    "Raw yield (%)",
    "Franking multiplier",
    "Grossed-up yield (%)",
    "Payout ratio (%)",
    "Currency risk",
]

# Tab 4: Liquidity & Risk
LIQUIDITY_HEADERS = [
    "Symbol",
    "Bid-Ask spread (%)",
    "52W range position (%)",
    "Volume turnover (%)",
    "Intraday volatility (%)",
]

# Mock API symbols
MOCK_SYMBOLS = ["BHP", "CBA", "CSL", "WES", "WBC"]


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

    All dataframe tests require feature engineering data, so we wait for
    the franked toggle (stCheckbox) to confirm feature filters rendered.
    """
    tab = page.get_by_role("tab", name=tab_label)
    tab.click()
    page.wait_for_selector(f"text={header_text}", timeout=30_000)

    # Dataframes require feature engineering — wait for feature filter toggle
    page.wait_for_selector("[data-testid='stCheckbox']", timeout=30_000)

    # Extra pause for dataframe to finish rendering
    page.wait_for_timeout(5000)


def _get_df_info(page) -> dict:
    """Extract dataframe structure from the hidden accessibility table.

    Returns dict with:
      - container_visible: bool
      - headers: list of column header display names
      - row_count: number of data rows
      - col_count: number of columns
      - symbols: list of symbol values from first column
      - cell_values: dict mapping "col-row" to raw cell text
      - has_style_elements: bool (Pandas Styler check)
      - has_inline_styles: bool (Pandas Styler check)
      - has_styler_classes: set of Pandas Styler class names found
    """
    return page.evaluate("""() => {
        const container = document.querySelector('[data-testid="stDataFrame"]');
        if (!container) return {error: 'no dataframe container'};

        const rect = container.getBoundingClientRect();
        const style = window.getComputedStyle(container);
        const containerVisible = (
            rect.width > 0 && rect.height > 0 &&
            style.display !== 'none' && style.visibility !== 'hidden'
        );

        const table = container.querySelector('table[role="grid"]');
        if (!table) return {error: 'no grid table'};

        // Column headers
        const headers = [];
        const ths = table.querySelectorAll('thead th');
        ths.forEach(th => headers.push(th.innerText.trim()));

        // Data rows and cells
        const rows = table.querySelectorAll('tbody tr');
        const row_count = rows.length;
        const col_count = table.getAttribute('aria-colcount');

        const symbols = [];
        const cell_values = {};

        rows.forEach((row, rowIdx) => {
            const cells = row.querySelectorAll('td[role="gridcell"]');
            cells.forEach((cell, colIdx) => {
                const text = cell.innerText.trim();
                cell_values[`${colIdx}-${rowIdx}`] = text;
                if (colIdx === 0) {
                    symbols.push(text);
                }
            });
        });

        // Pandas Styler checks
        const styleElements = container.querySelectorAll('style');
        const hasStyleElements = styleElements.length > 0;

        const tds = table.querySelectorAll('tbody td');
        let hasInlineStyles = false;
        tds.forEach(td => {
            if (td.style.cssText) hasInlineStyles = true;
        });
        const thsForStyle = table.querySelectorAll('thead th');
        thsForStyle.forEach(th => {
            if (th.style.cssText) hasInlineStyles = true;
        });

        const tableClass = (table.getAttribute('class') || '').split(' ');
        const stylerClasses = new Set();
        const stylerClassNames = ['dataframe', 'index_name', 'col_heading',
                                   'header', 'bool', 'numeric', 'text'];
        tableClass.forEach(c => {
            if (stylerClassNames.includes(c)) stylerClasses.add(c);
        });

        return {
            container_visible: containerVisible,
            headers,
            row_count,
            col_count: parseInt(col_count),
            symbols,
            cell_values,
            has_style_elements: hasStyleElements,
            has_inline_styles: hasInlineStyles,
            has_styler_classes: Array.from(stylerClasses),
        };
    }""")


# ── Tab 2: Valuation Matrix ─────────────────────────────────────────

def test_valuation_dataframe_renders(page, screenshot):
    """Valuation tab renders a dataframe with correct column headers
    and data rows."""
    _click_tab_and_wait(page, TAB_VALUATION, HEADER_VALUATION)

    info = _get_df_info(page)

    # Container must be visible
    assert info["container_visible"], "Valuation dataframe container not visible"

    # Column headers must match column_config display names
    assert info["headers"] == VALUATION_HEADERS, (
        f"Valuation headers mismatch.\n"
        f"Expected: {VALUATION_HEADERS}\n"
        f"Got:      {info['headers']}"
    )

    # Must have data rows (mock has 5 symbols)
    assert info["row_count"] >= 1, (
        f"Valuation dataframe has no data rows (got {info['row_count']})"
    )

    # Column count must match
    assert info["col_count"] == len(VALUATION_HEADERS), (
        f"Expected {len(VALUATION_HEADERS)} columns, got {info['col_count']}"
    )

    # Verify symbols from mock data are present
    assert set(info["symbols"]) == set(MOCK_SYMBOLS), (
        f"Expected symbols {MOCK_SYMBOLS}, got {info['symbols']}"
    )

    screenshot(path="df_valuation.png")


# ── Tab 3: Dividend Analysis ─────────────────────────────────────────

def test_dividend_dataframe_renders(page, screenshot):
    """Dividend tab renders a dataframe with correct column headers
    and data rows."""
    _click_tab_and_wait(page, TAB_DIVIDEND, HEADER_DIVIDEND)

    info = _get_df_info(page)

    assert info["container_visible"], "Dividend dataframe container not visible"

    assert info["headers"] == DIVIDEND_HEADERS, (
        f"Dividend headers mismatch.\n"
        f"Expected: {DIVIDEND_HEADERS}\n"
        f"Got:      {info['headers']}"
    )

    assert info["row_count"] >= 1, (
        f"Dividend dataframe has no data rows (got {info['row_count']})"
    )

    assert info["col_count"] == len(DIVIDEND_HEADERS), (
        f"Expected {len(DIVIDEND_HEADERS)} columns, got {info['col_count']}"
    )

    assert set(info["symbols"]) == set(MOCK_SYMBOLS), (
        f"Expected symbols {MOCK_SYMBOLS}, got {info['symbols']}"
    )

    screenshot(path="df_dividend.png")


# ── Tab 4: Liquidity & Risk ──────────────────────────────────────────

def test_liquidity_dataframe_renders(page, screenshot):
    """Liquidity tab renders a dataframe with correct column headers
    and data rows."""
    _click_tab_and_wait(page, TAB_LIQUIDITY, HEADER_LIQUIDITY)

    info = _get_df_info(page)

    assert info["container_visible"], "Liquidity dataframe container not visible"

    assert info["headers"] == LIQUIDITY_HEADERS, (
        f"Liquidity headers mismatch.\n"
        f"Expected: {LIQUIDITY_HEADERS}\n"
        f"Got:      {info['headers']}"
    )

    assert info["row_count"] >= 1, (
        f"Liquidity dataframe has no data rows (got {info['row_count']})"
    )

    assert info["col_count"] == len(LIQUIDITY_HEADERS), (
        f"Expected {len(LIQUIDITY_HEADERS)} columns, got {info['col_count']}"
    )

    assert set(info["symbols"]) == set(MOCK_SYMBOLS), (
        f"Expected symbols {MOCK_SYMBOLS}, got {info['symbols']}"
    )

    screenshot(path="df_liquidity.png")


# ── Cross-tab: Column Formatting ─────────────────────────────────────

def test_column_formatting(page, screenshot):
    """Verify column_config formatting is applied correctly.

    Streamlit's DataGrid renders formatted values on a Canvas (not
    accessible via DOM). The hidden table contains raw values. This test
    verifies:
    1. Column headers use display names from column_config
    2. Numeric columns contain valid numeric values
    3. Percentage columns show values that would format with % suffix
    4. Currency columns show values that would format with $ prefix

    Note: The actual formatted display (e.g., '$1,234.56' vs '1234.56')
    is rendered on Canvas and verified visually via screenshots.
    """
    # ── Valuation Matrix ────────────────────────────────────────────
    _click_tab_and_wait(page, TAB_VALUATION, HEADER_VALUATION)
    val_info = _get_df_info(page)

    # Headers use column_config display names
    assert val_info["headers"] == VALUATION_HEADERS

    # Verify numeric values in numeric columns
    for row_idx in range(val_info["row_count"]):
        # Col 1: Market cap ($M) — should be numeric
        mc = val_info["cell_values"].get(f"1-{row_idx}", "")
        assert mc.replace(",", "").replace(".", "").replace("-", "").isdigit() or mc == "", (
            f"Market cap not numeric: '{mc}'"
        )

        # Col 2: P/E ratio — should be numeric
        pe = val_info["cell_values"].get(f"2-{row_idx}", "")
        assert _is_numeric(pe), f"P/E ratio not numeric: '{pe}'"

        # Col 3: Earnings yield — should be numeric
        ey = val_info["cell_values"].get(f"3-{row_idx}", "")
        assert _is_numeric(ey), f"Earnings yield not numeric: '{ey}'"

        # Col 4: Price/cash — should be numeric
        pc = val_info["cell_values"].get(f"4-{row_idx}", "")
        assert _is_numeric(pc), f"Price/cash not numeric: '{pc}'"

        # Col 5: FCF yield — should be numeric
        fcf = val_info["cell_values"].get(f"5-{row_idx}", "")
        assert _is_numeric(fcf), f"FCF yield not numeric: '{fcf}'"

    # ── Dividend Analysis ───────────────────────────────────────────
    _click_tab_and_wait(page, TAB_DIVIDEND, HEADER_DIVIDEND)
    div_info = _get_df_info(page)

    assert div_info["headers"] == DIVIDEND_HEADERS

    for row_idx in range(div_info["row_count"]):
        # Col 1: Raw yield (%) — percentage value (raw * 100)
        ry = div_info["cell_values"].get(f"1-{row_idx}", "")
        assert _is_numeric(ry), f"Raw yield not numeric: '{ry}'"

        # Col 2: Franking multiplier — ratio value
        fm = div_info["cell_values"].get(f"2-{row_idx}", "")
        assert _is_numeric(fm), f"Franking multiplier not numeric: '{fm}'"

        # Col 3: Grossed-up yield (%) — percentage value
        gy = div_info["cell_values"].get(f"3-{row_idx}", "")
        assert _is_numeric(gy), f"Grossed-up yield not numeric: '{gy}'"

        # Col 4: Payout ratio (%) — percentage value
        pr = div_info["cell_values"].get(f"4-{row_idx}", "")
        assert _is_numeric(pr), f"Payout ratio not numeric: '{pr}'"

        # Col 5: Currency risk — text value with Material Symbols icons
        # e.g., ":material/attach_money: AUD" or ":material/warning: FX Risk"
        cr = div_info["cell_values"].get(f"5-{row_idx}", "")
        assert cr in (
            "AUD", " FX Risk", "",                        # plain text variants
            ":material/attach_money: AUD",                # AUD icon
            ":material/warning: FX Risk",                 # FX risk icon
        ), (
            f"Currency risk unexpected value: '{cr}'"
        )

    # ── Liquidity & Risk ────────────────────────────────────────────
    _click_tab_and_wait(page, TAB_LIQUIDITY, HEADER_LIQUIDITY)
    liq_info = _get_df_info(page)

    assert liq_info["headers"] == LIQUIDITY_HEADERS

    for row_idx in range(liq_info["row_count"]):
        # Col 1: Bid-Ask spread (%) — percentage value
        ba = liq_info["cell_values"].get(f"1-{row_idx}", "")
        assert _is_numeric(ba), f"Bid-Ask spread not numeric: '{ba}'"

        # Col 2: 52W range position (%) — percentage value
        rp = liq_info["cell_values"].get(f"2-{row_idx}", "")
        assert _is_numeric(rp), f"52W range position not numeric: '{rp}'"

        # Col 3: Volume turnover (%) — percentage value
        vt = liq_info["cell_values"].get(f"3-{row_idx}", "")
        assert _is_numeric(vt), f"Volume turnover not numeric: '{vt}'"

        # Col 4: Intraday volatility (%) — percentage value
        iv = liq_info["cell_values"].get(f"4-{row_idx}", "")
        assert _is_numeric(iv), f"Intraday volatility not numeric: '{iv}'"

    screenshot(path="df_formatting_check.png")


def _is_numeric(value: str) -> bool:
    """Check if a string represents a valid number."""
    if not value:
        return True  # Empty/NaN is acceptable
    try:
        float(value)
        return True
    except ValueError:
        return False


# ── Cross-tab: No Pandas Styler Artifacts ────────────────────────────

def test_no_styler_artifacts(page, screenshot):
    """Verify no Pandas Styler HTML artifacts in dataframe output.

    Pandas Styler produces HTML with:
    - <style> blocks embedded in the output
    - Inline style attributes on <td>/<th> elements
    - Class names like 'dataframe', 'index_name', 'col_heading'
    - Extra wrapper <div> elements

    Streamlit's native dataframe rendering (with column_config) should
    produce clean HTML tables without these artifacts.

    Note: We check the hidden accessibility table since the visible
    Canvas rendering cannot be inspected via DOM queries.
    """
    tabs_to_check = [
        (TAB_VALUATION, HEADER_VALUATION, "Valuation"),
        (TAB_DIVIDEND, HEADER_DIVIDEND, "Dividend"),
        (TAB_LIQUIDITY, HEADER_LIQUIDITY, "Liquidity"),
    ]

    for tab_label, header_text, tab_name in tabs_to_check:
        _click_tab_and_wait(page, tab_label, header_text)
        info = _get_df_info(page)

        # Check 1: No <style> elements inside the dataframe container
        assert not info["has_style_elements"], (
            f"{tab_name} dataframe contains <style> elements "
            f"(Pandas Styler artifact)"
        )

        # Check 2: No inline style attributes on <td>/<th> elements
        assert not info["has_inline_styles"], (
            f"{tab_name} dataframe cells have inline style attributes "
            f"(Pandas Styler artifact)"
        )

        # Check 3: No Pandas Styler class names on table elements
        assert not info["has_styler_classes"], (
            f"{tab_name} dataframe table has Pandas Styler classes: "
            f"{info['has_styler_classes']}"
        )

    screenshot(path="df_no_styler_check.png")
