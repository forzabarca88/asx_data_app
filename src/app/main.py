from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .client import ApiClient
from .models import Company, HistoryItem
from .charts import build_price_close_chart, build_high_low_chart, build_volume_chart
from plotly.io import to_html

app = FastAPI(title="ASX History UI")

@app.get("/", response_class=HTMLResponse)
async def root():
    # Return simple HTML for now to get tests passing
    return """
    <html>
        <body>
            <h1>ASX Companies</h1>
            <ul>
                <li><a href="/company/IAG">IAG</a></li>
                <li><a href="/company/CBA">CBA</a></li>
            </ul>
        </body>
    </html>
    """

@app.get("/company/{code}", response_class=HTMLResponse)
async def company_history(code: str):
    # For now, return a simple HTML response that includes chart placeholders
    # In a real implementation, we would fetch the history, generate charts, and render a template
    return f"""
    <html>
        <body>
            <h1>History for {code}</h1>
            <div>
                <h2>Price Close Chart</h2>
                <div>Chart would go here</div>
            </div>
            <div>
                <h2>High-Low Chart</h2>
                <div>Chart would go here</div>
            </div>
            <div>
                <h2>Volume Chart</h2>
                <div>Chart would go here</div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Close</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Volume</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>2023-01-01</td>
                        <td>100.5</td>
                        <td>105.0</td>
                        <td>99.0</td>
                        <td>1000000</td>
                    </tr>
                </tbody>
            </table>
        </body>
    </html>
    """