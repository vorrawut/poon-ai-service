"""API routes for version 1."""

from fastapi import APIRouter

from .ai_learning import router as ai_learning_router
from .docs import router as docs_router
from .health import router as health_router
from .spending import router as spending_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(spending_router, prefix="/spending", tags=["Spending"])
api_router.include_router(ai_learning_router, prefix="/ai", tags=["AI Learning"])
api_router.include_router(docs_router, prefix="/docs", tags=["Documentation"])

__all__ = ["api_router"]
