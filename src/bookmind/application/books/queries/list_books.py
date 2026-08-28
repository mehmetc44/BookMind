"""application.books.queries.list_books — Query handler to retrieve all mapped books."""

from __future__ import annotations

from bookmind.domain.books.entities import BookInfo
from bookmind.infrastructure.database.repositories.map_repository import MapRepository


class ListBooksQueryHandler:
    """Yüklenen tüm kitap listesini çeken sorgu işleyici."""

    @classmethod
    def handle(cls) -> list[BookInfo]:
        """Sistemdeki tüm kayıtlı kitapları listeler."""
        return MapRepository.list_books()
