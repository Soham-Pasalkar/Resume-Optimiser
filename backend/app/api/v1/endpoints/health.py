from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.llm import LLMStatusResponse, ollama_client

router = APIRouter()


@router.get("", summary="General system health check")
async def health_check() -> dict[str, Any]:
    """Root health check returning service operational status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0-phase0",
    }


@router.get("/ollama", summary="Local Ollama daemon status check", response_model=LLMStatusResponse)
async def check_ollama_status() -> LLMStatusResponse:
    """Check connection to local Ollama instance and list loaded models."""
    return await ollama_client.get_status()


@router.get("/db", summary="Database connectivity check")
async def check_database_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Execute simple ping query on the database."""
    try:
        result = await db.execute(text("SELECT 1"))
        scalar = result.scalar()
        return {
            "status": "connected" if scalar == 1 else "unexpected_result",
            "database": "postgresql",
        }
    except Exception as exc:
        return {
            "status": "error",
            "detail": str(exc),
        }
