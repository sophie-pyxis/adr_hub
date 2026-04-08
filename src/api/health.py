"""
Health monitoring API router.

PHASE 6: Health endpoints
- Service health check
- Database health check
- Template directory health check
- Overall system status
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from ..services.health_service import HealthService
from ..services.artifact_service import ArtifactService
from ..database import get_session

router = APIRouter(prefix="/api/health", tags=["health"])


def get_artifact_service(session: Session = Depends(get_session)) -> ArtifactService:
    """Dependency injection for ArtifactService."""
    return ArtifactService(session)


def get_health_service(
    session: Session = Depends(get_session),
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> HealthService:
    """Dependency injection for HealthService."""
    return HealthService(session, artifact_service)


@router.get("/")
def get_health_status(
    health_service: HealthService = Depends(get_health_service),
) -> Dict[str, Any]:
    """
    Get overall system health status.

    Returns:
        Overall health status with component details
    """
    try:
        health_status = health_service.get_overall_health()

        # Return 503 if overall status is unhealthy
        if health_status.get("status") == "unhealthy":
            raise HTTPException(
                status_code=503,
                detail="System is unhealthy",
                headers={"Retry-After": "30"},
            )

        return health_status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking health: {str(e)}")


@router.get("/readiness")
def get_readiness() -> Dict[str, Any]:
    """
    Readiness probe for load balancers and orchestration.

    Returns:
        Simple readiness status
    """
    return {"status": "ready", "timestamp": "2024-01-01T00:00:00Z"}


@router.get("/liveness")
def get_liveness() -> Dict[str, Any]:
    """
    Liveness probe for Kubernetes/container orchestration.

    Returns:
        Simple liveness status
    """
    return {"status": "alive", "timestamp": "2024-01-01T00:00:00Z"}


@router.get("/metrics")
def get_detailed_metrics(
    health_service: HealthService = Depends(get_health_service),
) -> Dict[str, Any]:
    """
    Get detailed system metrics for monitoring.

    Returns:
        Detailed metrics including database, artifacts, and system metrics
    """
    try:
        metrics = health_service.get_detailed_metrics()
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")
