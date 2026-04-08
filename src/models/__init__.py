"""
SQLModel models for AI Architecture Governance System.
"""

from .squad import Squad, SquadCreate, SquadUpdate, SquadRead
from .artifact import Artifact, ArtifactCreate, ArtifactUpdate, ArtifactStatusUpdate, ArtifactRead
from .trigger_rule import TriggerRule, TriggerRuleCreate, TriggerRuleRead
from .artifact_reference import ArtifactReference, ArtifactReferenceCreate, ArtifactReferenceRead

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
    "ArtifactReferenceRead"
]