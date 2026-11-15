from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle handler."""
    # Startup: Print configuration summary
    print(f"🚀 Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode")
    print(
        f"🤖 Default Local AI Engine: Ollama at {settings.OLLAMA_BASE_URL} ({settings.OLLAMA_DEFAULT_MODEL})"
    )
    print("💰 Operational Cost: 100% Free Local Execution")

    # Ensure database schema tables are initialized
    import app.models  # noqa: F401
    from app.core.database import Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # Shutdown
    print(f"🛑 Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CareerPilot — AI-Powered Career Intelligence & Application Optimization Platform",
    version="1.0.0-phase0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global standardized error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
                "details": [{"error": str(exc)}] if settings.DEBUG else [],
            }
        },
    )


# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root entry point with service metadata and documentation links."""
    return {
        "platform": settings.PROJECT_NAME,
        "tagline": "Navigate your career. Engineer your future.",
        "version": "1.0.0-phase0",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health",
        "status": "operational",
    }
