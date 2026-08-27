"""PDF işleme yardımcı fonksiyonları."""

from pathlib import Path

import pymupdf


def extract_full_text(pdf_path: str | Path, max_pages: int | None = None) -> str:
    """PDF'den tüm metni çıkarır.

    Args:
        pdf_path: PDF dosya yolu.
        max_pages: Maksimum okunacak sayfa sayısı. None ise tamamı okunur.

    Returns:
        Birleştirilmiş metin.
    """
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

    Önce PyMuPDF'in yerleşik TOC özelliğini dener.
    Bulamazsa ilk 15 sayfanın metnini döndürür.

    Args:
        pdf_path: PDF dosya yolu.

    Returns:
        İçindekiler metni veya ilk sayfaların metni.
    """
    doc = pymupdf.open(str(pdf_path))

    # PyMuPDF yerleşik TOC
    toc = doc.get_toc()
    if toc:
        toc_lines: list[str] = []
        for level, title, page_num in toc:
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}{title} ..... sayfa {page_num}")
        doc.close()
        return "İÇİNDEKİLER (PDF metadata):\n" + "\n".join(toc_lines)

    # Yerleşik TOC yoksa, ilk sayfaları gönder
    total_pages = len(doc)
    scan_pages = min(15, total_pages)
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
