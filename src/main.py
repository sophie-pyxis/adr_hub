"""
AI Architecture Governance System - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import squads_router, artifacts_router, triggers_router, health_router
from src.database import create_db_and_tables

app = FastAPI(
    title="AI Architecture Governance API",
    description="REST API for managing Architecture Decision Records (ADRs) and Squads",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(squads_router)
app.include_router(artifacts_router)
app.include_router(triggers_router)
app.include_router(health_router)


@app.on_event("startup")
def on_startup():
    """Initialize database on application startup."""
    create_db_and_tables()


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "name": "AI Architecture Governance API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "squads": "/api/squads",
            "artifacts": "/api/artifacts",
            "triggers": "/api/triggers"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )