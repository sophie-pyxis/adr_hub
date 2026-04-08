"""
Squads API router.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session

from ..models.squad import SquadCreate, SquadUpdate, SquadRead
from ..models.artifact import ArtifactRead
from ..services.squad_service import SquadService
from ..services.artifact_service import ArtifactService
from ..database import get_session

router = APIRouter(prefix="/api/squads", tags=["squads"])


def get_squad_service(session: Session = Depends(get_session)) -> SquadService:
    """Dependency injection for SquadService."""
    return SquadService(session)


def get_artifact_service(session: Session = Depends(get_session)) -> ArtifactService:
    """Dependency injection for ArtifactService."""
    return ArtifactService(session)


@router.post("/", response_model=SquadRead, status_code=status.HTTP_201_CREATED)
def create_squad(
    squad_create: SquadCreate, squad_service: SquadService = Depends(get_squad_service)
):
    """
    Create a new squad.

    - **squad_code**: Unique squad code (lowercase, no spaces, a-z0-9-_)
    - **name**: Display name of the squad
    - **tech_lead**: Name of the Tech Lead
    - **status**: Squad status (active, discontinued, archived)
    - **discontinued_reason**: Reason for discontinuation (required if status=discontinued)
    """
    try:
        return squad_service.create_squad(squad_create)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[SquadRead])
def list_squads(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    squad_service: SquadService = Depends(get_squad_service),
):
    """
    List all squads with optional filtering.

    - **status**: Filter by status (active, discontinued, archived)
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (default: 100)
    """
    return squad_service.list_squads(status=status, skip=skip, limit=limit)


@router.get("/{squad_code}", response_model=SquadRead)
def get_squad(
    squad_code: str, squad_service: SquadService = Depends(get_squad_service)
):
    """
    Get squad by code.

    - **squad_code**: Squad code to retrieve
    """
    squad = squad_service.get_squad(squad_code)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad with code '{squad_code}' not found",
        )
    return squad


@router.patch("/{squad_code}", response_model=SquadRead)
def update_squad(
    squad_code: str,
    squad_update: SquadUpdate,
    squad_service: SquadService = Depends(get_squad_service),
):
    """
    Update a squad.

    - **squad_code**: Squad code to update
    - **name**: New display name (optional)
    - **tech_lead**: New Tech Lead name (optional)
    - **status**: New status (optional)
    - **discontinued_reason**: New discontinuation reason (optional)
    """
    try:
        squad = squad_service.update_squad(squad_code, squad_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad with code '{squad_code}' not found",
        )
    return squad


@router.delete("/{squad_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_squad(
    squad_code: str,
    reason: str = "Discontinued by user",
    squad_service: SquadService = Depends(get_squad_service),
):
    """
    Soft delete a squad (mark as discontinued).

    - **squad_code**: Squad code to delete
    - **reason**: Reason for discontinuation (default: "Discontinued by user")
    """
    success = squad_service.delete_squad(squad_code, reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad with code '{squad_code}' not found",
        )


@router.get("/{squad_code}/artifacts", response_model=List[ArtifactRead])
def get_squad_artifacts(
    squad_code: str,
    squad_service: SquadService = Depends(get_squad_service),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """
    Get all artifacts for a specific squad.

    - **squad_code**: Code of the squad
    """
    # First get the squad to get its ID
    squad = squad_service.get_squad(squad_code)
    if not squad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Squad with code '{squad_code}' not found",
        )

    # Get artifacts for this squad
    artifacts = artifact_service.get_artifacts_by_squad(squad.id)
    return artifacts
