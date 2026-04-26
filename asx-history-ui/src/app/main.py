from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import settings
from app.client import ApiClient
import jinja2


app = FastAPI(title="ASX History UI")
app.mount("/static", StaticFiles(directory="src/app/static"), name="static")

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader("src/app/templates"), autoescape=False)
templates = Jinja2Templates(env=jinja_env)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Home page with company list."""
    companies = await ApiClient().get_companies()
    return templates.TemplateResponse("index.html", {"request": request, "companies": companies})


@app.get("/company/{code}", response_class=HTMLResponse)
async def company_history(request: Request, code: str) -> HTMLResponse:
    """Company history page with charts."""
    api_client = ApiClient()
    try:
        history = await api_client.get_company_history(code)
    except Exception as e:
        from httpx import HTTPStatusError
        if isinstance(e, HTTPStatusError):
            history = []
        else:
            raise

    return templates.TemplateResponse("company_history.html", {"request": request, "code": code, "history": history})


@app.post("/select-company")
async def select_company(request: Request, code: str) -> HTMLResponse:
    """Redirect to company history page after selection."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url=f"/company/{code}")
