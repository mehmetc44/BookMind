"""PDF preview/test ve Bookmark (TOC) tespit işlevleri."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pymupdf


from bookmind.services import PDFExtractorService


def inspect_pdf_toc(pdf_path: str | Path) -> dict[str, Any]:
    """PDF dosyasının 1. Kademe gömülü Bookmark (TOC) yapısını denetler.

    PDFExtractorService.inspect_toc metoduna delege eder.
    """
    return PDFExtractorService.inspect_toc(pdf_path)


def extract_preview_text(pdf_path: str | Path, max_pages: int = 5) -> list[dict[str, str | int]]:
    """PDF'in ilk max_pages sayfasını metin olarak çıkarır."""
    doc = pymupdf.open(str(pdf_path))
    pages_to_read = min(max_pages, len(doc))

    results = []
    for i in range(pages_to_read):
        page = doc[i]
        text = page.get_text()
        results.append({
            "page_num": i + 1,
            "text": text if text.strip() else "[Bu sayfada okunabilir metin bulunamadı]",
        })

    doc.close()
    return results
