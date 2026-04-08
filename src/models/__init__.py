"""
SQLModel models for AI Architecture Governance System.
"""

from .artifact import (
    Artifact,
    ArtifactCreate,
    ArtifactRead,
    ArtifactStatusUpdate,
    ArtifactUpdate,
)
from .artifact_reference import (
    ArtifactReference,
    ArtifactReferenceCreate,
    ArtifactReferenceRead,
)
from .squad import Squad, SquadCreate, SquadRead, SquadUpdate
from .trigger_rule import TriggerRule, TriggerRuleCreate, TriggerRuleRead

__all__ = [
    "Squad",
    "SquadCreate",
    "SquadUpdate",
    "SquadRead",
    "Artifact",
    "ArtifactCreate",
    "ArtifactUpdate",
    "ArtifactStatusUpdate",
    "ArtifactRead",
    "TriggerRule",
    "TriggerRuleCreate",
    "TriggerRuleRead",
    "ArtifactReference",
    "ArtifactReferenceCreate",
    "ArtifactReferenceRead",
]
