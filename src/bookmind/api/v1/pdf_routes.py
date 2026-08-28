"""api.v1.pdf_routes — PDF yükleme ve önizleme HTTP endpoint'leri."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from bookmind.services import PDFExtractorService, PDFPipelineService

router = APIRouter(prefix="/api", tags=["PDF"])


@router.post("/upload")
async def upload_pdf(file: UploadFile) -> dict:
    """PDF yükle ve haritalama pipeline'ını çalıştır (PDFPipelineService)."""
    return await PDFPipelineService.process_and_save(file)


@router.post("/test-pdf-preview")
async def test_pdf_preview(file: UploadFile) -> dict:
    """Yüklenen PDF'in 1. Kademe gömülü Bookmark/TOC kontrolünü yapar ve sonucunu döndürür."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yüklenebilir.")

    from bookmind.config import Config

    temp_path = Config.PDFS_DIR / f"temp_preview_{file.filename}"
    content = await file.read()
    temp_path.write_bytes(content)

    try:
        inspection = PDFExtractorService.inspect_toc(temp_path)
        return {
            "success": True,
            "filename": file.filename,
            **inspection,
        }
    finally:
        if temp_path.exists():
            temp_path.unlink()
