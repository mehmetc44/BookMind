"""application.books.commands.create_book — Command handler to upload, map and persist a book."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import HTTPException, UploadFile

from bookmind.infrastructure.configuration.settings import Settings
from bookmind.infrastructure.services import PDFFileService
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

        book_map = result.get("book_map")
        layout_elements = result.get("layout_elements")

        if not book_map and layout_elements:
            # Gözlemci motorunun çıkardığı fiziki etiketleri UI haritasına çevir
            chapters = []
            for idx, el in enumerate(layout_elements):
                el_type = str(el["type"]).upper()
                raw_content = str(el["content"])
                snippet = raw_content[:150] + ("..." if len(raw_content) > 150 else "")
                chapters.append({
                    "id": f"element_{idx+1}",
                    "title": f"[{el_type}] {snippet}",
                    "page_start": el["page"],
                    "page_end": el["page"],
                    "summary": f"Fiziki Tip: {el['type']} | Font Boyutu: {el.get('font_size')}pt | Koyu: {el.get('is_bold')}",
                    "topics": [el["type"]],
                    "keywords": [f"Sayfa {el['page']}"],
                    "children": []
                })

            total_pages = max([e["page"] for e in layout_elements] or [1])
            book_map = {
                "book_title": f"{file.filename} (Ham Layout Etiketli)",
                "author": "Gözlemci Motoru (LayoutParserEngine)",
                "total_pages": total_pages,
                "chapters": chapters
            }

        if not result.get("success") or not book_map:
            pdf_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "PDF çözümlenemedi veya etiket çıkarılamadı."),
            )

        # JSON dosyasını PDFFileService ile kaydet
        map_data = {
            "meta": {
                "id": book_id,
                "filename": file.filename,
                "pdf_path": str(pdf_path),
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "book_map": book_map,
            "raw_layout_elements": layout_elements,
        }

        PDFFileService.save_book_map(book_id, map_data)

        return {
            "success": True,
            "book_id": book_id,
            "title": book_map.get("book_title", "Bilinmiyor"),
            "message": "Kitap başarıyla yüklendi ve haritalandı.",
        }
