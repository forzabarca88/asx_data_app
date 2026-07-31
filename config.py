"""Central configuration for the ASX Stock Analysis Dashboard.

All hardcoded values from the application are defined here as constants
to enable easy maintenance and consistent usage across the codebase.

Theme colors are read from .streamlit/config.toml at module load time
to avoid duplication — the TOML file is the single source of truth.
"""

import datetime
import tomllib
from pathlib import Path

# ── App Config ──────────────────────────────────────────────────────

# Browser tab title
APP_PAGE_TITLE = "ASX dashboard"
# Page heading displayed in the app
APP_TITLE = "ASX stock analysis dashboard"
APP_LAYOUT = "wide"

# ── Sidebar Defaults ────────────────────────────────────────────────

# Default lookback period in days for date range selection
SIDEBAR_DATE_RANGE_DAYS = 90

# Default minimum filters
SIDEBAR_MIN_MARKET_CAP = 0.0  # in dollars (raw value)
SIDEBAR_MIN_YIELD = 0.0       # in percent
SIDEBAR_SHOW_ONLY_FRANKED = False

# ── Date Config ─────────────────────────────────────────────────────

# Earliest allowed date for the date input widget
DATE_INPUT_MIN = datetime.date(2020, 1, 1)

# ── Widget Labels (sentence case) ───────────────────────────────────

# Sidebar section headers
LABEL_SIDEBAR_CONTROLS = "Controls"
LABEL_SIDEBAR_FEATURE_FILTERS = "Feature filters"

# Sidebar widget labels
LABEL_DATE_RANGE = "Date range"
LABEL_STOCKS_FOR_TREND = "Stocks for trend analysis"
LABEL_GROWTH_FACTOR = "Growth factor"
LABEL_TOP_N_GROWTH = "Top N growth stocks"
LABEL_MIN_MARKET_CAP = "Min market cap ($M)"
LABEL_MIN_GROSSED_UP_YIELD = "Min grossed-up yield (%)"
LABEL_FRANKED_DIVIDENDS_ONLY = "Franked dividends only"
LABEL_SHOW_ONLY_FRANKED = "Show only franked"

# Widget help text
HELP_STOCKS_FOR_TREND = "Choose stocks to compare in the trend chart"
HELP_GROWTH_FACTOR = "Select the metric to calculate growth over time"

# Widget step values
STEP_MIN_MARKET_CAP = 100.0
STEP_MIN_YIELD = 0.5

# ── Tab Config ──────────────────────────────────────────────────────

TAB_GROWTH_RANKINGS = "Growth rankings"
TAB_VALUATION_MATRIX = "Valuation matrix"
TAB_DIVIDEND_ANALYSIS = "Dividend analysis"
TAB_LIQUIDITY_RISK = "Liquidity & risk"
TAB_TREND_OVER_TIME = "Trend over time"

TABS: list[str] = [
    TAB_GROWTH_RANKINGS,
    TAB_VALUATION_MATRIX,
    TAB_DIVIDEND_ANALYSIS,
    TAB_LIQUIDITY_RISK,
    TAB_TREND_OVER_TIME,
]

# ── Icon Mappings (Material Symbols) ────────────────────────────────

ICON_APP = ":material/show_chart:"
ICON_CONTROLS = ":material/tune:"
ICON_FEATURE_FILTERS = ":material/filter_list:"

# Sidebar widget icons
ICON_DATE_RANGE = ":material/calendar_month:"
ICON_STOCKS_FOR_TREND = ":material/show_chart:"
ICON_GROWTH_FACTOR = ":material/trending_up:"
ICON_TOP_N_GROWTH = ":material/numbers:"
ICON_MIN_MARKET_CAP = ":material/business:"
ICON_MIN_GROSSED_UP_YIELD = ":material/percent:"
ICON_FRANKED_DIVIDENDS_ONLY = ":material/verified:"

# Tab icons
ICON_TAB_GROWTH = ":material/trending_up:"
ICON_TAB_VALUATION = ":material/attach_money:"
ICON_TAB_DIVIDEND = ":material/savings:"
ICON_TAB_LIQUIDITY = ":material/water_drop:"
ICON_TAB_TREND = ":material/timeline:"

TAB_ICONS: dict[str, str] = {
    TAB_GROWTH_RANKINGS: ICON_TAB_GROWTH,
    TAB_VALUATION_MATRIX: ICON_TAB_VALUATION,
    TAB_DIVIDEND_ANALYSIS: ICON_TAB_DIVIDEND,
    TAB_LIQUIDITY_RISK: ICON_TAB_LIQUIDITY,
    TAB_TREND_OVER_TIME: ICON_TAB_TREND,
}

# Header icons
ICON_HEADER_GROWTH = ":material/trending_up:"
ICON_HEADER_VALUATION = ":material/attach_money:"
ICON_HEADER_DIVIDEND = ":material/savings:"
ICON_HEADER_LIQUIDITY = ":material/water_drop:"
ICON_HEADER_TREND = ":material/timeline:"

# Callout icons
ICON_CALLOUT_ERROR = ":material/error:"
ICON_CALLOUT_WARNING = ":material/warning:"
ICON_CALLOUT_INFO = ":material/info:"
ICON_CALLOUT_SUCCESS = ":material/check_circle:"

# Currency risk icon
ICON_CURRENCY_RISK = ":material/warning:"
ICON_CURRENCY_AUD = ":material/attach_money:"


# ── Header Labels ───────────────────────────────────────────────────

# Tab 1 header is dynamic: "Top N Growth Stocks ({factor or 'N/A'})"
HEADER_GROWTH_TEMPLATE = "Top N growth stocks ({})"
HEADER_GROWTH_FALLBACK = "N/A"
HEADER_VALUATION_MATRIX = "Valuation matrix"
HEADER_DIVIDEND_ANALYSIS = "Dividend & franking analysis"
HEADER_LIQUIDITY_RISK = "Liquidity & technical risk"
HEADER_TREND_OVER_TIME = "Trend over time"

# ── Chart Config ────────────────────────────────────────────────────

# Top N growth slider settings
TOP_N_DEFAULT = 10
TOP_N_MIN = 5
TOP_N_MAX = 50

# Top N for dividend ranking chart
TOP_N_DIVIDEND = 15

# Size category buckets for market cap classification
SIZE_BUCKET_BINS = [0, 50, 200, 2000, float("inf")]
SIZE_BUCKET_LABELS = ["Micro", "Small", "Mid", "Large"]
SIZE_BUCKET_COLORS: dict[str, str] = {
    "Micro": "grey",
    "Small": "blue",
    "Mid": "green",
    "Large": "red",
}

# Color scales for charts
COLOR_SCALE_GROWTH = "RdYlGn"
COLOR_SCALE_DIVIDEND = "YlOrRd"
COLOR_SEQUENCE_LIQUIDITY = ["steelblue"]

# Chart axis settings
CHART_XAXIS_TICK_ANGLE = -45
CHART_DATE_FORMAT = "%d %b %Y"
CHART_DATE_TICK_COUNT = 8
# Invisible overlay point size (px^2) giving a ~12px hover radius for
# trend line tooltips. Lines alone are 1px and nearly impossible to hover.
CHART_TREND_POINT_HIT_SIZE = 600
CHART_HISTOGRAM_NBINS = 20

# Chart labels
CHART_LABEL_STOCK_SYMBOL = "Stock symbol"
CHART_LABEL_GROWTH_PCT = "growth (%)"
CHART_LABEL_PE_RATIO = "P/E ratio"
CHART_LABEL_FCF_YIELD = "FCF yield"
CHART_LABEL_VOLUME_TURNOVER = "Volume turnover ratio"
CHART_LABEL_BID_ASK_SPREAD = "Bid-Ask spread"
CHART_LABEL_RANGE_POSITION = "position (0=low, 1=high)"
CHART_LABEL_DATE = "Date"
CHART_LABEL_STOCK = "Stock"
CHART_LABEL_SIZE_CATEGORY = "Size category"
CHART_LABEL_STOCK_COUNT = "Number of stocks"
CHART_LABEL_GROSS_DIVIDEND_YIELD = "grossed-up yield (%)"
CHART_LABEL_MARKET_CAP = "Market cap"
CHART_LABEL_EARNINGS_YIELD = "Earnings yield"
CHART_LABEL_52W_RANGE_POSITION = "52W range position"
CHART_LABEL_INTRADAY_VOLATILITY = "Intraday volatility"

# Chart titles
CHART_TITLE_MARKET_CAP_DIST = "Market cap distribution"
CHART_TITLE_PE_VS_FCF = "P/E ratio vs free cash flow yield"
CHART_TITLE_VOLUME_VS_SPREAD = "Volume turnover vs bid-ask spread"
CHART_TITLE_RANGE_DISTRIBUTION = "52-week range position distribution"
CHART_TITLE_DIVIDEND_RANKING = "Top {} by grossed-up dividend yield"
CHART_TITLE_FRANKING_DISTRIBUTION = "Franking credit distribution"
CHART_TITLE_GROWTH_TEMPLATE = "Top {} stocks by {} growth (%)"
CHART_TITLE_TREND_TEMPLATE = "{} trends over time"

# Franking distribution labels
LABEL_FRANKED = "Franked"
LABEL_UNFRANKED = "Unfranked"

# ── Dataframe Column Config ─────────────────────────────────────────

# Tab 2: Valuation Matrix — source columns and display columns
VALUATION_SOURCE_COLS: list[str] = [
    "symbol",
    "market_cap",
    "cleaned_pe",
    "earnings_yield",
    "price_to_cash",
    "free_cash_flow_yield",
]

VALUATION_DISPLAY_RENAME: dict[str, str] = {
    "market_cap": "Market cap ($M)",
}

VALUATION_DISPLAY_COLS: list[str] = [
    "symbol",
    "Market cap ($M)",
    "cleaned_pe",
    "earnings_yield",
    "price_to_cash",
    "free_cash_flow_yield",
]

# Tab 3: Dividend Analysis — source columns and display columns
DIVIDEND_SOURCE_COLS: list[str] = [
    "symbol",
    "raw_dividend_yield",
    "franking_credit_multiplier",
    "grossed_up_yield",
    "dividend_payout_ratio",
    "dividend_currency_risk",
]

DIVIDEND_DISPLAY_RENAME: dict[str, str] = {
    "raw_yield_pct": "Raw yield (%)",
    "franking_credit_multiplier": "Franking multiplier",
    "grossed_up_pct": "Grossed-up yield (%)",
    "payout_pct": "Payout ratio (%)",
}

DIVIDEND_DISPLAY_COLS: list[str] = [
    "symbol",
    "raw_yield_pct",
    "franking_credit_multiplier",
    "grossed_up_pct",
    "payout_pct",
    "currency_risk",
]

# Currency risk mapping (Material Symbols replace emojis)
CURRENCY_RISK_MAP: dict[bool, str] = {
    True: f"{ICON_CURRENCY_RISK} FX Risk",
    False: f"{ICON_CURRENCY_AUD} AUD",
}

# Tab 4: Liquidity & Risk — source columns and display columns
LIQUIDITY_SOURCE_COLS: list[str] = [
    "symbol",
    "bid_ask_spread_pct",
    "range_position_52w",
    "volume_turnover_ratio",
    "intraday_volatility",
]

LIQUIDITY_DISPLAY_RENAME: dict[str, str] = {
    "spread_pct": "Bid-Ask spread (%)",
    "range_pos": "52W range position (%)",
    "turnover_pct": "Volume turnover (%)",
    "intraday_vol": "Intraday volatility (%)",
}

LIQUIDITY_DISPLAY_COLS: list[str] = [
    "symbol",
    "spread_pct",
    "range_pos",
    "turnover_pct",
    "intraday_vol",
]

# ── Messages ────────────────────────────────────────────────────────

MSG_DATA_LOAD_FAILED = "Failed to load data: {}"
MSG_NO_DATA_FOR_RANGE = "No data available for the selected date range. Try a wider date range."
MSG_API_CONNECT_FAILED = "Cannot connect to API: {}"
MSG_FEATURE_ENGINEERING_UNAVAILABLE = "Feature engineering unavailable: {}"
MSG_NO_GROWTH_DATA = "No growth data available"
MSG_NO_NUMERIC_COLUMNS = "No numeric columns available for growth calculation"
MSG_GROWTH_COMPUTE_ERROR = "Error computing top N growth: {}"
MSG_FEATURE_DATA_NOT_AVAILABLE = "Feature engineering data not available."
MSG_NO_STOCKS_MATCH_FILTERS = "No stocks match the current filters."
MSG_SELECT_STOCKS_FOR_TREND = "Select stocks from the sidebar to view trend analysis"
MSG_TREND_FETCH_FAILED = "Could not fetch history for: {}"
MSG_NO_TREND_DATA = "No trend data available for selected symbols"
MSG_TREND_COMPUTE_ERROR = "Error computing trend data: {}"

# Markdown descriptions displayed above charts/tables
DESC_DATA_LOADED = "**Data loaded:** {:,} records | **Symbols:** {} unique"
DESC_SNAPSHOT_DATE = "**Snapshot date:** {}"
DESC_VALUATION = "Company size and valuation multiples relative to share price."
DESC_DIVIDEND = "Tax-adjusted dividend yields with franking credit benefits."
DESC_LIQUIDITY = "Transaction costs, price positioning, and short-term volatility indicators."

# ── Theme Colors (read from .streamlit/config.toml) ─────────────────

def _load_theme() -> dict:
    """Load theme colors from .streamlit/config.toml at module load time.

    Returns a nested dict matching the TOML structure:
    {
        "theme": {"primaryColor": ..., "greenColor": ..., ...},
        "theme.sidebar": {"backgroundColor": ..., ...},
    }
    """
    toml_path = Path(__file__).parent / ".streamlit" / "config.toml"
    with open(toml_path, "rb") as f:
        config = tomllib.load(f)
    return config


_toml = _load_theme()
_theme = _toml.get("theme", {})
_theme_sidebar = _theme.get("sidebar", {})

# Base theme colors
THEME_PRIMARY_COLOR = _theme.get("primaryColor", "#60A5FA")
THEME_BACKGROUND_COLOR = _theme.get("backgroundColor", "#0F172A")
THEME_SECONDARY_BACKGROUND_COLOR = _theme.get("secondaryBackgroundColor", "#1E293B")
THEME_TEXT_COLOR = _theme.get("textColor", "#F1F5F9")
THEME_LINK_COLOR = _theme.get("linkColor", THEME_PRIMARY_COLOR)
THEME_BORDER_COLOR = _theme.get("borderColor", "#334155")
THEME_CODE_BACKGROUND_COLOR = _theme.get("codeBackgroundColor", "#1E293B")
THEME_CODE_TEXT_COLOR = _theme.get("codeTextColor", "#CBD5E1")

# Semantic colors for financial indicators
THEME_GREEN_COLOR = _theme.get("greenColor", "#34D399")
THEME_RED_COLOR = _theme.get("redColor", "#F87171")
THEME_YELLOW_COLOR = _theme.get("yellowColor", "#FBBF24")
THEME_ORANGE_COLOR = _theme.get("orangeColor", "#FB923C")
THEME_BLUE_COLOR = _theme.get("blueColor", THEME_PRIMARY_COLOR)
THEME_VIOLET_COLOR = _theme.get("violetColor", "#A78BFA")
THEME_GRAY_COLOR = _theme.get("grayColor", "#94A3B8")

# Chart categorical palette
THEME_CHART_CATEGORICAL_COLORS: list[str] = list(
    _theme.get("chartCategoricalColors", [
        "#60A5FA", "#34D399", "#A78BFA", "#F87171",
        "#FBBF24", "#38BDF8", "#94A3B8", "#FB923C",
    ])
)

# Chart sequential palette (blue gradient)
THEME_CHART_SEQUENTIAL_COLORS: list[str] = list(
    _theme.get("chartSequentialColors", [
        "#0C4A6E", "#075985", "#0369A1", "#0284C7",
        "#0EA5E9", "#38BDF8", "#7DD3FC", "#BAE6FD",
        "#E0F2FE", "#F0F9FF",
    ])
)

# Dataframe styling
THEME_DATAFRAME_BORDER_COLOR = _theme.get("dataframeBorderColor", "#334155")
THEME_DATAFRAME_HEADER_BACKGROUND_COLOR = _theme.get(
    "dataframeHeaderBackgroundColor", "#1E293B"
)

# Sidebar theme
THEME_SIDEBAR_BACKGROUND_COLOR = _theme_sidebar.get("backgroundColor", "#1E293B")
THEME_SIDEBAR_SECONDARY_BACKGROUND_COLOR = _theme_sidebar.get(
    "secondaryBackgroundColor", "#1E293B"
)
THEME_SIDEBAR_TEXT_COLOR = _theme_sidebar.get("textColor", "#F1F5F9")
THEME_SIDEBAR_BORDER_COLOR = _theme_sidebar.get("borderColor", "#334155")
THEME_SIDEBAR_PRIMARY_COLOR = _theme_sidebar.get("primaryColor", THEME_PRIMARY_COLOR)

# ── Data Processing Constants ───────────────────────────────────────

# Sentinel values for data cleaning
PE_SENTINEL = -99999.99
FCF_YIELD_SENTINEL = -1.00000010000001e-05

# Australian tax rate for franking credit calculations
AU_TAX_RATE = 0.30

# Unit conversion: multiply by this to convert $M to dollars
MARKET_CAP_MILLION_MULTIPLIER = 1e6

# Franking credit multiplier thresholds
# > 1.0 means franked dividends; == 1.0 means unfranked
FRANKING_CREDIT_FRANKED_THRESHOLD = 1.0

# Column detection candidates (in priority order)
COLUMN_CANDIDATES_DATE: list[str] = [
    "fetched_at",
    "date",
    "Date",
    "timestamp",
    "Timestamp",
]

COLUMN_CANDIDATES_PRICE: list[str] = [
    "priceClose",
    "price_close",
    "close",
    "Close",
    "last_price",
    "Last_Price",
    "lastPrice",
    "last",
    "price",
    "Price",
]

COLUMN_CANDIDATES_SYMBOL: list[str] = [
    "symbol",
    "Symbol",
    "company",
    "Company",
    "ticker",
    "Ticker",
    "company_id",
    "companyName",
]

# ── Sentence Case Exceptions ────────────────────────────────────────
# Labels that are inherently uppercase (acronyms/abbreviations)
# and should be excluded from sentence-case validation in tests.
# These match axis title text from Vega-Lite charts.
SENTENCE_CASE_EXCEPTIONS: frozenset[str] = frozenset(
    ["P/E", "FCF", "AUD", "USD"]
)

# ── Trend Chart Config ──────────────────────────────────────────────
# Mapping from growth factor column names to readable y-axis labels
TREND_FACTOR_LABELS: dict[str, str] = {
    "priceClose": "Close price",
    "priceOpen": "Open price",
    "priceHigh": "High price",
    "priceLow": "Low price",
    "volume": "Volume",
}

# ── API Client Config ───────────────────────────────────────────────

# API base URL (overridable via ASX_API_BASE_URL env var)
API_BASE_URL_DEFAULT = "http://localhost:30181"

# Timeout constants: (connect_timeout, read_timeout)
API_CONNECT_TIMEOUT = 10
API_READ_TIMEOUT_HEALTH = 60
API_READ_TIMEOUT_BULK = 120
API_READ_TIMEOUT_HISTORY = 120

# Retry configuration
API_MAX_RETRIES = 2
API_BASE_RETRY_DELAY = 3
