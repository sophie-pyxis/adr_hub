"""
Squad model for AI Architecture Governance System.
"""

import re
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .artifact import Artifact


class SquadBase(SQLModel):
    """Base squad model with validation."""

    squad_code: str = Field(
        ...,
        description="Unique squad code (lowercase, no spaces, a-z0-9-_)",
        min_length=3,
        max_length=50,
    )
    name: str = Field(..., description="Display name of the squad", max_length=100)
    tech_lead: str = Field(..., description="Name of the Tech Lead", max_length=100)
    status: str = Field(
        default="active", description="Squad status: active, discontinued, archived"
    )
    discontinued_reason: Optional[str] = Field(
        default=None,
        description="Reason for discontinuation (required if status=discontinued)",
        max_length=500,
    )

    @field_validator("squad_code")
    @classmethod
    def validate_squad_code(cls, v: str) -> str:
        """Validate squad_code format: lowercase, no spaces, only a-z0-9-_."""
        # Convert to lowercase and replace spaces with hyphens
        v = v.lower().strip().replace(" ", "-")

        # Remove any other invalid characters
        v = re.sub(r"[^a-z0-9-_]", "", v)

        # Ensure it matches the pattern
        if not re.match(r"^[a-z0-9-_]{3,50}$", v):
            raise ValueError(
                "squad_code must be 3-50 characters, lowercase, "
                "containing only a-z, 0-9, hyphens, and underscores"
            )

        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed_statuses = {"active", "discontinued", "archived"}
        if v not in allowed_statuses:
            raise ValueError(f"status must be one of: {', '.join(allowed_statuses)}")
        return v

    @field_validator("discontinued_reason")
    @classmethod
    def validate_discontinued_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Validate discontinued_reason is provided when status=discontinued."""
        if info.data.get("status") == "discontinued" and not v:
            raise ValueError("discontinued_reason is required when status=discontinued")
        return v


class Squad(SquadBase, table=True):  # type: ignore[call-arg]
    """Squad database model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    # Relationships
    artifacts: List["Artifact"] = Relationship(
        back_populates="squad", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class SquadCreate(SquadBase):
    """Schema for creating a new squad."""

    pass


class SquadUpdate(SQLModel):
    """Schema for updating a squad."""

    name: Optional[str] = Field(default=None, max_length=100)
    tech_lead: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(
        default=None, description="Squad status: active, discontinued, archived"
    )
    discontinued_reason: Optional[str] = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value if provided."""
        if v is not None:
            allowed_statuses = {"active", "discontinued", "archived"}
            if v not in allowed_statuses:
                raise ValueError(
                    f"status must be one of: {', '.join(allowed_statuses)}"
                )
        return v

    @field_validator("discontinued_reason")
    @classmethod
    def validate_discontinued_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Validate discontinued_reason is provided when status=discontinued."""
        # Check if status is being set to discontinued in this update
        # In Pydantic v2, we use info.data to access other field values
        if info.data.get("status") == "discontinued" and not v:
            raise ValueError("discontinued_reason is required when status=discontinued")
        return v


class SquadRead(SquadBase):
    """Schema for reading a squad."""

    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
