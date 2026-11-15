from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.llm import LLMStatusResponse, ollama_client

router = APIRouter()


class LLMSettingsUpdate(BaseModel):
    ollama_base_url: str = settings.OLLAMA_BASE_URL
    default_model: str = settings.OLLAMA_DEFAULT_MODEL


@router.get(
    "/llm", summary="Get LLM configuration and Ollama status", response_model=dict[str, Any]
)
async def get_llm_settings() -> dict[str, Any]:
    """Retrieve current LLM configuration and local Ollama model list."""
    status: LLMStatusResponse = await ollama_client.get_status()
    return {
        "provider": "ollama",
        "is_free_mode": True,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "default_model": settings.OLLAMA_DEFAULT_MODEL,
        "fallback_model": settings.OLLAMA_FALLBACK_MODEL,
        "has_cloud_fallback": bool(settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY),
        "daemon_status": status.model_dump(),
    }
