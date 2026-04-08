"""
Artifact reference model for linking artifacts together.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import field_validator

if TYPE_CHECKING:
    from .artifact import Artifact


class ArtifactReferenceBase(SQLModel):
    """Base artifact reference model."""

    from_artifact_id: int = Field(..., foreign_key="artifact.id", description="Source artifact ID")
    to_artifact_id: int = Field(..., foreign_key="artifact.id", description="Target artifact ID")
    reference_type: str = Field(
        ...,
        description="Type of reference: triggers, supersedes, implements, documents, evidences",
        max_length=20
    )

    @field_validator("reference_type")
    @classmethod
    def validate_reference_type(cls, v: str) -> str:
        """Validate reference type."""
        allowed_types = {"triggers", "supersedes", "implements", "documents", "evidences"}
        if v not in allowed_types:
            raise ValueError(f"reference_type must be one of: {', '.join(sorted(allowed_types))}")
        return v


class ArtifactReference(ArtifactReferenceBase, table=True):
    """Artifact reference database model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    from_artifact: "Artifact" = Relationship(
        back_populates="outgoing_references",
        sa_relationship_kwargs={"foreign_keys": "ArtifactReference.from_artifact_id"}
    )
    to_artifact: "Artifact" = Relationship(
        back_populates="incoming_references",
        sa_relationship_kwargs={"foreign_keys": "ArtifactReference.to_artifact_id"}
    )

    class Config:
        """Pydantic config."""
        from_attributes = True


class ArtifactReferenceCreate(ArtifactReferenceBase):
    """Schema for creating a new artifact reference."""
    pass


class ArtifactReferenceRead(ArtifactReferenceBase):
    """Schema for reading an artifact reference."""

    id: int
    created_at: datetime
    from_artifact_title: Optional[str] = None  # Will be populated from relationship
    to_artifact_title: Optional[str] = None  # Will be populated from relationship