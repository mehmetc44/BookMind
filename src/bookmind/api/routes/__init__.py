"""BookMind.API.routes package."""

from fastapi import APIRouter

from bookmind.api.routes.chat_routes import router as chat_router
from bookmind.api.routes.pdf_routes import router as pdf_router

api_v1_router = APIRouter()
api_v1_router.include_router(pdf_router)
api_v1_router.include_router(chat_router)

__all__ = ["api_v1_router"]
