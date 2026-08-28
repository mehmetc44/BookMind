"""BookMind — FastAPI Ana Uygulama Giriş Noktası (Presentation Entrypoint)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from bookmind.api import api_v1_router
from bookmind.shared import Config

# Dizinleri oluştur
Config.PDFS_DIR.mkdir(parents=True, exist_ok=True)
Config.MAPS_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI uygulaması
app = FastAPI(
    title="BookMind",
    version="0.1.0",
    description="Kitap Haritalama ve Akıllı Asistan Sistemi",
)

# V1 API Router'ı bağla
app.include_router(api_v1_router)

# Static files & Jinja2 templates (BookMind.WebApp)
WEBAPP_DIR = Path(__file__).resolve().parent / "webapp"
STATIC_DIR = WEBAPP_DIR / "static"
TEMPLATE_DIR = WEBAPP_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# ---------- HTML Web Sayfaları ----------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Ana sohbet ve kitap haritalama arayüzü."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request) -> HTMLResponse:
    """PDF Bookmark & Köprü Tespit Laboratuvarı."""
    return templates.TemplateResponse(request, "test.html")


def main() -> None:
    """Uygulamayı Uvicorn ile başlatır."""
    import uvicorn

    uvicorn.run(
        "bookmind.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
