"""web.api package — FastAPI route initialization."""

from fastapi import APIRouter

from bookmind.web.api.books import router as books_router
from bookmind.web.api.documents import router as documents_router
from bookmind.web.api.chat import router as chat_router

api_v1_router = APIRouter()
api_v1_router.include_router(books_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(chat_router)

__all__ = ["api_v1_router"]
