"""API routes for version 1."""

from fastapi import APIRouter

from .health import router as health_router
from .spending import router as spending_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(spending_router, prefix="/spending", tags=["Spending"])

__all__ = ["api_router"]
