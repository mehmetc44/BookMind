"""web.api.books — API routes for listing, fetching, and deleting books."""

from __future__ import annotations

from fastapi import APIRouter

from bookmind.domain.books.entities import BookInfo
from bookmind.application.books.queries.list_books import ListBooksQueryHandler
from bookmind.application.books.queries.get_book import GetBookQueryHandler
from bookmind.application.books.commands.delete_book import DeleteBookCommandHandler

router = APIRouter(prefix="/api", tags=["Books"])


@router.get("/books", response_model=list[BookInfo])
async def list_books() -> list[BookInfo]:
    """Sistemdeki tüm kayıtlı kitapları listeler."""
    return ListBooksQueryHandler.handle()


@router.get("/books/{book_id}/map")
async def get_book_map(book_id: str) -> dict:
    """Belirli bir kitabın harita detaylarını getirir."""
    return GetBookQueryHandler.handle(book_id)


@router.delete("/books/{book_id}")
async def delete_book(book_id: str) -> dict:
    """Belirli bir kitabı ve haritasını siler."""
    return DeleteBookCommandHandler.handle(book_id)
