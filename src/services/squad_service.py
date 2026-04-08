"""
Squad service with business logic.
"""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from ..database import get_session
from ..models.squad import Squad, SquadCreate, SquadRead, SquadUpdate


class SquadService:
    """Service for managing squads."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize squad service.

        Args:
            session: Optional database session (for testing)
        """
        self.session = session

    def _get_session(self) -> Session:
        """Get database session."""
        if self.session:
            return self.session
        # Note: In production, this would use dependency injection
        # For now, we create a new session
        from ..database.engine import get_engine

        engine = get_engine(testing=False)
        return Session(engine)

    def create_squad(self, squad_create: SquadCreate) -> SquadRead:
        """
        Create a new squad.

        Args:
            squad_create: Squad creation data

        Returns:
            Created squad
        """
        session = self._get_session()

        # Check if squad_code already exists
        existing = session.exec(
            select(Squad).where(Squad.squad_code == squad_create.squad_code)
        ).first()
        if existing:
            raise ValueError(
                f"Squad with code '{squad_create.squad_code}' already exists"
            )

        # Create squad
        squad = Squad(**squad_create.model_dump())
        session.add(squad)
        session.commit()
        session.refresh(squad)

        return SquadRead.model_validate(squad)

    def get_squad(self, squad_code: str) -> Optional[SquadRead]:
        """
        Get squad by code.

        Args:
            squad_code: Squad code

        Returns:
            Squad if found, None otherwise
        """
        session = self._get_session()

        squad = session.exec(
            select(Squad).where(Squad.squad_code == squad_code)
        ).first()

        if not squad:
            return None

        return SquadRead.model_validate(squad)

    def list_squads(
        self, status: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[SquadRead]:
        """
        List squads with optional filtering.

        Args:
            status: Filter by status (active, discontinued, archived)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of squads
        """
        session = self._get_session()

        query = select(Squad)

        if status:
            query = query.where(Squad.status == status)

        # Exclude soft-deleted squads (deleted_at is not null)
        query = query.where(Squad.deleted_at.is_(None))  # type: ignore[union-attr]

        query = query.offset(skip).limit(limit)

        squads = session.exec(query).all()
        return [SquadRead.model_validate(squad) for squad in squads]

    def update_squad(
        self, squad_code: str, squad_update: SquadUpdate
    ) -> Optional[SquadRead]:
        """
        Update a squad.

        Args:
            squad_code: Squad code to update
            squad_update: Update data

        Returns:
            Updated squad if found, None otherwise
        """
        session = self._get_session()

        squad = session.exec(
            select(Squad).where(Squad.squad_code == squad_code)
        ).first()

        if not squad:
            return None

        # Update fields
        update_data = squad_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(squad, field, value)

        # Update timestamp
        squad.updated_at = datetime.utcnow()

        # If status changed to discontinued, ensure reason is set
        if squad_update.status == "discontinued":
            # Check if reason is provided in update or already exists
            if (
                "discontinued_reason" not in update_data
                and not squad.discontinued_reason
            ):
                raise ValueError(
                    "discontinued_reason is required when status=discontinued"
                )

        session.add(squad)
        session.commit()
        session.refresh(squad)

        return SquadRead.model_validate(squad)

    def delete_squad(
        self, squad_code: str, reason: str = "Discontinued by user"
    ) -> bool:
        """
        Soft delete a squad (mark as discontinued).

        Args:
            squad_code: Squad code to delete
            reason: Reason for discontinuation

        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()

        squad = session.exec(
            select(Squad).where(Squad.squad_code == squad_code)
        ).first()

        if not squad:
            return False

        # Soft delete: mark as discontinued and set deleted_at
        squad.status = "discontinued"
        squad.discontinued_reason = reason
        squad.deleted_at = datetime.utcnow()
        squad.updated_at = datetime.utcnow()

        session.add(squad)
        session.commit()

        return True

    def get_squad_by_id(self, squad_id: int) -> Optional[Squad]:
        """
        Get squad by ID (internal use).

        Args:
            squad_id: Squad ID

        Returns:
            Squad model if found
        """
        session = self._get_session()
        return session.get(Squad, squad_id)
