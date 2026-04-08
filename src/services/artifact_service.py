"""
Artifact service for unified artifact model.

PHASE 3: Artifact Service
- Business logic for artifact CRUD operations for all 7 artifact types
- Integration with template and markdown generation services
- Auto-number generation for all artifact types
- Validation and schema matching
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlmodel import Session, or_, select

from ..database import get_session
from ..models.artifact import (
    Artifact,
    ArtifactCreate,
    ArtifactRead,
    ArtifactStatusUpdate,
    ArtifactUpdate,
)
from ..models.squad import Squad
from .squad_service import SquadService
from .template_service import TemplateService


class ArtifactService:
    """Service for managing artifacts of all types."""

    # Number generation patterns for each artifact type
    NUMBER_PATTERNS = {
        "adr": r"ADR-(\d{3})-(\d{3})",  # ADR-001-001
        "rfc": r"RFC-(\d{4})-(\d{3})",  # RFC-2024-001
        "evidence": r"EVI-(\d{4})-(\d{3})",  # EVI-2024-001
        "governance": r"GOV-(\d{4})-(\d{3})",  # GOV-2024-001
        "implementation": r"IMP-(\d{3})",  # IMP-001
        "visibility": r"VIS-(\d{3})",  # VIS-001
        "uncommon": r"UNC-(\d{4})-(\d{3})",  # UNC-2024-001
    }

    # Status transition rules
    STATUS_TRANSITIONS = {
        "proposed": ["accepted", "rejected"],
        "accepted": ["superseded", "discontinued"],
        "rejected": ["reopened"],
        "reopened": ["accepted", "rejected"],
        "superseded": [],  # Terminal state
        "discontinued": [],  # Terminal state
    }

    def __init__(
        self,
        session: Optional[Session] = None,
        template_service: Optional[TemplateService] = None,
    ):
        """
        Initialize ArtifactService.

        Args:
            session: Optional database session (for testing)
            template_service: Optional template service
        """
        self.session = session
        self.template_service = template_service or TemplateService()
        self.squad_service = SquadService(session)

    def _get_session(self) -> Session:
        """Get database session."""
        if self.session:
            return self.session
        # Note: In production, this would use dependency injection
        # For now, we create a new session
        from ..database.engine import get_engine

        engine = get_engine(testing=False)
        return Session(engine)

    def _generate_artifact_number(
        self, artifact_type: str, level: Optional[int], squad_id: int, session: Session
    ) -> str:
        """
        Generate next artifact number based on type.

        Args:
            artifact_type: Type of artifact
            level: ADR level (1-5) or None for non-ADR artifacts
            squad_id: Squad ID for context
            session: Active database session (same transaction as caller)

        Returns:
            Generated artifact number
        """
        if artifact_type == "adr":
            # For ADR: ADR-{level:03d}-{sequence:03d}
            if level is None:
                raise ValueError("level is required for ADR artifacts")

            query = select(Artifact).where(
                Artifact.artifact_type == "adr",
                Artifact.level == level,
                Artifact.squad_id == squad_id,
            )
            adrs = session.exec(query).all()

            max_num = 0
            pattern = re.compile(rf"ADR-{level:03d}-(\d{{3}})")

            for adr in adrs:
                match = pattern.match(adr.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"ADR-{level:03d}-{next_num:03d}"

        elif artifact_type == "rfc":
            # For RFC: RFC-{year}-{sequence:03d}
            current_year = datetime.now().year

            query = select(Artifact).where(
                Artifact.artifact_type == "rfc", Artifact.squad_id == squad_id
            )
            rfcs = session.exec(query).all()

            max_num = 0
            pattern = re.compile(rf"RFC-{current_year}-(\d{{3}})")

            for rfc in rfcs:
                match = pattern.match(rfc.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"RFC-{current_year}-{next_num:03d}"

        elif artifact_type == "evidence":
            # For Evidence: EVI-{year}-{sequence:03d}
            current_year = datetime.now().year

            query = select(Artifact).where(
                Artifact.artifact_type == "evidence", Artifact.squad_id == squad_id
            )
            evidence_items = session.exec(query).all()

            max_num = 0
            pattern = re.compile(rf"EVI-{current_year}-(\d{{3}})")

            for item in evidence_items:
                match = pattern.match(item.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"EVI-{current_year}-{next_num:03d}"

        elif artifact_type == "governance":
            # For Governance: GOV-{year}-{sequence:03d}
            current_year = datetime.now().year

            query = select(Artifact).where(
                Artifact.artifact_type == "governance", Artifact.squad_id == squad_id
            )
            governance_items = session.exec(query).all()

            max_num = 0
            pattern = re.compile(rf"GOV-{current_year}-(\d{{3}})")

            for item in governance_items:
                match = pattern.match(item.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"GOV-{current_year}-{next_num:03d}"

        elif artifact_type == "implementation":
            # For Implementation: IMP-{sequence:03d}
            query = select(Artifact).where(
                Artifact.artifact_type == "implementation",
                Artifact.squad_id == squad_id,
            )
            implementations = session.exec(query).all()

            max_num = 0
            pattern = re.compile(r"IMP-(\d{3})")

            for item in implementations:
                match = pattern.match(item.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"IMP-{next_num:03d}"

        elif artifact_type == "visibility":
            # For Visibility: VIS-{sequence:03d}
            query = select(Artifact).where(
                Artifact.artifact_type == "visibility", Artifact.squad_id == squad_id
            )
            visibility_items = session.exec(query).all()

            max_num = 0
            pattern = re.compile(r"VIS-(\d{3})")

            for item in visibility_items:
                match = pattern.match(item.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"VIS-{next_num:03d}"

        elif artifact_type == "uncommon":
            # For Uncommon: UNC-{year}-{sequence:03d}
            current_year = datetime.now().year

            query = select(Artifact).where(
                Artifact.artifact_type == "uncommon", Artifact.squad_id == squad_id
            )
            uncommon_items = session.exec(query).all()

            max_num = 0
            pattern = re.compile(rf"UNC-{current_year}-(\d{{3}})")

            for item in uncommon_items:
                match = pattern.match(item.artifact_number)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

            next_num = max_num + 1
            return f"UNC-{current_year}-{next_num:03d}"

        else:
            raise ValueError(f"Unsupported artifact type: {artifact_type}")

    def create_artifact(self, artifact_create: ArtifactCreate) -> ArtifactRead:
        """
        Create a new artifact.

        Args:
            artifact_create: Artifact creation data

        Returns:
            Created artifact
        """
        session = self._get_session()

        # Check if squad exists
        squad = self.squad_service.get_squad_by_id(artifact_create.squad_id)
        if not squad:
            raise ValueError(f"Squad with ID {artifact_create.squad_id} not found")

        # Check if squad is active
        if squad.status != "active":
            raise ValueError(
                f"Cannot create artifact for squad with status '{squad.status}'"
            )

        # Generate artifact number if not provided or "auto"
        if (
            not artifact_create.artifact_number
            or artifact_create.artifact_number == "auto"
        ):
            artifact_number = self._generate_artifact_number(
                artifact_create.artifact_type,
                artifact_create.level,
                artifact_create.squad_id,
                session,
            )
        else:
            artifact_number = artifact_create.artifact_number

        # Check if artifact number already exists
        existing = session.exec(
            select(Artifact).where(Artifact.artifact_number == artifact_number)
        ).first()
        if existing:
            raise ValueError(f"Artifact with number '{artifact_number}' already exists")

        # Validate artifact data against template schema
        artifact_data = artifact_create.model_dump()
        artifact_data["artifact_number"] = artifact_number

        # Validate level-specific requirements for ADR
        if artifact_create.artifact_type == "adr" and artifact_create.level:
            if artifact_create.level >= 4:
                if not artifact_create.tco_estimate:
                    raise ValueError("tco_estimate is required for ADR level >= 4")
                if not artifact_create.lgpd_analysis:
                    raise ValueError("lgpd_analysis is required for ADR level >= 4")
                if not artifact_create.health_compliance_impact:
                    raise ValueError(
                        "health_compliance_impact is required for ADR level >= 4"
                    )
            if artifact_create.level >= 3:
                if not artifact_create.rfc_status:
                    raise ValueError("rfc_status is required for ADR level >= 3")

        # Validate template requirements
        self.template_service.validate_artifact_against_template(
            artifact_create.artifact_type, artifact_data
        )

        # Generate content from template
        generated_content = self.template_service.generate_content_for_artifact(
            artifact_create
        )

        # Update content with generated content if not provided
        if not artifact_create.content:
            artifact_data["content"] = generated_content
        else:
            artifact_data["content"] = artifact_create.content

        # Create artifact
        artifact = Artifact(**artifact_data)

        session.add(artifact)
        session.commit()
        session.refresh(artifact)

        # Generate and save markdown file
        try:
            type_folder_map = {
                "adr": "decisions",
                "rfc": "rfcs",
                "evidence": "evidence",
                "governance": "governance",
                "implementation": "implementation",
                "visibility": "visibility",
                "uncommon": "uncommon",
            }
            folder = type_folder_map.get(artifact.artifact_type, artifact.artifact_type)
            arch_root = Path(__file__).parent.parent.parent / "architecture"
            dest = arch_root / folder / f"{artifact_number}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(artifact.content, encoding="utf-8")
            artifact.file_path = str(dest.relative_to(arch_root.parent))
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
        except Exception as e:
            print(f"Warning: Failed to save markdown for {artifact_number}: {e}")

        # Create response with squad name
        artifact_read = ArtifactRead.model_validate(artifact)
        artifact_read.squad_name = squad.name

        return artifact_read

    def get_artifact(self, artifact_number: str) -> Optional[ArtifactRead]:
        """
        Get artifact by number.

        Args:
            artifact_number: Artifact number

        Returns:
            Artifact if found, None otherwise
        """
        session = self._get_session()

        artifact = session.exec(
            select(Artifact).where(Artifact.artifact_number == artifact_number)
        ).first()

        if not artifact:
            return None

        # Get squad name
        squad = session.get(Squad, artifact.squad_id)
        squad_name = squad.name if squad else "Unknown"

        artifact_read = ArtifactRead.model_validate(artifact)
        artifact_read.squad_name = squad_name

        return artifact_read

    def get_artifacts(self, skip: int = 0, limit: int = 100) -> List[ArtifactRead]:
        """
        Get all artifacts with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of artifacts
        """
        return self.list_artifacts(skip=skip, limit=limit)

    def list_artifacts(
        self,
        artifact_type: Optional[str] = None,
        level: Optional[int] = None,
        status: Optional[str] = None,
        squad_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ArtifactRead]:
        """
        List artifacts with optional filtering.

        Args:
            artifact_type: Filter by artifact type
            level: Filter by ADR level (1-5)
            status: Filter by status
            squad_id: Filter by squad ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of artifacts
        """
        session = self._get_session()

        query = select(Artifact)

        if artifact_type:
            query = query.where(Artifact.artifact_type == artifact_type)

        if level is not None:
            query = query.where(Artifact.level == level)

        if status:
            query = query.where(Artifact.status == status)

        if squad_id:
            query = query.where(Artifact.squad_id == squad_id)

        query = query.offset(skip).limit(limit)

        artifacts = session.exec(query).all()

        # Get squad names for all artifacts
        squad_ids = {
            artifact.squad_id for artifact in artifacts if artifact.squad_id is not None
        }
        if squad_ids:
            squads = session.exec(select(Squad).where(Squad.id.in_(squad_ids))).all()
            squad_map = {squad.id: squad.name for squad in squads}
        else:
            squad_map = {}

        # Create response objects
        result = []
        for artifact in artifacts:
            artifact_read = ArtifactRead.model_validate(artifact)
            artifact_read.squad_name = squad_map.get(artifact.squad_id, "Unknown")
            result.append(artifact_read)

        return result

    def update_artifact(
        self, artifact_number: str, artifact_update: ArtifactUpdate
    ) -> Optional[ArtifactRead]:
        """
        Update an artifact.

        Args:
            artifact_number: Artifact number to update
            artifact_update: Update data

        Returns:
            Updated artifact if found, None otherwise
        """
        session = self._get_session()

        artifact = session.exec(
            select(Artifact).where(Artifact.artifact_number == artifact_number)
        ).first()

        if not artifact:
            return None

        # Update fields
        update_data = artifact_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(artifact, field, value)

        # Update timestamp
        artifact.updated_at = datetime.utcnow()

        # Validate level-specific requirements for ADR if level is being updated
        if "level" in update_data and artifact.artifact_type == "adr":
            new_level = update_data["level"]

            if new_level >= 4:
                if not artifact.tco_estimate:
                    raise ValueError("tco_estimate is required for ADR level >= 4")
                if not artifact.lgpd_analysis:
                    raise ValueError("lgpd_analysis is required for ADR level >= 4")
                if not artifact.health_compliance_impact:
                    raise ValueError(
                        "health_compliance_impact is required for ADR level >= 4"
                    )

            if new_level >= 3 and not artifact.rfc_status:
                raise ValueError("rfc_status is required for ADR level >= 3")

        # Also validate if level >= 4 and tco_estimate/lgpd_analysis fields are being updated
        if artifact.artifact_type == "adr" and artifact.level >= 4:
            if "tco_estimate" in update_data and not update_data["tco_estimate"]:
                raise ValueError("tco_estimate cannot be empty for ADR level >= 4")
            if "lgpd_analysis" in update_data and not update_data["lgpd_analysis"]:
                raise ValueError("lgpd_analysis cannot be empty for ADR level >= 4")
            if (
                "health_compliance_impact" in update_data
                and not update_data["health_compliance_impact"]
            ):
                raise ValueError(
                    "health_compliance_impact cannot be empty for ADR level >= 4"
                )

        session.add(artifact)
        session.commit()
        session.refresh(artifact)

        # Get squad name
        squad = session.get(Squad, artifact.squad_id)
        squad_name = squad.name if squad else "Unknown"

        artifact_read = ArtifactRead.model_validate(artifact)
        artifact_read.squad_name = squad_name

        return artifact_read

    def update_artifact_status(
        self, artifact_number: str, status_update: ArtifactStatusUpdate
    ) -> Optional[ArtifactRead]:
        """
        Update artifact status with validation.

        Args:
            artifact_number: Artifact number
            status_update: Status update data

        Returns:
            Updated artifact if found, None otherwise
        """
        session = self._get_session()

        artifact = session.exec(
            select(Artifact).where(Artifact.artifact_number == artifact_number)
        ).first()

        if not artifact:
            return None

        # Validate status transition
        current_status = artifact.status
        new_status = status_update.status

        if new_status not in self.STATUS_TRANSITIONS.get(current_status, []):
            raise ValueError(
                f"Cannot transition from '{current_status}' to '{new_status}'"
            )

        # Update status
        artifact.status = new_status
        artifact.updated_at = datetime.utcnow()

        # Handle special cases
        if new_status == "superseded":
            # Validate superseded_by artifact exists
            superseded_artifact = session.exec(
                select(Artifact).where(
                    Artifact.artifact_number == status_update.superseded_by
                )
            ).first()
            if not superseded_artifact:
                raise ValueError(
                    f"Artifact '{status_update.superseded_by}' not found for superseded_by"
                )
            # Could store this relationship in a separate field if needed

        elif new_status == "rejected":
            # Store rejection reason if provided
            if status_update.rejection_reason:
                # Store in a note or separate field (not in current model)
                pass

        session.add(artifact)
        session.commit()
        session.refresh(artifact)

        # Get squad name
        squad = session.get(Squad, artifact.squad_id)
        squad_name = squad.name if squad else "Unknown"

        artifact_read = ArtifactRead.model_validate(artifact)
        artifact_read.squad_name = squad_name

        return artifact_read

    def search_artifacts(
        self,
        query: str,
        artifact_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ArtifactRead]:
        """
        Search artifacts by title or content.

        Args:
            query: Search query
            artifact_type: Optional filter by artifact type
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of matching artifacts
        """
        session = self._get_session()

        search_pattern = f"%{query}%"

        sql_query = select(Artifact).where(
            or_(
                Artifact.title.ilike(search_pattern),  # type: ignore[attr-defined]
                Artifact.content.ilike(search_pattern),  # type: ignore[attr-defined]
            )
        )

        if artifact_type:
            sql_query = sql_query.where(Artifact.artifact_type == artifact_type)

        sql_query = sql_query.offset(skip).limit(limit)

        artifacts = session.exec(sql_query).all()

        # Get squad names
        squad_ids = {
            artifact.squad_id for artifact in artifacts if artifact.squad_id is not None
        }
        if squad_ids:
            squads = session.exec(select(Squad).where(Squad.id.in_(squad_ids))).all()
            squad_map = {squad.id: squad.name for squad in squads}
        else:
            squad_map = {}

        # Create response objects
        result = []
        for artifact in artifacts:
            artifact_read = ArtifactRead.model_validate(artifact)
            artifact_read.squad_name = squad_map.get(artifact.squad_id, "Unknown")
            result.append(artifact_read)

        return result

    def get_artifacts_by_squad(self, squad_id: int) -> List[ArtifactRead]:
        """
        Get all artifacts for a specific squad.

        Args:
            squad_id: ID of the squad

        Returns:
            List of artifacts for the squad
        """
        session = self._get_session()

        sql_query = select(Artifact).where(Artifact.squad_id == squad_id)
        artifacts = session.exec(sql_query).all()

        # Get squad name
        squad = session.get(Squad, squad_id)
        squad_name = squad.name if squad else "Unknown"

        # Create response objects
        result = []
        for artifact in artifacts:
            artifact_read = ArtifactRead.model_validate(artifact)
            artifact_read.squad_name = squad_name
            result.append(artifact_read)

        return result

    def get_artifact_by_id(self, artifact_id: int) -> Optional[ArtifactRead]:
        """
        Get artifact by ID.

        Args:
            artifact_id: Artifact ID

        Returns:
            Artifact if found, None otherwise
        """
        session = self._get_session()

        artifact = session.get(Artifact, artifact_id)

        if not artifact:
            return None

        # Get squad name
        squad = session.get(Squad, artifact.squad_id)
        squad_name = squad.name if squad else "Unknown"

        artifact_read = ArtifactRead.model_validate(artifact)
        artifact_read.squad_name = squad_name

        return artifact_read

    def delete_artifact(self, artifact_number: str) -> bool:
        """
        Delete an artifact.

        Args:
            artifact_number: Artifact number

        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()

        artifact = session.exec(
            select(Artifact).where(Artifact.artifact_number == artifact_number)
        ).first()

        if not artifact:
            return False

        session.delete(artifact)
        session.commit()

        return True

    def get_artifact_counts(self) -> Dict[str, Any]:
        """
        Get artifact counts and statistics.

        Returns:
            Dictionary with total count, counts by type, and counts by status
        """
        session = self._get_session()

        try:
            # Get total artifact count
            total_count = session.exec(select(Artifact)).all()
            total = len(total_count)

            # Get counts by type
            by_type = {}
            artifact_types = [
                "adr",
                "rfc",
                "evidence",
                "governance",
                "implementation",
                "visibility",
                "uncommon",
            ]

            for artifact_type in artifact_types:
                count = len(
                    session.exec(
                        select(Artifact).where(Artifact.artifact_type == artifact_type)
                    ).all()
                )
                if count > 0:
                    by_type[artifact_type] = count

            # Get counts by status
            by_status = {}
            statuses = [
                "proposed",
                "accepted",
                "rejected",
                "superseded",
                "discontinued",
            ]

            for status in statuses:
                count = len(
                    session.exec(
                        select(Artifact).where(Artifact.status == status)
                    ).all()
                )
                if count > 0:
                    by_status[status] = count

            return {"total": total, "by_type": by_type, "by_status": by_status}

        except Exception as e:
            # Return empty counts on error
            return {"total": 0, "by_type": {}, "by_status": {}, "error": str(e)}
