"""
Unified artifact API router.

PHASE 5: API Routes
- CRUD endpoints for all 7 artifact types
- Status update endpoints
- Search and filtering endpoints
- Integration with template and trigger services
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from ..database import get_session
from ..models.artifact import (
    ArtifactCreate,
    ArtifactRead,
    ArtifactStatusUpdate,
    ArtifactUpdate,
)
from ..services.artifact_service import ArtifactService
from ..services.trigger_service import TriggerService

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


def get_artifact_service(session: Session = Depends(get_session)) -> ArtifactService:
    """Dependency injection for ArtifactService."""
    return ArtifactService(session)


def get_trigger_service(
    session: Session = Depends(get_session),
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> TriggerService:
    """Dependency injection for TriggerService."""
    return TriggerService(session, artifact_service)


@router.get("/", response_model=List[ArtifactRead])
def get_artifacts(
    skip: int = 0,
    limit: int = 100,
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
    squad_id: Optional[int] = Query(None, description="Filter by squad ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    level: Optional[int] = Query(None, ge=1, le=5, description="Filter by level (1-5)"),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Get artifacts with optional filtering and pagination.

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (default: 100)
    - **artifact_type**: Filter by artifact type (adr, rfc, evidence, governance,
      implementation, visibility, uncommon)
    - **squad_id**: Filter by squad ID
    - **status**: Filter by status (proposed, accepted, rejected, superseded,
      discontinued)
    - **level**: Filter by level (1-5)
    """
    return artifact_service.list_artifacts(
        skip=skip,
        limit=limit,
        artifact_type=artifact_type,
        squad_id=squad_id,
        status=status,
        level=level,
    )


@router.post("/", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_artifact(
    artifact_data: ArtifactCreate,
    artifact_service: ArtifactService = Depends(get_artifact_service),
    trigger_service: TriggerService = Depends(get_trigger_service),
):
    """
    Create a new artifact.

    - **artifact_type**: Type of artifact (adr, rfc, evidence, governance,
      implementation, visibility, uncommon)
    - **artifact_number**: Artifact number (use "auto" for auto-generation)
    - **title**: Title of the artifact
    - **level**: Artifact level (1-5, required for certain types)
    - **status**: Artifact status (proposed, accepted, rejected, superseded, discontinued)
    - **content**: Artifact content in Markdown format
    - **squad_id**: ID of the owning squad (required)
    - **template_used**: Template used for this artifact (optional)
    - **rfc_status**: RFC status (required for ADRs with level >= 3)
    - **triggered_by_id**: ID of artifact that triggered this one (optional)
    - **trigger_reason**: Reason for trigger (optional)
    """
    try:
        # Create the artifact
        artifact_read = artifact_service.create_artifact(artifact_data)

        # Get the full artifact model for trigger processing
        artifact_model = artifact_service.get_artifact_model_by_id(artifact_read.id)
        if artifact_model:
            # Check and process any triggers for this artifact
            # This will auto-create any target artifacts based on trigger rules
            trigger_service.process_artifact_triggers(artifact_model)

        return artifact_read

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/search", response_model=List[ArtifactRead])
def search_artifacts(
    q: str = Query(..., description="Search query for title or content"),
    artifact_type: Optional[str] = Query(None, description="Filter by artifact type"),
    skip: int = 0,
    limit: int = 100,
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Search artifacts by title or content.

    - **q**: Search query (required)
    - **artifact_type**: Optional filter by artifact type
    """
    try:
        return artifact_service.search_artifacts(
            query=q, artifact_type=artifact_type, skip=skip, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/types")
def get_artifact_types():
    """
    Get list of available artifact types.

    Returns all 7 artifact types in the unified model.
    """
    artifact_types = [
        "adr",
        "rfc",
        "evidence",
        "governance",
        "implementation",
        "visibility",
        "uncommon",
    ]

    return {"types": artifact_types}


@router.get("/statuses")
def get_artifact_statuses():
    """
    Get list of available artifact statuses.

    Returns all valid artifact status values.
    """
    statuses = ["proposed", "accepted", "rejected", "superseded", "discontinued"]

    return {"statuses": statuses}


@router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact_by_id(
    artifact_id: int, artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Get artifact by ID.

    - **artifact_id**: ID of the artifact to retrieve
    """
    artifact = artifact_service.get_artifact_by_id(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID '{artifact_id}' not found",
        )
    return artifact


@router.put("/{artifact_id}", response_model=ArtifactRead)
def update_artifact(
    artifact_id: int,
    artifact_update: ArtifactUpdate,
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Update an artifact.

    - **artifact_id**: ID of the artifact to update
    - **title**: New title (optional)
    - **content**: New content (optional)
    - **level**: New level (optional)
    - **template_used**: New template used (optional)
    - **rfc_status**: New RFC status (optional)
    """
    try:
        artifact = artifact_service.update_artifact_by_id(artifact_id, artifact_update)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with ID '{artifact_id}' not found",
            )
        return artifact
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(
    artifact_id: int, artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Delete an artifact.

    - **artifact_id**: ID of the artifact to delete
    """
    success = artifact_service.delete_artifact_by_id(artifact_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID '{artifact_id}' not found",
        )


@router.patch("/{artifact_id}/status", response_model=ArtifactRead)
def update_artifact_status(
    artifact_id: int,
    status_update: ArtifactStatusUpdate,
    artifact_service: ArtifactService = Depends(get_artifact_service),
    trigger_service: TriggerService = Depends(get_trigger_service),
):
    """
    Update artifact status with validation.

    - **artifact_id**: ID of the artifact to update
    - **status**: New artifact status
    - **superseded_by**: Artifact number that supersedes this one
      (required for status=superseded)
    - **rejection_reason**: Reason for rejection (required for status=rejected)
    """
    try:
        # First get the current artifact model to check triggers
        artifact_model = artifact_service.get_artifact_model_by_id(artifact_id)
        if not artifact_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with ID '{artifact_id}' not found",
            )

        # Validate required triggers before status update
        trigger_service.validate_required_triggers(artifact_model)

        # Update the status
        updated_artifact_read = artifact_service.update_artifact_status_by_id(
            artifact_id, status_update
        )
        if not updated_artifact_read:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with ID '{artifact_id}' not found",
            )

        # Get the updated artifact model for trigger processing
        updated_artifact_model = artifact_service.get_artifact_model_by_id(artifact_id)
        if updated_artifact_model:
            # Check and process any triggers that might now be satisfied
            trigger_service.process_artifact_triggers(updated_artifact_model)

        return updated_artifact_read

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{artifact_id}/file")
def get_artifact_file(
    artifact_id: int, artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Get artifact file content.

    - **artifact_id**: ID of the artifact
    Returns the Markdown file content for the artifact.
    """
    content = artifact_service.get_artifact_file_content(artifact_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found for artifact with ID '{artifact_id}'",
        )

    return Response(content=content, media_type="text/markdown; charset=utf-8")
