from typing import Any

import httpx
from pydantic import BaseModel

from app.core.config import settings


class OllamaModelInfo(BaseModel):
    name: str
    size: int | None = None
    digest: str | None = None
    modified_at: str | None = None


class LLMStatusResponse(BaseModel):
    provider: str
    is_available: bool
    base_url: str
    active_model: str
    available_models: list[str] = []
    error: str | None = None


class LocalOllamaClient:
    """Client for communicating with the local Ollama daemon at zero cost."""

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OLLAMA_DEFAULT_MODEL
        self.timeout = timeout

    async def get_status(self) -> LLMStatusResponse:
        """Ping Ollama and return daemon status and list of installed models."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Check if configured model or fallback is present
                    active = self.default_model
                    if active not in models and models:
                        active = models[0]  # Fallback to first available model

                    return LLMStatusResponse(
                        provider="ollama",
                        is_available=True,
                        base_url=self.base_url,
                        active_model=active,
                        available_models=models,
                        error=None,
                    )
                else:
                    return LLMStatusResponse(
                        provider="ollama",
                        is_available=False,
                        base_url=self.base_url,
                        active_model=self.default_model,
                        error=f"Ollama returned HTTP {response.status_code}",
                    )
        except Exception as exc:
            return LLMStatusResponse(
                provider="ollama",
                is_available=False,
                base_url=self.base_url,
                active_model=self.default_model,
                error=f"Cannot connect to Ollama daemon at {self.base_url}: {str(exc)}",
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        format_json: bool = False,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Generate text or structured JSON from local Ollama model."""
        target_model = model or self.default_model
        payload: dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        url = f"{self.base_url}/api/generate"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def get_embedding(
        self,
        text: str,
        model: str | None = None,
    ) -> list[float] | None:
        """Fetch dense vector embedding from local Ollama model."""
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": text,
        }
        url = f"{self.base_url}/api/embeddings"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")
        except Exception:
            return None
        return None


# Global client instance
ollama_client = LocalOllamaClient()
