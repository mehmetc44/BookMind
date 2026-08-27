"""BookMind - FastAPI uygulaması."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from starlette.requests import Request

from bookmind.graph import process_pdf
from bookmind.models import BookInfo

load_dotenv()


class ChatMessage(BaseModel):
    """Chat isteği modeli."""

    book_id: str | None = None
    message: str
    history: list[dict[str, str]] = []

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # BookMind root
DATA_DIR = BASE_DIR / "data"
PDFS_DIR = DATA_DIR / "pdfs"
MAPS_DIR = DATA_DIR / "maps"

# Dizinleri oluştur
PDFS_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)

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
    """Kullanıcı mesajını DeepSeek'e gönder, yanıt döndür."""

    # Sistem promptunu oluştur
    if req.book_id:
        map_path = MAPS_DIR / f"{req.book_id}.json"
        if map_path.exists():
            data = json.loads(map_path.read_text(encoding="utf-8"))
            book_map = data.get("book_map", {})
            book_context = json.dumps(book_map, ensure_ascii=False, indent=2)
            system_prompt = (
                "Sen BookMind adlı bir kitap analiz asistanısın. "
                "Kullanıcının seçtiği kitabın yapısal haritası aşağıda verilmiştir. "
                "Bu haritayı kullanarak kitap hakkındaki soruları yanıtla. "
                "Türkçe yanıt ver.\n\n"
                f"KİTAP HARİTASI:\n```json\n{book_context}\n```"
            )
        else:
            system_prompt = (
                "Sen BookMind adlı bir kitap analiz asistanısın. "
                "Kitap ve okuma hakkındaki soruları Türkçe yanıtla."
            )
    else:
        system_prompt = (
            "Sen BookMind adlı bir kitap analiz asistanısın. "
            "Kitap ve okuma hakkındaki soruları Türkçe yanıtla."
        )

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url="https://api.deepseek.com",
        temperature=0.7,
        max_tokens=2000,
    )

    # Mesaj geçmişini oluştur
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for h in req.history[-10:]:  # Son 10 mesajı bağlam olarak al
        messages.append(h)
    messages.append({"role": "user", "content": req.message})

    try:
        response = llm.invoke(messages)
        return {"success": True, "reply": response.content}
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
