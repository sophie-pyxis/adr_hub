"""
Trigger rule model for defining automatic artifact creation rules.
"""

from datetime import datetime
from typing import Optional

from pydantic.functional_validators import field_validator
from sqlmodel import Field, SQLModel


class TriggerRuleBase(SQLModel):
    """Base trigger rule model."""

    source_type: str = Field(
        ...,
        description="Type of artifact that triggers: adr, rfc, evidence, governance, etc.",
        max_length=20,
    )
    source_condition: str = Field(
        ...,
        description="Condition to trigger on (safe whitelist expression)",
        max_length=500,
    )
    target_type: str = Field(
        ...,
        description="Type of artifact to create: adr, rfc, evidence, governance, etc.",
        max_length=20,
    )
    auto_create: bool = Field(
        default=False,
        description="Whether to automatically create the target when condition is met",
    )
    required: bool = Field(
        default=False,
        description="Whether this trigger blocks status changes if not satisfied",
    )
    description: str = Field(
        ..., description="Description of what this rule does", max_length=500
    )

    @field_validator("source_type", "target_type")
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
            raise ValueError(f"Type must be one of: {', '.join(sorted(allowed_types))}")
        return v

    @field_validator("source_condition")
    @classmethod
    def validate_source_condition(cls, v: str) -> str:
        """Validate that condition only contains safe whitelisted operators."""
        # Check for dangerous patterns
        dangerous_patterns = [
            "__",
            "eval(",
            "exec(",
            "compile(",
            "import",
            "open(",
            "read(",
            "write(",
            "os.",
            "sys.",
            "subprocess.",
        ]
        for pattern in dangerous_patterns:
            if pattern in v.lower():
                raise ValueError(
                    f"Source condition contains potentially dangerous pattern: {pattern}"
                )

        # Check that condition uses only allowed operators and attributes
        allowed_operators = ["==", "!=", ">=", "<=", ">", "<", "and", "or", "not"]
        allowed_attributes = ["level", "status", "artifact_type"]

        # Simple validation - more thorough validation will happen in trigger service
        # where we parse and evaluate the condition safely
        tokens = v.lower().replace("(", " ").replace(")", " ").split()
        for token in tokens:
            if token in ["true", "false", "none"] or token.isdigit():
                continue
            if token in allowed_attributes:
                continue
            if token in allowed_operators:
                continue
            # Check if token is a string literal (in quotes)
            if (token.startswith('"') and token.endswith('"')) or (
                token.startswith("'") and token.endswith("'")
            ):
                continue
            # Check if token is a valid Python identifier (for future extensibility)
            if token.isidentifier():
                # Only allow specific identifiers
                if token not in ["level", "status", "artifact_type"]:
                    raise ValueError(f"Unknown identifier in source condition: {token}")

        return v


class TriggerRule(TriggerRuleBase, table=True):  # type: ignore[call-arg]
    """Trigger rule database model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        from_attributes = True


class TriggerRuleCreate(TriggerRuleBase):
    """Schema for creating a new trigger rule."""

    pass


class TriggerRuleRead(TriggerRuleBase):
    """Schema for reading a trigger rule."""

    id: int
    created_at: datetime


class TriggerRuleUpdate(SQLModel):
    """Schema for updating a trigger rule."""

    source_condition: Optional[str] = Field(
        default=None,
        description="Condition to trigger on (safe whitelist expression)",
        max_length=500,
    )
    description: Optional[str] = Field(
        default=None, description="Description of what this rule does", max_length=500
    )
    auto_create: Optional[bool] = Field(
        default=None,
        description="Whether to automatically create the target when condition is met",
    )
    required: Optional[bool] = Field(
        default=None,
        description="Whether this trigger blocks status changes if not satisfied",
    )

    @field_validator("source_condition")
    @classmethod
    def validate_source_condition(cls, v: str) -> str:
        """Validate that condition only contains safe whitelisted operators."""
        if v is None:
            return v

        # Check for dangerous patterns
        dangerous_patterns = [
            "__",
            "eval(",
            "exec(",
            "compile(",
            "import",
            "open(",
            "read(",
            "write(",
            "os.",
            "sys.",
            "subprocess.",
        ]
        for pattern in dangerous_patterns:
            if pattern in v.lower():
                raise ValueError(
                    f"Source condition contains potentially dangerous pattern: {pattern}"
                )

        # Check that condition uses only allowed operators and attributes
        allowed_operators = ["==", "!=", ">=", "<=", ">", "<", "and", "or", "not"]
        allowed_attributes = ["level", "status", "artifact_type"]

        # Simple validation - more thorough validation will happen in trigger service
        # where we parse and evaluate the condition safely
        tokens = v.lower().replace("(", " ").replace(")", " ").split()
        for token in tokens:
            if token in ["true", "false", "none"] or token.isdigit():
                continue
            if token in allowed_attributes:
                continue
            if token in allowed_operators:
                continue
            # Check if token is a string literal (in quotes)
            if (token.startswith('"') and token.endswith('"')) or (
                token.startswith("'") and token.endswith("'")
            ):
                continue
            # Check if token is a valid Python identifier (for future extensibility)
            if token.isidentifier():
                # Only allow specific identifiers
                if token not in ["level", "status", "artifact_type"]:
                    raise ValueError(f"Unknown identifier in source condition: {token}")

        return v
