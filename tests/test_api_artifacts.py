"""
Test API routes for unified artifact model.

PHASE 5: API Routes
- CRUD endpoints for all 7 artifact types
- Status update endpoints
- Search and filtering endpoints
- Integration with template and trigger services
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from src.models.artifact import (
    Artifact,
    ArtifactCreate,
    ArtifactStatusUpdate,
    ArtifactUpdate,
)
from src.models.squad import Squad
from src.models.trigger_rule import TriggerRule


def test_get_artifacts_empty(client, session):
    """Test getting artifacts when none exist."""
    response = client.get("/api/artifacts")
    assert response.status_code == 200
    assert response.json() == []


def test_create_artifact(client, session):
    """Test creating a new artifact."""
    # First create a squad
    squad_data = {
        "squad_code": "test-squad",
        "name": "Test Squad",
        "tech_lead": "Test Lead",
        "status": "active",
    }
    squad_response = client.post("/api/squads", json=squad_data)
    assert squad_response.status_code == 201
    squad_id = squad_response.json()["id"]

    # Create artifact
    artifact_data = {
        "artifact_type": "adr",
        "artifact_number": "auto",
        "title": "Test ADR",
        "level": 3,
        "status": "proposed",
        "content": "Test content for ADR",
        "squad_id": squad_id,
        "rfc_status": "RFC-2024-001 completed",
    }

    with patch("src.api.artifacts.ArtifactService") as MockArtifactService, patch(
        "src.api.artifacts.TriggerService"
    ) as MockTriggerService:

        mock_artifact_service = Mock()
        mock_trigger_service = Mock()

        mock_artifact = Artifact(
            id=1,
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR",
            level=3,
            status="proposed",
            content="Test content for ADR",
            squad_id=squad_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            file_path="architecture/adr/ADR-001-001.md",
            template_used="adr_template.md",
            rfc_status="RFC-2024-001 completed",
        )

        mock_artifact_service.create_artifact.return_value = mock_artifact
        mock_trigger_service.process_artifact_triggers.return_value = []

        MockArtifactService.return_value = mock_artifact_service
        MockTriggerService.return_value = mock_trigger_service

        response = client.post("/api/artifacts", json=artifact_data)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["artifact_type"] == "adr"
    assert data["artifact_number"] == "ADR-001-001"
    assert data["title"] == "Test ADR"


def test_create_artifact_invalid_type(client):
    """Test creating artifact with invalid type."""
    artifact_data = {
        "artifact_type": "invalid_type",
        "artifact_number": "auto",
        "title": "Test",
        "content": "Test content",
        "squad_id": 1,
    }

    response = client.post("/api/artifacts", json=artifact_data)
    assert response.status_code == 422  # Validation error


def test_get_artifact_by_id(client, session):
    """Test getting artifact by ID."""
    # Create a test artifact via service
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_artifact = Artifact(
            id=1,
            artifact_type="rfc",
            artifact_number="RFC-2024-001",
            title="Test RFC",
            status="proposed",
            content="Test RFC content",
            squad_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_service.get_artifact_by_id.return_value = mock_artifact
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["artifact_type"] == "rfc"
    assert data["artifact_number"] == "RFC-2024-001"


def test_get_artifact_not_found(client):
    """Test getting non-existent artifact."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_service.get_artifact_by_id.return_value = None
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_artifact(client):
    """Test updating an artifact."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        updated_artifact = Artifact(
            id=1,
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Updated Title",
            level=3,
            status="accepted",
            content="Updated content",
            squad_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            rfc_status="RFC-2024-001 completed",
        )
        mock_service.update_artifact_by_id.return_value = updated_artifact
        MockArtifactService.return_value = mock_service

        update_data = {
            "title": "Updated Title",
            "content": "Updated content",
            "status": "accepted",
        }

        response = client.put("/api/artifacts/1", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "accepted"


def test_update_artifact_not_found(client):
    """Test updating non-existent artifact."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_service.update_artifact_by_id.return_value = None
        MockArtifactService.return_value = mock_service

        update_data = {"title": "Updated Title"}
        response = client.put("/api/artifacts/999", json=update_data)

    assert response.status_code == 404


def test_delete_artifact(client):
    """Test deleting an artifact."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_service.delete_artifact_by_id.return_value = True
        MockArtifactService.return_value = mock_service

        response = client.delete("/api/artifacts/1")

    assert response.status_code == 204


def test_delete_artifact_not_found(client):
    """Test deleting non-existent artifact."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_service.delete_artifact_by_id.return_value = False
        MockArtifactService.return_value = mock_service

        response = client.delete("/api/artifacts/999")

    assert response.status_code == 404


def test_update_artifact_status(client):
    """Test updating artifact status."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService, patch(
        "src.api.artifacts.TriggerService"
    ) as MockTriggerService:

        mock_artifact_service = Mock()
        mock_trigger_service = Mock()

        updated_artifact = Artifact(
            id=1,
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR",
            level=3,
            status="accepted",
            content="Test content",
            squad_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            rfc_status="RFC-2024-001 completed",
        )

        # Mock the artifact service methods
        mock_artifact_service.get_artifact_by_id.return_value = updated_artifact
        mock_artifact_service.get_artifact_model_by_id.return_value = updated_artifact
        mock_artifact_service.update_artifact_status_by_id.return_value = (
            updated_artifact
        )

        # Mock the trigger service to do nothing (no validation needed for this test)
        mock_trigger_service.validate_required_triggers.return_value = None
        mock_trigger_service.process_artifact_triggers.return_value = []

        MockArtifactService.return_value = mock_artifact_service
        MockTriggerService.return_value = mock_trigger_service

        status_data = {"status": "accepted"}

        response = client.patch("/api/artifacts/1/status", json=status_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"


def test_update_artifact_status_superseded(client):
    """Test updating artifact status to superseded with superseded_by."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService, patch(
        "src.api.artifacts.TriggerService"
    ) as MockTriggerService:

        mock_artifact_service = Mock()
        mock_trigger_service = Mock()

        updated_artifact = Artifact(
            id=1,
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR",
            level=3,
            status="superseded",
            content="Test content",
            squad_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            rfc_status="RFC-2024-001 completed",
        )

        # Mock the artifact service methods
        mock_artifact_service.get_artifact_by_id.return_value = updated_artifact
        mock_artifact_service.get_artifact_model_by_id.return_value = updated_artifact
        mock_artifact_service.update_artifact_status_by_id.return_value = (
            updated_artifact
        )

        # Mock the trigger service to do nothing (no validation needed for this test)
        mock_trigger_service.validate_required_triggers.return_value = None
        mock_trigger_service.process_artifact_triggers.return_value = []

        MockArtifactService.return_value = mock_artifact_service
        MockTriggerService.return_value = mock_trigger_service

        status_data = {"status": "superseded", "superseded_by": "ADR-002-001"}

        response = client.patch("/api/artifacts/1/status", json=status_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "superseded"


def test_search_artifacts_by_type(client, session):
    """Test searching artifacts by type."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_artifacts = [
            Artifact(
                id=1,
                artifact_type="adr",
                artifact_number="ADR-001-001",
                title="Test ADR 1",
                level=3,
                status="proposed",
                content="Content 1",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                rfc_status="RFC-2024-001 completed",
            ),
            Artifact(
                id=2,
                artifact_type="adr",
                artifact_number="ADR-001-002",
                title="Test ADR 2",
                level=4,
                status="accepted",
                content="Content 2",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                rfc_status="RFC-2024-002 completed",
                tco_estimate="10000",
                lgpd_analysis="Low risk",
            ),
        ]
        mock_service.search_artifacts.return_value = mock_artifacts
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/search?q=test&artifact_type=adr")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["artifact_type"] == "adr" for item in data)


def test_search_artifacts_by_squad(client, session):
    """Test searching artifacts by squad."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_artifacts = [
            Artifact(
                id=1,
                artifact_type="adr",
                artifact_number="ADR-001-001",
                title="Test ADR",
                level=3,
                status="proposed",
                content="Content",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                rfc_status="RFC-2024-001 completed",
            )
        ]
        mock_service.search_artifacts.return_value = mock_artifacts
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/search?q=test&squad_id=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["squad_id"] == 1


def test_search_artifacts_by_status(client, session):
    """Test searching artifacts by status."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_artifacts = [
            Artifact(
                id=1,
                artifact_type="adr",
                artifact_number="ADR-001-001",
                title="Test ADR",
                level=3,
                status="accepted",
                content="Content",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                rfc_status="RFC-2024-001 completed",
            )
        ]
        mock_service.search_artifacts.return_value = mock_artifacts
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/search?q=test&status=accepted")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "accepted"


def test_search_artifacts_multiple_filters(client, session):
    """Test searching artifacts with multiple filters."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_artifacts = [
            Artifact(
                id=1,
                artifact_type="adr",
                artifact_number="ADR-001-001",
                title="Test ADR",
                level=4,
                status="accepted",
                content="Content",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                rfc_status="RFC-2024-001 completed",
                tco_estimate="15000",
                lgpd_analysis="Medium risk",
            )
        ]
        mock_service.search_artifacts.return_value = mock_artifacts
        MockArtifactService.return_value = mock_service

        response = client.get(
            "/api/artifacts/search?q=test&artifact_type=adr&status=accepted&squad_id=1"
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["artifact_type"] == "adr"
    assert data[0]["status"] == "accepted"
    assert data[0]["squad_id"] == 1


def test_get_artifacts_by_squad(client, session):
    """Test getting artifacts for a specific squad."""
    with patch("src.api.squads.ArtifactService") as MockArtifactService, patch(
        "src.api.squads.SquadService"
    ) as MockSquadService:

        mock_artifact_service = Mock()
        mock_squad_service = Mock()

        # Mock squad
        from src.models.squad import Squad

        mock_squad = Squad(
            id=1,
            squad_code="1",
            name="Test Squad",
            tech_lead="Test Lead",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        mock_squad_service.get_squad.return_value = mock_squad

        # Mock artifacts
        mock_artifacts = [
            Artifact(
                id=1,
                artifact_type="adr",
                artifact_number="ADR-001-001",
                title="Test ADR",
                level=3,
                status="proposed",
                content="Content",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                rfc_status="RFC-2024-001 completed",
            ),
            Artifact(
                id=2,
                artifact_type="rfc",
                artifact_number="RFC-2024-001",
                title="Test RFC",
                status="proposed",
                content="RFC content",
                squad_id=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        mock_artifact_service.get_artifacts_by_squad.return_value = mock_artifacts

        MockArtifactService.return_value = mock_artifact_service
        MockSquadService.return_value = mock_squad_service

        response = client.get("/api/squads/1/artifacts")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["squad_id"] == 1 for item in data)


def test_get_artifact_file(client):
    """Test getting artifact file content."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_service.get_artifact_file_content.return_value = (
            "# Test ADR\n\nTest content"
        )
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/1/file")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "# Test ADR" in response.text


def test_get_artifact_file_not_found(client):
    """Test getting file for artifact without file."""
    with patch("src.api.artifacts.ArtifactService") as MockArtifactService:
        mock_service = Mock()
        mock_service.get_artifact_file_content.return_value = None
        MockArtifactService.return_value = mock_service

        response = client.get("/api/artifacts/1/file")

    assert response.status_code == 404


def test_get_artifact_types(client):
    """Test getting list of available artifact types."""
    response = client.get("/api/artifacts/types")

    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert "adr" in data["types"]
    assert "rfc" in data["types"]
    assert "evidence" in data["types"]
    assert len(data["types"]) == 7  # All 7 artifact types


def test_get_artifact_statuses(client):
    """Test getting list of available artifact statuses."""
    response = client.get("/api/artifacts/statuses")

    assert response.status_code == 200
    data = response.json()
    assert "statuses" in data
    assert "proposed" in data["statuses"]
    assert "accepted" in data["statuses"]
    assert "rejected" in data["statuses"]
    assert "superseded" in data["statuses"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
