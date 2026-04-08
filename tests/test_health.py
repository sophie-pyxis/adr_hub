"""
Test health endpoints and service.

PHASE 6: Health endpoints
- Service health check
- Database health check
- Template directory health check
- Overall system status
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.services.health_service import HealthService, HealthStatus


def test_health_service_initialization():
    """Test health service initialization."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = HealthService(mock_session, mock_artifact_service)

    assert service.session == mock_session
    assert service.artifact_service == mock_artifact_service


def test_check_database_health_success():
    """Test database health check when database is healthy."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    # Mock successful database query
    mock_session.execute.return_value = Mock(scalar=Mock(return_value=1))

    service = HealthService(mock_session, mock_artifact_service)

    result = service.check_database_health()

    assert result["status"] == "healthy"
    assert "response_time_ms" in result
    assert result["response_time_ms"] > 0


def test_check_database_health_failure():
    """Test database health check when database query fails."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    # Mock database query failure
    mock_session.execute.side_effect = Exception("Database connection failed")

    service = HealthService(mock_session, mock_artifact_service)

    result = service.check_database_health()

    assert result["status"] == "unhealthy"
    assert "error" in result
    assert "Database connection failed" in result["error"]


def test_check_template_directory_exists():
    """Test template directory health check when directory exists."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = HealthService(mock_session, mock_artifact_service)

    with patch("os.path.exists", return_value=True):
        result = service.check_template_directory()

    assert result["status"] == "healthy"
    assert result["directory_exists"] is True


def test_check_template_directory_missing():
    """Test template directory health check when directory doesn't exist."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = HealthService(mock_session, mock_artifact_service)

    with patch("os.path.exists", return_value=False):
        result = service.check_template_directory()

    assert result["status"] == "unhealthy"
    assert result["directory_exists"] is False
    assert "warning" in result


def test_check_artifact_counts():
    """Test artifact count health check."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    # Mock artifact counts
    mock_artifact_service.get_artifact_counts.return_value = {
        "total": 10,
        "by_type": {"adr": 5, "rfc": 3, "evidence": 2},
        "by_status": {"proposed": 3, "accepted": 7},
    }

    service = HealthService(mock_session, mock_artifact_service)

    result = service.check_artifact_counts()

    assert result["status"] == "healthy"
    assert result["total_count"] == 10
    assert "adr" in result["by_type"]
    assert "proposed" in result["by_status"]


def test_check_artifact_counts_empty():
    """Test artifact count health check when no artifacts exist."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    # Mock empty artifact counts
    mock_artifact_service.get_artifact_counts.return_value = {
        "total": 0,
        "by_type": {},
        "by_status": {},
    }

    service = HealthService(mock_session, mock_artifact_service)

    result = service.check_artifact_counts()

    assert result["status"] == "healthy"  # Empty is still healthy
    assert result["total_count"] == 0
    assert result["by_type"] == {}


def test_check_artifact_counts_error():
    """Test artifact count health check when service fails."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    # Mock service failure
    mock_artifact_service.get_artifact_counts.side_effect = Exception("Service error")

    service = HealthService(mock_session, mock_artifact_service)

    result = service.check_artifact_counts()

    assert result["status"] == "unhealthy"
    assert "error" in result
    assert "Service error" in result["error"]


def test_get_overall_health():
    """Test overall health check aggregation."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = HealthService(mock_session, mock_artifact_service)

    # Mock individual health checks
    with patch.object(
        service,
        "check_database_health",
        return_value={"status": "healthy", "response_time_ms": 10},
    ):
        with patch.object(
            service,
            "check_template_directory",
            return_value={"status": "healthy", "directory_exists": True},
        ):
            with patch.object(
                service,
                "check_artifact_counts",
                return_value={"status": "healthy", "total_count": 5},
            ):

                result = service.get_overall_health()

    assert result["status"] == "healthy"
    assert len(result["components"]) == 3
    assert all(comp["status"] == "healthy" for comp in result["components"])
    assert "timestamp" in result


def test_get_overall_health_with_failure():
    """Test overall health check when one component fails."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = HealthService(mock_session, mock_artifact_service)

    # Mock mixed health checks
    with patch.object(
        service,
        "check_database_health",
        return_value={"status": "healthy", "response_time_ms": 10},
    ):
        with patch.object(
            service,
            "check_template_directory",
            return_value={
                "status": "unhealthy",
                "directory_exists": False,
                "warning": "Directory missing",
            },
        ):
            with patch.object(
                service,
                "check_artifact_counts",
                return_value={"status": "healthy", "total_count": 5},
            ):

                result = service.get_overall_health()

    assert result["status"] == "unhealthy"  # Overall status should be unhealthy
    assert len(result["components"]) == 3
    assert result["components"][1]["status"] == "unhealthy"


def test_health_endpoint(client):
    """Test health API endpoint."""
    # Mock the health service
    with patch("src.api.health.get_health_service") as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.get_overall_health.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": [
                {"name": "database", "status": "healthy"},
                {"name": "templates", "status": "healthy"},
                {"name": "artifacts", "status": "healthy"},
            ],
        }

        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert len(data["components"]) == 3


def test_health_endpoint_unhealthy(client):
    """Test health API endpoint when system is unhealthy."""
    from unittest.mock import Mock

    from src.api.health import get_health_service

    # Create a mock health service
    mock_service = Mock()
    mock_service.get_overall_health.return_value = {
        "status": "unhealthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "components": [
            {"name": "database", "status": "healthy"},
            {"name": "templates", "status": "unhealthy", "error": "Directory missing"},
            {"name": "artifacts", "status": "healthy"},
        ],
    }

    # Override the dependency
    from src.main import app

    app.dependency_overrides[get_health_service] = lambda: mock_service

    try:
        response = client.get("/api/health")
        assert response.status_code == 503  # Service Unavailable
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "System is unhealthy"
    finally:
        # Clean up
        app.dependency_overrides.clear()


def test_health_endpoint_internal_error(client):
    """Test health API endpoint when service raises exception."""
    from unittest.mock import Mock

    from src.api.health import get_health_service

    # Create a mock health service that raises an exception
    mock_service = Mock()
    mock_service.get_overall_health.side_effect = Exception("Internal error")

    # Override the dependency
    from src.main import app

    app.dependency_overrides[get_health_service] = lambda: mock_service

    try:
        response = client.get("/api/health")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error checking health" in data["detail"]
    finally:
        # Clean up
        app.dependency_overrides.clear()


def test_health_readiness_endpoint(client):
    """Test health readiness endpoint."""
    response = client.get("/api/health/readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_health_liveness_endpoint(client):
    """Test health liveness endpoint."""
    response = client.get("/api/health/liveness")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_health_metrics_endpoint(client):
    """Test health metrics endpoint."""
    # Mock the health service
    with patch("src.api.health.get_health_service") as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_service.get_detailed_metrics.return_value = {
            "database": {"queries_per_minute": 100, "connection_pool": 10},
            "artifacts": {"total": 50, "created_today": 5},
            "system": {"memory_usage_mb": 128, "cpu_percent": 15.5},
        }

        response = client.get("/api/health/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "artifacts" in data
    assert "system" in data


def test_health_status_enum():
    """Test HealthStatus enum values."""
    assert HealthStatus.HEALTHY == "healthy"
    assert HealthStatus.UNHEALTHY == "unhealthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
