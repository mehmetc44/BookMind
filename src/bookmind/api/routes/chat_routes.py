"""BookMind.API.routes.chat_routes — Chat ve Kitap listeleme HTTP endpoint'leri."""

from __future__ import annotations

from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from bookmind.api.storage import MapRepository
from bookmind.ai.graphs import stream_chat_graph
from bookmind.shared import BookInfo, ChatMessage, ChatResponse, Config

router = APIRouter(prefix="/api", tags=["Chat & Books"])


@router.get("/books", response_model=list[BookInfo])
async def list_books() -> list[BookInfo]:
    """Yüklenen kitapları listele."""
    return MapRepository.list_books()


@router.get("/books/{book_id}/map")
async def get_book_map(book_id: str) -> dict:
    """Kitap haritasını getir."""
    map_data = MapRepository.get_book_map(book_id)
    if not map_data:
        raise HTTPException(status_code=404, detail="Kitap haritası bulunamadı.")
    return map_data


@router.delete("/books/{book_id}")
async def delete_book(book_id: str) -> dict:
    """Kitabı ve haritasını sil."""
    from pathlib import Path

    map_path = Config.MAPS_DIR / f"{book_id}.json"
    if not map_path.exists():
        raise HTTPException(status_code=404, detail="Kitap bulunamadı.")

    import json

    data = json.loads(map_path.read_text(encoding="utf-8"))
    pdf_path = Path(data.get("meta", {}).get("pdf_path", ""))

    if pdf_path.exists():
        pdf_path.unlink()
    map_path.unlink()

    return {"success": True, "message": "Kitap başarıyla silindi."}


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatMessage) -> ChatResponse:
    """Sohbet asistanına mesaj gönder (Sync yanıt)."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    from bookmind.ai.agents import get_chat_agent

    agent = get_chat_agent()
    try:
        reply = await agent.run(
            message=body.message,
            book_id=body.book_id,
            history=body.history,
        )
        return ChatResponse(success=True, reply=reply)
    except Exception as e:
        return ChatResponse(success=False, error=str(e))


@router.post("/chat/stream")
async def chat_stream(body: ChatMessage) -> StreamingResponse:
    """Sohbet asistanına mesaj gönder (Canlı Streaming yanıt)."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in stream_chat_graph(body.message):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")
