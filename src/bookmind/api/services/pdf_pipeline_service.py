"""BookMind.API.services.pdf_pipeline_service — PDF Yükleme, Haritalama ve Kaydetme Servisi."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile

from bookmind.shared.config import Config

PDFS_DIR = Config.PDFS_DIR
MAPS_DIR = Config.MAPS_DIR


class PDFPipelineService:
    """PDF işleme ve kayıt pipeline servisi."""

    @classmethod
    async def process_and_save(cls, file: UploadFile) -> dict[str, Any]:
        """Yüklenen PDF dosyasını doğrular, kaydeder, LangGraph pipeline'ı ile haritalandırır ve saklar."""
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yüklenebilir.")

        # Benzersiz ID oluştur
        book_id = uuid.uuid4().hex[:12]
        safe_filename = f"{book_id}_{file.filename}"

        # PDF'i fiziki olarak kaydet
        pdf_path = PDFS_DIR / safe_filename
        content = await file.read()
        pdf_path.write_bytes(content)

        # LangGraph PDFProcessingGraph Orkestratörünü tetikle
        from bookmind.ai.graphs import PDFProcessingGraph

        orchestrator = PDFProcessingGraph()
        result = await orchestrator.run(str(pdf_path))

        if not result.get("success") or not result.get("book_map"):
            # Hata durumunda geçici PDF'i sil ve hata fırlat
            pdf_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "1. Kademe TOC haritası çıkarılamadı (2. Kademe düğümüne geçilecek)."),
            )

        # Üretilen Harita JSON'ını MapRepository ile kaydet
        map_data = {
            "meta": {
                "id": book_id,
                "filename": file.filename,
                "pdf_path": str(pdf_path),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "book_map": result["book_map"],
        }

        from bookmind.api.storage import MapRepository

        MapRepository.save_book_map(book_id, map_data)

        return {
            "success": True,
            "book_id": book_id,
            "title": result["book_map"].get("book_title", "Bilinmiyor"),
            "message": "Kitap başarıyla yüklendi ve haritalandı.",
        }
