import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_llm_settings_endpoint(async_client: AsyncClient):
    """Test /api/v1/settings/llm endpoint returns expected configuration."""
    response = await async_client.get("/api/v1/settings/llm")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "ollama"
    assert data["is_free_mode"] is True
    assert data["default_model"] == settings.OLLAMA_DEFAULT_MODEL
    assert "daemon_status" in data


def test_settings_defaults():
    """Verify core security and operational defaults in configuration."""
    assert settings.PROJECT_NAME == "CareerPilot"
    assert settings.OLLAMA_DEFAULT_MODEL in [
        "llama3.1:8b",
        "llama3.2:3b",
        "qwen2.5:7b",
        "mistral:7b",
    ]
    assert settings.API_V1_STR == "/api/v1"
