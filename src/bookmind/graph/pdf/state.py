"""PDF haritalama pipeline'ının durumu (State)."""

from __future__ import annotations

from typing import Any, TypedDict


class PDFGraphState(TypedDict):
    """PDF haritalama pipeline'ının durumu.

    Attributes:
        pdf_path:    İşlenecek PDF dosyasının tam yolu.
        toc_text:    extract_toc node'unun çıkardığı içindekiler metni.
        total_pages: PDF'in toplam sayfa sayısı.
        book_map:    map_chapters node'unun ürettiği JSON harita (dict).
        error:       Herhangi bir node'da oluşan hata mesajı.
    """

    pdf_path: str
    toc_text: str
    total_pages: int
    book_map: dict[str, Any] | None
    error: str | None
