# ASX History UI

Modern Python web front-end for `company/<id>/history`

## Features

- View available ASX companies
- View company history data
- Interactive charts using Plotly
- Server-side rendering with Jinja2

## Setup

```bash
uv venv
uv pip install -e .
uv run pytest
```

## Running the app

```bash
uv run uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

Access at `http://localhost:8000`
