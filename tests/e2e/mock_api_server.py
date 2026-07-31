"""Mock HTTP server for the ASX data API.

Intercepts requests from the Streamlit app during E2E tests,
returning deterministic responses that match the real API format.

Endpoints:
  GET /health              - Returns available stock symbols
  GET /export/company      - Returns bulk CSV data (with optional date filters)
  GET /company/{symbol}/history - Returns historical data for a symbol

Dates are generated relative to today so the mock data always falls
within the app's default 90-day date range.
"""

import csv
import datetime
import io
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

MOCK_PORT = int(os.environ.get("E2E_MOCK_API_PORT", "19000"))

# Symbols returned by /health and used throughout mock data
MOCK_SYMBOLS = ["BHP", "CBA", "CSL", "WES", "WBC"]

# Generate dates relative to today so mock data always falls within
# the app's default 90-day date range.
_TODAY = datetime.date.today()
# fetched_at: 5 days ago (well within 90-day default range)
MOCK_FETCHED_AT = (_TODAY - datetime.timedelta(days=5)).isoformat()
# History dates: spread across the last ~200 days
MOCK_HISTORY_DATES = [
    (_TODAY - datetime.timedelta(days=200)).isoformat(),
    (_TODAY - datetime.timedelta(days=150)).isoformat(),
    (_TODAY - datetime.timedelta(days=100)).isoformat(),
    MOCK_FETCHED_AT,
]


# Bulk CSV stock data: each entry is (csv_prefix, income_statement_dict).
# The income statement dict is serialised with json.dumps() and converted to
# single-quoted Python literal format (required by ast.literal_eval in data_processor).
_CSV_STOCK_DATA = [
    (
        "BHP,BHP Group,42.50,42.55,42.45,52.00,35.00,42.60,42.30,15000000,7900000000,12.5,8.2,0.045,0.06,85.0,2.80,3.40,AUD",
        [{"revenue": 65000000000, "netIncome": 8000000000, "cashFlow": 12000000000, "period": "2024A"}],
    ),
    (
        "CBA,Commonwealth Bank,110.00,110.10,109.90,125.00,95.00,110.20,109.80,5000000,18700000000,15.0,10.5,0.035,0.07,90.0,7.70,7.33,AUD",
        [{"revenue": 19000000000, "netIncome": 9500000000, "cashFlow": 11000000000, "period": "2024A"}],
    ),
    (
        "CSL,CSL Limited,310.00,310.50,309.50,350.00,260.00,311.00,309.00,1200000,1500000000,35.0,25.0,0.025,0.015,0.0,4.68,4.80,USD",
        [{"revenue": 18000000000, "netIncome": 2200000000, "cashFlow": 3000000000, "period": "2024A"}],
    ),
    (
        "WES,Wesfarmers,58.00,58.10,57.90,65.00,48.00,58.20,57.80,3500000,1200000000,32.0,22.0,0.038,0.055,80.0,3.20,1.81,AUD",
        [{"revenue": 52000000000, "netIncome": 4200000000, "cashFlow": 6000000000, "period": "2024A"}],
    ),
    (
        "WBC,Westpac Banking,24.00,24.05,23.95,28.00,20.00,24.10,23.90,20000000,18500000000,10.0,7.0,0.040,0.065,85.0,1.56,2.40,AUD",
        [{"revenue": 18000000000, "netIncome": 5500000000, "cashFlow": 7000000000, "period": "2024A"}],
    ),
]


def _generate_bulk_csv() -> str:
    """Generate bulk CSV with dynamic dates.

    Income statement dicts are serialised with json.dumps() and converted
    to single-quoted Python literal format (required by ast.literal_eval
    in data_processor.parse_income_statement).
    """
    header = "symbol,company,priceClose,priceAsk,priceBid,priceFiftyTwoWeekHigh,priceFiftyTwoWeekLow,priceDayHigh,priceDayLow,volumeAverage,numOfShares,priceEarningsRatio,priceToCash,freeCashFlowYield,yieldAnnual,frankingPercent,dividend,earningsPerShare,dividendCurrency,incomeStatement,fPeriodEndDate,fetched_at"
    data_lines = []
    for prefix, stmt_dict in _CSV_STOCK_DATA:
        # json.dumps produces double-quoted JSON; replace with single quotes
        # for ast.literal_eval compatibility in the data processor
        stmt_str = json.dumps(stmt_dict).replace('"', "'")
        line = f'{prefix},"{stmt_str}",45838,{MOCK_FETCHED_AT}'
        data_lines.append(line)
    return header + "\n" + "\n".join(data_lines) + "\n"


# Historical data per symbol for /company/{symbol}/history
# Each entry: (fetched_at, priceClose)
def _generate_history() -> dict[str, list[tuple[str, float]]]:
    """Generate history data with dynamic dates."""
    d = MOCK_HISTORY_DATES
    return {
        "BHP": [
            (d[0], 40.00),
            (d[1], 41.50),
            (d[2], 43.00),
            (d[3], 42.50),
        ],
        "CBA": [
            (d[0], 105.00),
            (d[1], 108.00),
            (d[2], 112.00),
            (d[3], 110.00),
        ],
        "CSL": [
            (d[0], 290.00),
            (d[1], 300.00),
            (d[2], 315.00),
            (d[3], 310.00),
        ],
        "WES": [
            (d[0], 55.00),
            (d[1], 56.50),
            (d[2], 59.00),
            (d[3], 58.00),
        ],
        "WBC": [
            (d[0], 22.00),
            (d[1], 23.00),
            (d[2], 24.50),
            (d[3], 24.00),
        ],
    }


MOCK_HISTORY = _generate_history()


class MockAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler that returns mock ASX API responses."""

    def log_message(self, format, *args):
        """Suppress default request logging during tests."""
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/health":
            self._handle_health()
        elif path == "/export/company":
            self._handle_bulk_csv(params)
        elif path.startswith("/company/") and path.endswith("/history"):
            symbol = path.split("/")[2]
            self._handle_history(symbol, params)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())

    def _handle_health(self):
        response = {
            "data": {
                "status": "healthy",
                "refreshes": {sym: {"last_refresh": MOCK_FETCHED_AT} for sym in MOCK_SYMBOLS},
            }
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def _handle_bulk_csv(self, params):
        # Filter by date range if provided
        lines = _generate_bulk_csv().strip().split("\n")
        header = lines[0]
        data_lines = lines[1:]

        if "start_date" in params or "end_date" in params:
            start = params.get("start_date", [""])[0]
            end = params.get("end_date", [""])[0]
            filtered = []
            for line in data_lines:
                reader = csv.reader(io.StringIO(line))
                fields = next(reader)
                # fetched_at is the last column in the CSV
                date_val = fields[-1]
                if start and date_val < start:
                    continue
                if end and date_val > end:
                    continue
                filtered.append(line)
            data_lines = filtered

        csv_output = header + "\n" + "\n".join(data_lines) + "\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.end_headers()
        self.wfile.write(csv_output.encode())

    def _handle_history(self, symbol, params):
        if symbol not in MOCK_HISTORY:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Symbol {symbol} not found"}).encode())
            return

        records = MOCK_HISTORY[symbol]
        # Filter by date range if provided
        if "start_date" in params or "end_date" in params:
            start = params.get("start_date", [""])[0]
            end = params.get("end_date", [""])[0]
            records = [
                (d, p) for d, p in records
                if (not start or d >= start) and (not end or d <= end)
            ]

        response = {
            "data": [{"symbol": symbol, "priceClose": p, "fetched_at": d} for d, p in records]
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


def run_server(port=None):
    """Start and block on the mock API server."""
    port = port or MOCK_PORT
    server = HTTPServer(("127.0.0.1", port), MockAPIHandler)
    print(f"Mock API server listening on 127.0.0.1:{port}")
    server.serve_forever()
    return server


if __name__ == "__main__":
    run_server()
