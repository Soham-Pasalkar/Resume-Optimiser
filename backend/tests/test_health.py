import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test root endpoint returns service metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "CareerPilot"
    assert data["status"] == "operational"
    assert "/docs" in data["docs_url"]


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Test /api/v1/health returns healthy status."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "CareerPilot"


@pytest.mark.asyncio
async def test_ollama_health_endpoint_structure(async_client: AsyncClient):
    """Test /api/v1/health/ollama returns valid structured response even when offline."""
    response = await async_client.get("/api/v1/health/ollama")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "ollama"
    assert "is_available" in data
    assert "active_model" in data
    assert "available_models" in data
