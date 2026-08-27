"""PDF işleme yardımcı araçları."""

from pathlib import Path
import pymupdf
from bookmind.core.config import Config


def extract_full_text(pdf_path: str | Path, max_pages: int | None = None) -> str:
    """PDF'den tüm metni çıkarır."""
    doc = pymupdf.open(str(pdf_path))
    pages_to_read = max_pages if max_pages else len(doc)
    pages_to_read = min(pages_to_read, len(doc))

    text_parts: list[str] = []
    for i in range(pages_to_read):
        page = doc[i]
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(f"--- Sayfa {i + 1} ---\n{page_text}")

    doc.close()
    return "\n\n".join(text_parts)


def extract_toc_text(pdf_path: str | Path) -> str:
    """PDF'den içindekiler bölümünü çıkarmaya çalışır.

    Önce PyMuPDF yerleşik TOC özelliğini dener.
    Bulamazsa Config.TOC_SCAN_PAGES kadar ilk sayfanın metnini döndürür.
    """
    doc = pymupdf.open(str(pdf_path))

    toc = doc.get_toc()
    if toc:
        toc_lines: list[str] = []
        for level, title, page_num in toc:
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}{title} ..... sayfa {page_num}")
        doc.close()
        return "İÇİNDEKİLER (PDF metadata):\n" + "\n".join(toc_lines)

    total_pages = len(doc)
    scan_pages = min(Config.TOC_SCAN_PAGES, total_pages)
    text_parts: list[str] = []
    for i in range(scan_pages):
        page = doc[i]
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(f"--- Sayfa {i + 1} ---\n{page_text}")

    doc.close()

    return (
        f"İÇİNDEKİLER BULUNAMADI. İlk {scan_pages} sayfanın metni:\n"
        + "\n\n".join(text_parts)
    )


def get_page_count(pdf_path: str | Path) -> int:
    """PDF'deki toplam sayfa sayısını döndürür."""
    doc = pymupdf.open(str(pdf_path))
    count = len(doc)
    doc.close()
    return count
