from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, Undefined

from .client import get_api_client
from .config import settings
from .models import Company, HistoryItem
from .views import get_company_history, get_companies


app = FastAPI(title="ASX History UI")

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=True,
    auto_reload=True,
    undefined=Undefined,
)

templates = env.get_template("base.html")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    api_client = get_api_client()
    companies = await api_client.get_companies()
    return templates.render("index.html", companies=companies)


@app.get("/company/{code}", response_class=HTMLResponse)
async def company_history(code: str, request: Request):
    api_client = get_api_client()
    try:
        history = await get_company_history(code)
    except Exception as e:
        return templates.render(
            "error.html",
            code=code,
            error=str(e),
        )

    chart_html = ""
    if history:
        from .charts import (
            build_high_low_chart,
            build_price_close_chart,
            build_volume_chart,
        )

        price_close_fig = build_price_close_chart(history)
        chart_html = price_close_fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
        )

        high_low_fig = build_high_low_chart(history)
        chart_html += high_low_fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
        )

        volume_fig = build_volume_chart(history)
        chart_html += volume_fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
        )

    return templates.render(
        "company_history.html",
        code=code,
        history=history,
        chart_html=chart_html,
    )


@app.post("/select-company")
async def select_company(request: Request):
    api_client = get_api_client()
    companies = await get_companies()
    codes = [company.code for company in companies]

    form = request.form
    code = form.get("code")
    if code:
        return redirect(f"/company/{code}")
    return redirect("/")
