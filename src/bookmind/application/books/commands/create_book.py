"""application.books.commands.create_book — Command handler to upload, map and persist a book."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException, UploadFile

from bookmind.infrastructure.configuration.settings import Settings
from bookmind.infrastructure.database.repositories.map_repository import MapRepository
from bookmind.workflows.ingestion.graph import PDFProcessingGraph


class CreateBookCommandHandler:
    """PDF belgesini işleyen, haritalayan ve kaydeden komut işleyici."""

    @classmethod
    async def handle(cls, file: UploadFile) -> dict[str, Any]:
        """PDF dosyasını doğrular, LangGraph akışını tetikler ve haritayı saklar."""
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yüklenebilir.")

        book_id = uuid.uuid4().hex[:12]
        safe_filename = f"{book_id}_{file.filename}"

        # PDF'i diske yaz
        pdf_path = Settings.PDFS_DIR / safe_filename
        content = await file.read()
        pdf_path.write_bytes(content)

        # Ingestion workflow tetikle
        orchestrator = PDFProcessingGraph()
        result = await orchestrator.run(str(pdf_path))

        if not result.get("success") or not result.get("book_map"):
            # Hata durumunda yüklenen geçici PDF'i sil
            pdf_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "1. Kademe TOC haritası çıkarılamadı."),
            )

        # JSON dosyasını MapRepository ile kaydet
        map_data = {
            "meta": {
                "id": book_id,
                "filename": file.filename,
                "pdf_path": str(pdf_path),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "book_map": result["book_map"],
        }

        MapRepository.save_book_map(book_id, map_data)

        return {
            "success": True,
            "book_id": book_id,
            "title": result["book_map"].get("book_title", "Bilinmiyor"),
            "message": "Kitap başarıyla yüklendi ve haritalandı.",
        }
