"""application.books.queries.get_book — Query handler to retrieve a specific book map by ID."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException

from bookmind.infrastructure.services import PDFFileService


class GetBookQueryHandler:
    """Belirli bir kitabın haritasını getiren sorgu işleyici."""

    @classmethod
    def handle(cls, book_id: str) -> dict[str, Any]:
        """book_id'ye ait kitap haritası verisini döndürür."""
        map_data = PDFFileService.get_book_map(book_id)
        if not map_data:
            raise HTTPException(status_code=404, detail="Kitap haritası bulunamadı.")
        return map_data
