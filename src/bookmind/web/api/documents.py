"""web.api.documents — API routes for document upload and previewing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile

from bookmind.ai.services import PDFExtractorService
from bookmind.application.books.commands.create_book import CreateBookCommandHandler
from bookmind.infrastructure.configuration.settings import Settings

router = APIRouter(prefix="/api", tags=["Documents"])


@router.post("/upload")
async def upload_pdf(file: UploadFile) -> dict:
    """PDF dosyasını yükler ve haritalandırır."""
    return await CreateBookCommandHandler.handle(file)


@router.post("/test-pdf-preview")
async def test_pdf_preview(file: UploadFile) -> dict:
    """Yüklenen PDF'in 1. Kademe gömülü Bookmark/TOC yapısını kontrol eder."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları yüklenebilir.")

    temp_path = Settings.PDFS_DIR / f"temp_preview_{file.filename}"
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
