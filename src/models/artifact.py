"""
Unified artifact model for all artifact types.
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import field_validator, model_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .artifact_reference import ArtifactReference
    from .squad import Squad


class ArtifactBase(SQLModel):
    """Base artifact model with validation."""

    artifact_type: str = Field(
        ...,
        description="Type of artifact: adr, rfc, evidence, governance, implementation, visibility, uncommon",
        max_length=20,
    )
    artifact_number: str = Field(
        ...,
        description="Artifact number format varies by type, or 'auto' for auto-generation",
        max_length=50,
        unique=True,
    )
    title: str = Field(..., description="Title of the artifact", max_length=200)
    status: str = Field(
        default="proposed",
        description="Artifact status: proposed, accepted, rejected, superseded, discontinued",
    )
    level: Optional[int] = Field(
        default=None, description="Level (1-5) for ADRs only", ge=1, le=5
    )
    content: str = Field(..., description="Artifact content in Markdown format")
    file_path: Optional[str] = Field(
        default=None, description="Path to the generated markdown file", max_length=500
    )
    template_used: Optional[str] = Field(
        default=None,
        description="Template used to generate this artifact",
        max_length=100,
    )
    squad_id: int = Field(
        ..., foreign_key="squad.id", description="ID of the owning squad"
    )
    triggered_by_id: Optional[int] = Field(
        default=None,
        foreign_key="artifact.id",
        description="ID of the artifact that triggered this one",
    )
    trigger_reason: Optional[str] = Field(
        default=None,
        description="Reason for trigger (if triggered_by is set)",
        max_length=500,
    )
    tco_estimate: Optional[str] = Field(
        default=None,
        description="Total Cost of Ownership estimate (for ADR level >= 4)",
        max_length=500,
    )
    lgpd_analysis: Optional[str] = Field(
        default=None,
        description="LGPD (Brazilian GDPR) compliance analysis (for ADR level >= 4)",
        max_length=1000,
    )
    rfc_status: Optional[str] = Field(
        default=None,
        description="RFC status (required for ADR level >= 3)",
        max_length=50,
    )
    health_compliance_impact: Optional[str] = Field(
        default=None,
        description="Health compliance impact analysis (for healthcare organizations)",
        max_length=1000,
    )
    created_by_ip: Optional[str] = Field(
        default=None, description="IP address of the creator", max_length=45
    )

    @field_validator("artifact_type")
    @classmethod
    def validate_artifact_type(cls, v: str) -> str:
        """Validate artifact type."""
        allowed_types = {
            "adr",
            "rfc",
            "evidence",
            "governance",
            "implementation",
            "visibility",
            "uncommon",
        }
        if v not in allowed_types:
            raise ValueError(
                f"artifact_type must be one of: {', '.join(sorted(allowed_types))}"
            )
        return v

    @field_validator("artifact_number")
    @classmethod
    def validate_artifact_number(cls, v: str) -> str:
        """Validate artifact number format or allow 'auto'."""
        if v == "auto":
            return v

        # Validate based on type - will be done in model_validator with type context
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed_statuses = {
            "proposed",
            "accepted",
            "rejected",
            "reopened",
            "superseded",
            "discontinued",
        }
        if v not in allowed_statuses:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(allowed_statuses))}"
            )
        return v

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: Optional[int], info) -> Optional[int]:
        """Validate level is only provided for ADRs."""
        if v is not None:
            artifact_type = info.data.get("artifact_type")
            if artifact_type != "adr":
                raise ValueError("level can only be set for artifact_type='adr'")
        return v

    @model_validator(mode="after")
    def validate_artifact_number_format(self):
        """Validate artifact number format based on type."""
        if self.artifact_number == "auto":
            return self

        if self.artifact_type == "adr":
            if not re.match(r"^ADR-\d{3}-\d{3}$", self.artifact_number):
                raise ValueError("ADR artifact_number must be in format ADR-XXX-XXX")
        elif self.artifact_type == "rfc":
            if not re.match(r"^RFC-\d{4}-\d{3}$", self.artifact_number):
                raise ValueError("RFC artifact_number must be in format RFC-YYYY-XXX")
        elif self.artifact_type == "evidence":
            if not re.match(r"^EVI-\d{4}-\d{3}$", self.artifact_number):
                raise ValueError(
                    "Evidence artifact_number must be in format EVI-YYYY-XXX"
                )
        elif self.artifact_type == "governance":
            if not re.match(r"^GOV-\d{4}-\d{3}$", self.artifact_number):
                raise ValueError(
                    "Governance artifact_number must be in format GOV-YYYY-XXX"
                )
        elif self.artifact_type == "implementation":
            if not re.match(r"^IMP-\d{3}$", self.artifact_number):
                raise ValueError(
                    "Implementation artifact_number must be in format IMP-XXX"
                )
        elif self.artifact_type == "visibility":
            if not re.match(r"^VIS-\d{3}$", self.artifact_number):
                raise ValueError("Visibility artifact_number must be in format VIS-XXX")
        elif self.artifact_type == "uncommon":
            if not re.match(r"^UNC-\d{4}-\d{3}$", self.artifact_number):
                raise ValueError(
                    "Uncommon artifact_number must be in format UNC-YYYY-XXX"
                )

        return self

    @model_validator(mode="after")
    def validate_level_requirements(self):
        """Validate level-specific requirements for ADRs."""
        if self.artifact_type == "adr":
            if self.level is None:
                raise ValueError("level is required for ADR artifacts")

            # Level 3+ requires RFC status
            if self.level >= 3 and not self.rfc_status:
                raise ValueError("rfc_status is required for ADR level >= 3")

            # Level 4+ requires TCO estimate and LGPD analysis
            if self.level >= 4:
                if not self.tco_estimate:
                    raise ValueError("tco_estimate is required for ADR level >= 4")
                if not self.lgpd_analysis:
                    raise ValueError("lgpd_analysis is required for ADR level >= 4")

        # Non-ADR artifacts should not have level-specific fields
        if self.artifact_type != "adr":
            if self.tco_estimate:
                raise ValueError("tco_estimate can only be set for ADR artifacts")
            if self.lgpd_analysis:
                raise ValueError("lgpd_analysis can only be set for ADR artifacts")
            if self.rfc_status:
                raise ValueError("rfc_status can only be set for ADR artifacts")
            if self.health_compliance_impact:
                raise ValueError(
                    "health_compliance_impact can only be set for ADR artifacts"
                )

        return self


class Artifact(ArtifactBase, table=True):  # type: ignore[call-arg]
    """Artifact database model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    squad: Optional["Squad"] = Relationship(back_populates="artifacts")
    triggered_by: Optional["Artifact"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Artifact.id",
            "foreign_keys": "Artifact.triggered_by_id",
        }
    )

    # References where this artifact is the source
    outgoing_references: list["ArtifactReference"] = Relationship(
        back_populates="from_artifact",
        sa_relationship_kwargs={
            "foreign_keys": "ArtifactReference.from_artifact_id",
            "cascade": "all, delete-orphan",
        },
    )

    # References where this artifact is the target
    incoming_references: list["ArtifactReference"] = Relationship(
        back_populates="to_artifact",
        sa_relationship_kwargs={
            "foreign_keys": "ArtifactReference.to_artifact_id",
            "cascade": "all, delete-orphan",
        },
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class ArtifactCreate(ArtifactBase):
    """Schema for creating a new artifact."""

    pass


class ArtifactUpdate(SQLModel):
    """Schema for updating an artifact (excluding immutable fields)."""

    title: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = Field(default=None)
    status: Optional[str] = Field(
        default=None,
        description="Artifact status: proposed, accepted, rejected, superseded, discontinued",
    )
    level: Optional[int] = Field(default=None, ge=1, le=5)
    tco_estimate: Optional[str] = Field(default=None, max_length=500)
    lgpd_analysis: Optional[str] = Field(default=None, max_length=1000)
    rfc_status: Optional[str] = Field(default=None, max_length=50)
    health_compliance_impact: Optional[str] = Field(default=None, max_length=1000)
    trigger_reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value if provided."""
        if v is not None:
            allowed_statuses = {
                "proposed",
                "accepted",
                "rejected",
                "reopened",
                "superseded",
                "discontinued",
            }
            if v not in allowed_statuses:
                raise ValueError(
                    f"status must be one of: {', '.join(sorted(allowed_statuses))}"
                )
        return v


class ArtifactStatusUpdate(SQLModel):
    """Schema for updating artifact status."""

    status: str = Field(
        ...,
        description="New artifact status: proposed, accepted, rejected, superseded, discontinued",
    )
    superseded_by: Optional[str] = Field(
        default=None,
        description="Artifact number that supersedes this one (required for status=superseded)",
        max_length=50,
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Reason for rejection (required for status=rejected)",
        max_length=500,
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed_statuses = {
            "proposed",
            "accepted",
            "rejected",
            "reopened",
            "superseded",
            "discontinued",
        }
        if v not in allowed_statuses:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(allowed_statuses))}"
            )
        return v

    @model_validator(mode="after")
    def validate_status_dependent_fields(self):
        """Validate superseded_by and rejection_reason based on status."""
        if self.status == "superseded" and not self.superseded_by:
            raise ValueError("superseded_by is required when status=superseded")
        if self.status == "rejected" and not self.rejection_reason:
            raise ValueError("rejection_reason is required when status=rejected")
        return self


class ArtifactRead(ArtifactBase):
    """Schema for reading an artifact."""

    id: int
    created_at: datetime
    updated_at: datetime
    squad_name: Optional[str] = None  # Will be populated from relationship
    triggered_by_title: Optional[str] = None  # Will be populated from relationship
