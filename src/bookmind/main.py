"""BookMind - FastAPI uygulaması."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from starlette.requests import Request

from bookmind.agents import get_chat_agent
from bookmind.core.config import Config, LLMProvider
from bookmind.core.schemas.book import BookInfo
from bookmind.core.schemas.chat import ChatMessage
from bookmind.graph import process_pdf
from bookmind.utils.preview import extract_preview_text

# Paths
PDFS_DIR = Config.PDFS_DIR
MAPS_DIR = Config.MAPS_DIR

# Dizinleri oluştur
Config.PDFS_DIR.mkdir(parents=True, exist_ok=True)
Config.MAPS_DIR.mkdir(parents=True, exist_ok=True)

# FastAPI app
app = FastAPI(title="BookMind", version="0.1.0")

# Static files & templates
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# ---------- Yardımcı fonksiyonlar ----------


def _get_book_list() -> list[BookInfo]:
    """data/maps dizinindeki tüm kitap haritalarını listeler."""
    books: list[BookInfo] = []
    for map_file in sorted(MAPS_DIR.glob("*.json")):
        try:
            data = json.loads(map_file.read_text(encoding="utf-8"))
            meta = data.get("meta", {})
            book_map = data.get("book_map", {})
            books.append(
                BookInfo(
                    id=meta.get("id", map_file.stem),
                    filename=meta.get("filename", ""),
                    title=book_map.get("book_title", "Bilinmiyor"),
                    author=book_map.get("author", "Bilinmiyor"),
                    total_pages=book_map.get("total_pages", 0),
                    chapter_count=len(book_map.get("chapters", [])),
                    created_at=meta.get("created_at", ""),
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return books


# ---------- Routes ----------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Ana sayfa."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request) -> HTMLResponse:
    """PDF Text Extraction Test Sayfası."""
    return templates.TemplateResponse(request, "test.html")


@app.post("/api/test-pdf-preview")
async def test_pdf_preview(file: UploadFile) -> dict:
    """Yüklenen PDF'in ilk 5 sayfasının çıkarılan metnini test için döndürür."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yüklenebilir.")

    # Gecici kaydet
    temp_path = PDFS_DIR / f"temp_preview_{file.filename}"
    content = await file.read()
    temp_path.write_bytes(content)

    try:
        pages_preview = extract_preview_text(temp_path, max_pages=5)
        return {
            "success": True,
            "filename": file.filename,
            "pages": pages_preview
        }
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/upload")
async def upload_pdf(file: UploadFile) -> dict:
    """PDF yükle ve haritalama başlat."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yüklenebilir.")

    # Benzersiz ID oluştur
    book_id = uuid.uuid4().hex[:12]
    safe_filename = f"{book_id}_{file.filename}"

    # PDF'i kaydet
    pdf_path = PDFS_DIR / safe_filename
    content = await file.read()
    pdf_path.write_bytes(content)

    # LangGraph pipeline ile haritalama
    result = await process_pdf(str(pdf_path))

    if not result.get("success"):
        # PDF'i sil, hata döndür
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Haritalama sırasında bilinmeyen bir hata oluştu."),
        )

    # Harita JSON'ını kaydet
    map_data = {
        "meta": {
            "id": book_id,
            "filename": file.filename,
            "pdf_path": str(pdf_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "book_map": result["book_map"],
    }

    map_path = MAPS_DIR / f"{book_id}.json"
    map_path.write_text(json.dumps(map_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "success": True,
        "book_id": book_id,
        "title": result["book_map"].get("book_title", "Bilinmiyor"),
        "message": "Kitap başarıyla yüklendi ve haritalandı.",
    }


@app.get("/api/books")
async def list_books() -> list[BookInfo]:
    """Yüklenen kitapları listele."""
    return _get_book_list()


@app.get("/api/books/{book_id}/map")
async def get_book_map(book_id: str) -> dict:
    """Kitap haritasını getir."""
    map_path = MAPS_DIR / f"{book_id}.json"
    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Kitap haritası bulunamadı.")

    data = json.loads(map_path.read_text(encoding="utf-8"))
    return data


@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str) -> dict:
    """Kitabı ve haritasını sil."""
    map_path = MAPS_DIR / f"{book_id}.json"
    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Kitap bulunamadı.")

    # Harita dosyasından PDF yolunu oku
    data = json.loads(map_path.read_text(encoding="utf-8"))
    pdf_path = Path(data.get("meta", {}).get("pdf_path", ""))

    # Dosyaları sil
    if pdf_path.exists():
        pdf_path.unlink()
    map_path.unlink()

    return {"success": True, "message": "Kitap başarıyla silindi."}


@app.post("/api/chat")
async def chat(req: ChatMessage) -> dict:
    """Kullanıcı mesajını ChatAgent (Singleton) ile yanıtlar."""
    book_map = None
    if req.book_id:
        map_path = MAPS_DIR / f"{req.book_id}.json"
        if map_path.exists():
            data = json.loads(map_path.read_text(encoding="utf-8"))
            book_map = data.get("book_map")

    try:
        chat_agent = get_chat_agent()
        reply = await chat_agent.ask(
            message=req.message,
            book_map=book_map,
            history=req.history,
        )
        return {"success": True, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model hatası: {e!s}") from e


def main() -> None:
    """Uygulamayı başlat."""
    import uvicorn

    uvicorn.run(
        "bookmind.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
