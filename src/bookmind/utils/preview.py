"""PDF preview/test yardımcı işlevleri."""

from pathlib import Path
import pymupdf


def extract_preview_text(pdf_path: str | Path, max_pages: int = 5) -> list[dict[str, str | int]]:
    """PDF'in ilk `max_pages` sayfasını sayfa sayfa metin olarak çıkarır.

    Returns:
        [
            {"page_num": 1, "text": "..."},
            {"page_num": 2, "text": "..."},
        ]
    """
    doc = pymupdf.open(str(pdf_path))
    pages_to_read = min(max_pages, len(doc))

    results = []
    for i in range(pages_to_read):
        page = doc[i]
        text = page.get_text()
        results.append({
            "page_num": i + 1,
            "text": text if text.strip() else "[Bu sayfada okunabilir metin bulunamadı (Görsel veya boş sayfa olabilir)]"
        })

    doc.close()
    return results
