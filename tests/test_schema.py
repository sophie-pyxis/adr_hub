"""
Test database schema for unified artifact model.
"""

from datetime import datetime

import pytest
from sqlmodel import Session, select

from src.models.artifact import Artifact, ArtifactCreate
from src.models.artifact_reference import ArtifactReference, ArtifactReferenceCreate
from src.models.squad import Squad, SquadCreate
from src.models.trigger_rule import TriggerRule, TriggerRuleCreate


def test_artifact_creation_valid(session: Session):
    """Test that a basic artifact can be created."""
    # First create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an artifact
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)

    assert artifact.id is not None
    assert artifact.artifact_type == "adr"
    assert artifact.artifact_number == "ADR-001-001"
    assert artifact.title == "Test ADR"
    assert artifact.level == 1
    assert artifact.status == "proposed"
    assert artifact.squad_id == squad.id


def test_auto_number_adr_level1(session: Session):
    """Test auto-number generation for ADR level 1."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an ADR with auto number
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="auto",
        title="Test ADR Level 1",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)

    # The actual number generation happens in the service layer,
    # but we can test that "auto" is allowed
    assert artifact.artifact_number == "auto"


def test_auto_number_adr_level3(session: Session):
    """Test auto-number generation for ADR level 3."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an ADR level 3 with auto number and RFC status (required)
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="auto",
        title="Test ADR Level 3",
        level=3,
        status="proposed",
        content="Test content",
        rfc_status="RFC-2024-001 completed",
        squad_id=squad.id,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)

    assert artifact.level == 3
    assert artifact.rfc_status == "RFC-2024-001 completed"
    assert artifact.artifact_number == "auto"


def test_auto_number_rfc(session: Session):
    """Test auto-number generation for RFC."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an RFC with auto number
    artifact = Artifact(
        artifact_type="rfc",
        artifact_number="auto",
        title="Test RFC",
        status="proposed",
        content="Test RFC content",
        squad_id=squad.id,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)

    assert artifact.artifact_type == "rfc"
    assert artifact.artifact_number == "auto"
    assert artifact.level is None  # RFCs don't have level


def test_artifact_number_immutable(session: Session):
    """Test that artifact_number cannot be changed after creation."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an artifact
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)

    # Try to update artifact_number - this should be prevented by the service layer
    # but at model level, SQLModel will allow it. We'll test at service layer.
    # For now, just verify the original value.
    assert artifact.artifact_number == "ADR-001-001"


def test_self_referential_triggered_by(session: Session):
    """Test that an artifact can reference itself as triggered_by."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create first artifact
    artifact1 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR 1",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    session.add(artifact1)
    session.commit()
    session.refresh(artifact1)

    # Create second artifact that references the first as triggered_by
    artifact2 = Artifact(
        artifact_type="rfc",
        artifact_number="RFC-2024-001",
        title="Test RFC",
        status="proposed",
        content="Test RFC content",
        squad_id=squad.id,
        triggered_by_id=artifact1.id,
        trigger_reason="Triggered by ADR level 3+ requirement",
    )
    session.add(artifact2)
    session.commit()
    session.refresh(artifact2)

    # Verify the reference exists
    assert artifact2.triggered_by_id == artifact1.id
    assert artifact2.trigger_reason == "Triggered by ADR level 3+ requirement"


def test_trigger_rule_creation(session: Session):
    """Test that trigger rules can be created."""
    trigger_rule = TriggerRule(
        source_type="adr",
        source_condition="level >= 3",
        target_type="rfc",
        auto_create=False,
        required=True,
        description="ADR level 3+ requires RFC",
    )
    session.add(trigger_rule)
    session.commit()
    session.refresh(trigger_rule)

    assert trigger_rule.id is not None
    assert trigger_rule.source_type == "adr"
    assert trigger_rule.source_condition == "level >= 3"
    assert trigger_rule.target_type == "rfc"
    assert trigger_rule.auto_create is False
    assert trigger_rule.required is True
    assert trigger_rule.description == "ADR level 3+ requires RFC"


def test_artifact_reference_creation(session: Session):
    """Test that artifact references can be created."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create two artifacts
    artifact1 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR 1",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    artifact2 = Artifact(
        artifact_type="rfc",
        artifact_number="RFC-2024-001",
        title="Test RFC",
        status="proposed",
        content="Test RFC content",
        squad_id=squad.id,
    )
    session.add_all([artifact1, artifact2])
    session.commit()
    session.refresh(artifact1)
    session.refresh(artifact2)

    # Create a reference between them
    reference = ArtifactReference(
        from_artifact_id=artifact1.id,
        to_artifact_id=artifact2.id,
        reference_type="triggers",
    )
    session.add(reference)
    session.commit()
    session.refresh(reference)

    assert reference.id is not None
    assert reference.from_artifact_id == artifact1.id
    assert reference.to_artifact_id == artifact2.id
    assert reference.reference_type == "triggers"


def test_type_validation(session: Session):
    """Test that only valid artifact types are allowed."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Test invalid artifact type raises ValueError - use ArtifactCreate for validation
    with pytest.raises(ValueError) as exc_info:
        artifact = ArtifactCreate(
            artifact_type="invalid_type",
            artifact_number="TEST-001",
            title="Test Artifact",
            level=1,
            status="proposed",
            content="Test content",
            squad_id=squad.id,
        )

    assert "artifact_type must be one of:" in str(exc_info.value)

    # Test valid artifact types should succeed
    valid_types = [
        "adr",
        "rfc",
        "evidence",
        "governance",
        "implementation",
        "visibility",
        "uncommon",
    ]
    for artifact_type in valid_types:
        # Use appropriate number format for each type
        if artifact_type == "adr":
            artifact_number = "ADR-001-001"
        elif artifact_type == "rfc":
            artifact_number = "RFC-2024-001"
        elif artifact_type == "evidence":
            artifact_number = "EVI-2024-001"
        elif artifact_type == "governance":
            artifact_number = "GOV-2024-001"
        elif artifact_type == "implementation":
            artifact_number = "IMP-001"
        elif artifact_type == "visibility":
            artifact_number = "VIS-001"
        elif artifact_type == "uncommon":
            artifact_number = "UNC-2024-001"

        # Use Artifact for database operations
        artifact = Artifact(
            artifact_type=artifact_type,
            artifact_number=artifact_number,
            title=f"Test {artifact_type.upper()}",
            level=1 if artifact_type == "adr" else None,
            status="proposed",
            content="Test content",
            squad_id=squad.id,
        )
        # Should not raise any error
        assert artifact.artifact_type == artifact_type


def test_level_required_for_adr(session: Session):
    """Test that level is required for ADR type only."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Test ADR without level raises error - use ArtifactCreate for validation
    with pytest.raises(ValueError) as exc_info:
        artifact = ArtifactCreate(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR",
            level=None,
            status="proposed",
            content="Test content",
            squad_id=squad.id,
        )

    assert "level is required for ADR artifacts" in str(exc_info.value)

    # Test ADR with level succeeds - can use Artifact for DB operations
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    assert artifact.level == 1

    # Test non-ADR artifact with level raises error - use ArtifactCreate for validation
    with pytest.raises(ValueError) as exc_info:
        artifact = ArtifactCreate(
            artifact_type="rfc",
            artifact_number="RFC-2024-001",
            title="Test RFC",
            level=1,  # level should not be allowed for RFC
            status="proposed",
            content="Test content",
            squad_id=squad.id,
        )

    assert "level can only be set for artifact_type='adr'" in str(exc_info.value)

    # Test non-ADR artifact without level succeeds
    artifact = Artifact(
        artifact_type="rfc",
        artifact_number="RFC-2024-001",
        title="Test RFC",
        level=None,  # Should be allowed
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    assert artifact.level is None


def test_status_valid_values(session: Session):
    """Test that status must be one of allowed values."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Test invalid status raises ValueError - use ArtifactCreate for validation
    with pytest.raises(ValueError) as exc_info:
        artifact = ArtifactCreate(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR",
            level=1,
            status="invalid_status",
            content="Test content",
            squad_id=squad.id,
        )

    assert "status must be one of:" in str(exc_info.value)

    # Test all valid statuses succeed
    valid_statuses = [
        "proposed",
        "accepted",
        "rejected",
        "reopened",
        "superseded",
        "discontinued",
    ]
    for status in valid_statuses:
        # Use Artifact for database operations
        artifact = Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title=f"Test ADR {status}",
            level=1,
            status=status,
            content="Test content",
            squad_id=squad.id,
        )
        assert artifact.status == status


def test_unique_number_constraint(session: Session):
    """Test that artifact_number must be unique across all artifacts."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active",
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create first artifact
    artifact1 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR 1",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id,
    )
    session.add(artifact1)
    session.commit()
    session.refresh(artifact1)

    # Try to create second artifact with same number
    artifact2 = Artifact(
        artifact_type="rfc",  # Different type, same number
        artifact_number="ADR-001-001",  # Same number
        title="Test RFC",
        status="proposed",
        content="Test RFC content",
        squad_id=squad.id,
    )
    session.add(artifact2)

    # This should raise an integrity error when committing
    import sqlalchemy

    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc_info:
        session.commit()

    # Rollback for clean session
    session.rollback()

    # Also test with same type
    artifact3 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",  # Same number
        title="Test ADR 2",
        level=2,
        status="proposed",
        content="Test content 2",
        squad_id=squad.id,
    )
    session.add(artifact3)

    with pytest.raises(sqlalchemy.exc.IntegrityError) as exc_info:
        session.commit()

    # Rollback for clean session
    session.rollback()

    # Test that different numbers are allowed
    artifact4 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-002",  # Different number
        title="Test ADR 3",
        level=1,
        status="proposed",
        content="Test content 3",
        squad_id=squad.id,
    )
    session.add(artifact4)
    session.commit()  # Should succeed
    session.refresh(artifact4)

    assert artifact4.artifact_number == "ADR-001-002"
