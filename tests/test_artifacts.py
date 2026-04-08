"""
Test artifact service for unified artifact model.

PHASE 3: Artifact Service
- Business logic for artifact CRUD operations
- Integration with template and markdown generation services
- Auto-number generation for all artifact types
- Validation and schema matching
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session, select
from datetime import datetime

from src.models.artifact import Artifact, ArtifactCreate, ArtifactUpdate, ArtifactStatusUpdate, ArtifactRead
from src.models.squad import Squad
from src.services.artifact_service import ArtifactService
from src.services.template_service import TemplateService


def test_artifact_service_initialization():
    """Test ArtifactService initialization with dependencies."""
    # Test with default dependencies
    service = ArtifactService()
    assert isinstance(service.template_service, TemplateService)

    # Test with custom template service
    mock_template = Mock(spec=TemplateService)
    service = ArtifactService(template_service=mock_template)
    assert service.template_service == mock_template


def test_generate_artifact_number_adr_level1(session: Session):
    """Test auto-number generation for ADR level 1."""
    # Create a squad first
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create some existing ADRs
    artifact1 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR 1",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    artifact2 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-003",  # Gap in numbering
        title="Test ADR 2",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add_all([artifact1, artifact2])
    session.commit()

    service = ArtifactService(session=session)

    # Generate next number for level 1
    next_number = service._generate_artifact_number("adr", 1, squad.id, session)

    # Should be ADR-001-004 (next after 003)
    assert next_number == "ADR-001-004"


def test_generate_artifact_number_adr_level3(session: Session):
    """Test auto-number generation for ADR level 3."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create existing level 3 ADRs
    artifact1 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-003-001",
        title="Test ADR Level 3-1",
        level=3,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    artifact2 = Artifact(
        artifact_type="adr",
        artifact_number="ADR-003-005",  # Gap
        title="Test ADR Level 3-2",
        level=3,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add_all([artifact1, artifact2])
    session.commit()

    service = ArtifactService(session=session)

    # Generate next number for level 3
    next_number = service._generate_artifact_number("adr", 3, squad.id, session)

    # Should be ADR-003-006 (next after 005)
    assert next_number == "ADR-003-006"


def test_generate_artifact_number_rfc(session: Session):
    """Test auto-number generation for RFC (year-based)."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    current_year = datetime.now().year

    # Create existing RFCs for current year
    artifact1 = Artifact(
        artifact_type="rfc",
        artifact_number=f"RFC-{current_year}-001",
        title="Test RFC 1",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    artifact2 = Artifact(
        artifact_type="rfc",
        artifact_number=f"RFC-{current_year}-005",  # Gap
        title="Test RFC 2",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add_all([artifact1, artifact2])
    session.commit()

    service = ArtifactService(session=session)

    # Generate next RFC number
    next_number = service._generate_artifact_number("rfc", None, squad.id, session)

    # Should be RFC-{year}-006 (next after 005)
    assert next_number == f"RFC-{current_year}-006"


def test_generate_artifact_number_evidence(session: Session):
    """Test auto-number generation for evidence."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    current_year = datetime.now().year

    # Create existing evidence
    artifact1 = Artifact(
        artifact_type="evidence",
        artifact_number=f"EVI-{current_year}-001",
        title="Test Evidence 1",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact1)
    session.commit()

    service = ArtifactService(session=session)

    # Generate next evidence number
    next_number = service._generate_artifact_number("evidence", None, squad.id, session)

    # Should be EVI-{year}-002
    assert next_number == f"EVI-{current_year}-002"


def test_create_artifact_with_auto_number(session: Session):
    """Test creating artifact with auto-number generation."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Mock template validation and content generation
    mock_template = Mock(spec=TemplateService)
    mock_template.validate_artifact_against_template.return_value = None
    mock_template.generate_content_for_artifact.return_value = "# Test ADR\n\nGenerated content"

    service = ArtifactService(
        session=session,
        template_service=mock_template,
    )

    # Create artifact data
    artifact_data = ArtifactCreate(
        artifact_type="adr",
        artifact_number="auto",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )

    # Create artifact
    result = service.create_artifact(artifact_data)

    assert isinstance(result, ArtifactRead)
    assert result.artifact_type == "adr"
    assert result.title == "Test ADR"
    assert result.squad_name == "Test Squad"
    assert result.artifact_number != "auto"  # Should be generated
    assert "ADR-001-" in result.artifact_number

    # Verify template service was called
    mock_template.validate_artifact_against_template.assert_called_once()
    mock_template.generate_content_for_artifact.assert_called_once()



def test_create_artifact_with_manual_number(session: Session):
    """Test creating artifact with manual number."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Mock dependencies
    mock_template = Mock(spec=TemplateService)
    mock_template.validate_artifact_against_template.return_value = None
    mock_template.generate_content_for_artifact.return_value = "# Test RFC\n\nGenerated content"

    service = ArtifactService(
        session=session,
        template_service=mock_template,
    )

    # Create RFC with manual number
    artifact_data = ArtifactCreate(
        artifact_type="rfc",
        artifact_number="RFC-2024-123",
        title="Test RFC",
        status="proposed",
        content="Test RFC content",
        squad_id=squad.id
    )

    result = service.create_artifact(artifact_data)

    assert result.artifact_number == "RFC-2024-123"
    assert result.artifact_type == "rfc"
    assert result.squad_name == "Test Squad"


def test_create_artifact_duplicate_number(session: Session):
    """Test creating artifact with duplicate number fails."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create existing artifact
    existing = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Existing ADR",
        level=1,
        status="proposed",
        content="Existing content",
        squad_id=squad.id
    )
    session.add(existing)
    session.commit()

    service = ArtifactService(session=session)

    # Try to create artifact with same number
    artifact_data = ArtifactCreate(
        artifact_type="adr",
        artifact_number="ADR-001-001",  # Duplicate
        title="New ADR",
        level=1,
        status="proposed",
        content="New content",
        squad_id=squad.id
    )

    with pytest.raises(ValueError, match="already exists"):
        service.create_artifact(artifact_data)


def test_create_artifact_invalid_squad(session: Session):
    """Test creating artifact for non-existent squad fails."""
    service = ArtifactService(session=session)

    # Try to create artifact with invalid squad ID
    artifact_data = ArtifactCreate(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=999  # Non-existent squad
    )

    with pytest.raises(ValueError, match="not found"):
        service.create_artifact(artifact_data)


def test_create_artifact_inactive_squad(session: Session):
    """Test creating artifact for inactive squad fails."""
    # Create an inactive squad
    squad = Squad(
        squad_code="inactive-squad",
        name="Inactive Squad",
        tech_lead="Test Lead",
        status="inactive"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    service = ArtifactService(session=session)

    # Try to create artifact for inactive squad
    artifact_data = ArtifactCreate(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )

    with pytest.raises(ValueError, match="Cannot create artifact for squad with status"):
        service.create_artifact(artifact_data)


def test_get_artifact(session: Session):
    """Test retrieving artifact by number."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
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
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Get the artifact
    result = service.get_artifact("ADR-001-001")

    assert result is not None
    assert result.artifact_number == "ADR-001-001"
    assert result.title == "Test ADR"
    assert result.squad_name == "Test Squad"


def test_get_artifact_not_found(session: Session):
    """Test retrieving non-existent artifact returns None."""
    service = ArtifactService(session=session)

    result = service.get_artifact("NON-EXISTENT-001")

    assert result is None


def test_list_artifacts(session: Session):
    """Test listing artifacts with filtering."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create multiple artifacts
    artifacts = [
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR 1",
            level=1,
            status="proposed",
            content="Test content",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-002",
            title="Test ADR 2",
            level=2,
            status="accepted",
            content="Test content",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="rfc",
            artifact_number="RFC-2024-001",
            title="Test RFC",
            status="proposed",
            content="Test content",
            squad_id=squad.id
        ),
    ]
    session.add_all(artifacts)
    session.commit()

    service = ArtifactService(session=session)

    # List all artifacts
    all_artifacts = service.list_artifacts()
    assert len(all_artifacts) == 3

    # Filter by type
    adrs = service.list_artifacts(artifact_type="adr")
    assert len(adrs) == 2
    assert all(a.artifact_type == "adr" for a in adrs)

    # Filter by status
    proposed = service.list_artifacts(status="proposed")
    assert len(proposed) == 2  # ADR 1 and RFC

    # Filter by squad
    squad_filtered = service.list_artifacts(squad_id=squad.id)
    assert len(squad_filtered) == 3

    # Combined filters
    proposed_adrs = service.list_artifacts(artifact_type="adr", status="proposed")
    assert len(proposed_adrs) == 1
    assert proposed_adrs[0].artifact_number == "ADR-001-001"


def test_update_artifact(session: Session):
    """Test updating artifact fields."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an artifact
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Original Title",
        level=1,
        status="proposed",
        content="Original content",
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Update the artifact
    update_data = ArtifactUpdate(
        title="Updated Title",
        content="Updated content",
        level=2
    )

    result = service.update_artifact("ADR-001-001", update_data)

    assert result is not None
    assert result.title == "Updated Title"
    assert result.content == "Updated content"
    assert result.level == 2

    # Verify in database
    updated = session.get(Artifact, artifact.id)
    assert updated.title == "Updated Title"
    assert updated.updated_at is not None


def test_update_artifact_not_found(session: Session):
    """Test updating non-existent artifact returns None."""
    service = ArtifactService(session=session)

    update_data = ArtifactUpdate(title="Updated Title")
    result = service.update_artifact("NON-EXISTENT-001", update_data)

    assert result is None


def test_update_artifact_level_validation(session: Session):
    """Test validation when updating ADR level."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create a level 1 ADR
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Try to update to level 4 without required fields
    update_data = ArtifactUpdate(level=4)

    with pytest.raises(ValueError, match="tco_estimate is required for ADR level >= 4"):
        service.update_artifact("ADR-001-001", update_data)

    # Update with required fields
    update_data_with_fields = ArtifactUpdate(
        level=4,
        tco_estimate="100k USD",
        lgpd_analysis="GDPR compliant",
        health_compliance_impact="HIPAA compliant",
        rfc_status="RFC-2024-001 completed"
    )

    result = service.update_artifact("ADR-001-001", update_data_with_fields)
    assert result.level == 4
    assert result.tco_estimate == "100k USD"


def test_update_artifact_status(session: Session):
    """Test updating artifact status with validation."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
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
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Update status to accepted (valid transition)
    status_update = ArtifactStatusUpdate(status="accepted")
    result = service.update_artifact_status("ADR-001-001", status_update)

    assert result is not None
    assert result.status == "accepted"

    # Try invalid transition (accepted -> proposed)
    status_update_invalid = ArtifactStatusUpdate(status="proposed")
    with pytest.raises(ValueError, match="Cannot transition from"):
        service.update_artifact_status("ADR-001-001", status_update_invalid)


def test_search_artifacts(session: Session):
    """Test searching artifacts by title or content."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create artifacts with searchable content
    artifacts = [
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Database Migration",
            level=1,
            status="proposed",
            content="Migrate from MySQL to PostgreSQL",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="rfc",
            artifact_number="RFC-2024-001",
            title="API Design",
            status="proposed",
            content="Design REST API with PostgreSQL backend",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-002",
            title="Frontend Framework",
            level=2,
            status="accepted",
            content="Choose React for frontend",
            squad_id=squad.id
        ),
    ]
    session.add_all(artifacts)
    session.commit()

    service = ArtifactService(session=session)

    # Search for "PostgreSQL" - should match first two artifacts
    results = service.search_artifacts("PostgreSQL")
    assert len(results) == 2
    assert any(r.title == "Database Migration" for r in results)
    assert any(r.title == "API Design" for r in results)

    # Search for "React" - should match third artifact
    results = service.search_artifacts("React")
    assert len(results) == 1
    assert results[0].title == "Frontend Framework"

    # Search for "nonexistent" - should return empty
    results = service.search_artifacts("nonexistent")
    assert len(results) == 0



def test_generate_artifact_number_governance(session: Session):
    """Test auto-number generation for governance."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    current_year = datetime.now().year

    # Create existing governance artifact
    artifact1 = Artifact(
        artifact_type="governance",
        artifact_number=f"GOV-{current_year}-003",  # Gap
        title="Test Governance 1",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact1)
    session.commit()

    service = ArtifactService(session=session)

    # Generate next governance number
    next_number = service._generate_artifact_number("governance", None, squad.id, session)

    # Should be GOV-{year}-004 (next after 003)
    assert next_number == f"GOV-{current_year}-004"


def test_generate_artifact_number_implementation(session: Session):
    """Test auto-number generation for implementation."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create existing implementation artifacts
    artifact1 = Artifact(
        artifact_type="implementation",
        artifact_number="IMP-005",
        title="Test Implementation 1",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    artifact2 = Artifact(
        artifact_type="implementation",
        artifact_number="IMP-007",  # Gap
        title="Test Implementation 2",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add_all([artifact1, artifact2])
    session.commit()

    service = ArtifactService(session=session)

    # Generate next implementation number
    next_number = service._generate_artifact_number("implementation", None, squad.id, session)

    # Should be IMP-008 (next after 007)
    assert next_number == "IMP-008"


def test_generate_artifact_number_visibility(session: Session):
    """Test auto-number generation for visibility."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create existing visibility artifact
    artifact1 = Artifact(
        artifact_type="visibility",
        artifact_number="VIS-001",
        title="Test Visibility 1",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact1)
    session.commit()

    service = ArtifactService(session=session)

    # Generate next visibility number
    next_number = service._generate_artifact_number("visibility", None, squad.id, session)

    # Should be VIS-002
    assert next_number == "VIS-002"


def test_generate_artifact_number_uncommon(session: Session):
    """Test auto-number generation for uncommon."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    current_year = datetime.now().year

    # Create existing uncommon artifact
    artifact1 = Artifact(
        artifact_type="uncommon",
        artifact_number=f"UNC-{current_year}-010",
        title="Test Uncommon 1",
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact1)
    session.commit()

    service = ArtifactService(session=session)

    # Generate next uncommon number
    next_number = service._generate_artifact_number("uncommon", None, squad.id, session)

    # Should be UNC-{year}-011
    assert next_number == f"UNC-{current_year}-011"


def test_generate_artifact_number_invalid_type(session: Session):
    """Test auto-number generation for invalid artifact type."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    service = ArtifactService(session=session)

    # Try to generate number for invalid type
    with pytest.raises(ValueError, match="Unsupported artifact type"):
        service._generate_artifact_number("invalid_type", None, squad.id, session)


def test_update_artifact_comprehensive(session: Session):
    """Test comprehensive update artifact functionality."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create an artifact with various fields
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Original Title",
        level=1,
        status="proposed",
        content="Original content",
        squad_id=squad.id,
        tco_estimate="",
        lgpd_analysis="",
        health_compliance_impact="",
        rfc_status=""
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Test 1: Update basic fields
    update_data1 = ArtifactUpdate(
        title="Updated Title",
        content="Updated content",
        level=2
    )
    result1 = service.update_artifact("ADR-001-001", update_data1)
    assert result1.title == "Updated Title"
    assert result1.content == "Updated content"
    assert result1.level == 2

    # Test 2: Update ADR level to 3 (requires rfc_status)
    update_data2 = ArtifactUpdate(
        level=3,
        rfc_status="approved"
    )
    result2 = service.update_artifact("ADR-001-001", update_data2)
    assert result2.level == 3
    assert result2.rfc_status == "approved"

    # Test 3: Update ADR level to 4 (requires additional fields)
    update_data3 = ArtifactUpdate(
        level=4,
        tco_estimate="200k USD",
        lgpd_analysis="GDPR compliant updated",
        health_compliance_impact="HIPAA compliant updated"
    )
    result3 = service.update_artifact("ADR-001-001", update_data3)
    assert result3.level == 4
    assert result3.tco_estimate == "200k USD"
    assert result3.lgpd_analysis == "GDPR compliant updated"

    # Test 4: Try to update level to 4 without required fields (should succeed because fields already exist)
    update_data4 = ArtifactUpdate(level=4)
    result4 = service.update_artifact("ADR-001-001", update_data4)
    assert result4.level == 4
    # Fields should still exist from previous update
    assert result4.tco_estimate == "200k USD"
    assert result4.lgpd_analysis == "GDPR compliant updated"

    # Test 5: Update other fields when level >= 4 (validation)
    update_data5 = ArtifactUpdate(
        tco_estimate="",  # Try to clear required field
        health_compliance_impact=""
    )
    with pytest.raises(ValueError, match="tco_estimate cannot be empty for ADR level >= 4"):
        service.update_artifact("ADR-001-001", update_data5)


def test_update_artifact_status_superseded(session: Session):
    """Test updating artifact status to superseded with validation."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create original artifact (accepted status)
    original = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Original ADR",
        level=1,
        status="accepted",
        content="Original content",
        squad_id=squad.id
    )

    # Create superseding artifact
    superseding = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-002",
        title="Superseding ADR",
        level=1,
        status="proposed",
        content="Superseding content",
        squad_id=squad.id
    )

    session.add_all([original, superseding])
    session.commit()

    service = ArtifactService(session=session)

    # Update status to superseded with valid superseded_by
    status_update = ArtifactStatusUpdate(
        status="superseded",
        superseded_by="ADR-001-002"
    )
    result = service.update_artifact_status("ADR-001-001", status_update)
    assert result.status == "superseded"

    # Try to update to superseded with non-existent artifact
    # First need to accept the artifact before it can be superseded
    status_update_accept = ArtifactStatusUpdate(
        status="accepted"
    )
    service.update_artifact_status("ADR-001-002", status_update_accept)

    # Now try to update to superseded with non-existent artifact
    status_update_invalid = ArtifactStatusUpdate(
        status="superseded",
        superseded_by="NON-EXISTENT"
    )
    with pytest.raises(ValueError, match="not found for superseded_by"):
        service.update_artifact_status("ADR-001-002", status_update_invalid)


def test_update_artifact_status_rejected_with_reason(session: Session):
    """Test updating artifact status to rejected with reason."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create artifact in proposed status
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="proposed",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Update status to rejected with reason (should work, reason is stored in notes field if model supports it)
    status_update = ArtifactStatusUpdate(
        status="rejected",
        rejection_reason="Not aligned with strategy"
    )
    result = service.update_artifact_status("ADR-001-001", status_update)
    assert result.status == "rejected"
    # Note: rejection_reason might not be stored in current model


def test_update_artifact_status_terminal_states(session: Session):
    """Test that terminal states cannot be changed."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create artifact in superseded status (terminal)
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        level=1,
        status="superseded",
        content="Test content",
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Try to change from terminal state (should fail)
    status_update = ArtifactStatusUpdate(status="accepted")
    with pytest.raises(ValueError, match="Cannot transition from"):
        service.update_artifact_status("ADR-001-001", status_update)


def test_search_artifacts_with_type_filter(session: Session):
    """Test searching artifacts with artifact type filter."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create artifacts with searchable content
    artifacts = [
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Database ADR",
            level=1,
            status="proposed",
            content="Migrate database to PostgreSQL",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="rfc",
            artifact_number="RFC-2024-001",
            title="Database RFC",
            status="proposed",
            content="Design PostgreSQL schema",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-002",
            title="API ADR",
            level=2,
            status="accepted",
            content="Design REST API",
            squad_id=squad.id
        ),
    ]
    session.add_all(artifacts)
    session.commit()

    service = ArtifactService(session=session)

    # Search for "database" across all types
    results_all = service.search_artifacts("database")
    assert len(results_all) == 2
    assert any(r.title == "Database ADR" for r in results_all)
    assert any(r.title == "Database RFC" for r in results_all)

    # Search for "database" in ADRs only
    results_adr = service.search_artifacts("database", artifact_type="adr")
    assert len(results_adr) == 1
    assert results_adr[0].title == "Database ADR"
    assert results_adr[0].artifact_type == "adr"

    # Search for "database" in RFCs only
    results_rfc = service.search_artifacts("database", artifact_type="rfc")
    assert len(results_rfc) == 1
    assert results_rfc[0].title == "Database RFC"
    assert results_rfc[0].artifact_type == "rfc"

    # Search for "PostgreSQL" across all types
    results_pg = service.search_artifacts("PostgreSQL")
    assert len(results_pg) == 2

    # Test case-insensitive search
    results_lower = service.search_artifacts("postgresql")
    assert len(results_lower) == 2


def test_search_artifacts_pagination(session: Session):
    """Test search artifacts with pagination."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create many artifacts with searchable content
    artifacts = []
    for i in range(15):
        artifact = Artifact(
            artifact_type="adr",
            artifact_number=f"ADR-001-{i+1:03d}",
            title=f"Test ADR {i+1}",
            level=1,
            status="proposed",
            content=f"Content for ADR {i+1} with search term",
            squad_id=squad.id
        )
        artifacts.append(artifact)
    session.add_all(artifacts)
    session.commit()

    service = ArtifactService(session=session)

    # Search with limit
    results_limit = service.search_artifacts("search term", limit=5)
    assert len(results_limit) == 5

    # Search with skip and limit
    results_skip = service.search_artifacts("search term", skip=5, limit=5)
    assert len(results_skip) == 5
    # Should be different results than first page
    numbers_first = {r.artifact_number for r in results_limit}
    numbers_second = {r.artifact_number for r in results_skip}
    assert numbers_first.isdisjoint(numbers_second)


def test_get_artifact_by_id(session: Session):
    """Test retrieving artifact by ID."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
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
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)  # Get the ID

    service = ArtifactService(session=session)

    # Get artifact by ID
    result = service.get_artifact_by_id(artifact.id)
    assert result is not None
    assert result.id == artifact.id
    assert result.artifact_number == "ADR-001-001"
    assert result.squad_name == "Test Squad"

    # Get non-existent artifact
    result_none = service.get_artifact_by_id(999)
    assert result_none is None


def test_delete_artifact(session: Session):
    """Test deleting an artifact."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
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
        squad_id=squad.id
    )
    session.add(artifact)
    session.commit()

    service = ArtifactService(session=session)

    # Delete the artifact
    deleted = service.delete_artifact("ADR-001-001")
    assert deleted is True

    # Verify artifact is gone
    result = service.get_artifact("ADR-001-001")
    assert result is None

    # Try to delete non-existent artifact
    deleted_none = service.delete_artifact("NON-EXISTENT")
    assert deleted_none is False


def test_get_artifact_counts(session: Session):
    """Test getting artifact counts and statistics."""
    # Create a squad
    squad = Squad(
        squad_code="test-squad",
        name="Test Squad",
        tech_lead="Test Lead",
        status="active"
    )
    session.add(squad)
    session.commit()
    session.refresh(squad)

    # Create artifacts of different types and statuses
    artifacts = [
        # ADRs
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="ADR 1",
            level=1,
            status="proposed",
            content="Content",
            squad_id=squad.id
        ),
        Artifact(
            artifact_type="adr",
            artifact_number="ADR-001-002",
            title="ADR 2",
            level=2,
            status="accepted",
            content="Content",
            squad_id=squad.id
        ),
        # RFCs
        Artifact(
            artifact_type="rfc",
            artifact_number="RFC-2024-001",
            title="RFC 1",
            status="proposed",
            content="Content",
            squad_id=squad.id
        ),
        # Evidence
        Artifact(
            artifact_type="evidence",
            artifact_number="EVI-2024-001",
            title="Evidence 1",
            status="accepted",
            content="Content",
            squad_id=squad.id
        ),
        # Implementation
        Artifact(
            artifact_type="implementation",
            artifact_number="IMP-001",
            title="Implementation 1",
            status="proposed",
            content="Content",
            squad_id=squad.id
        ),
    ]
    session.add_all(artifacts)
    session.commit()

    service = ArtifactService(session=session)

    counts = service.get_artifact_counts()

    assert counts["total"] == 5
    assert counts["by_type"]["adr"] == 2
    assert counts["by_type"]["rfc"] == 1
    assert counts["by_type"]["evidence"] == 1
    assert counts["by_type"]["implementation"] == 1
    assert "governance" not in counts["by_type"]  # No governance artifacts
    assert counts["by_status"]["proposed"] == 3  # ADR 1, RFC 1, IMP 1
    assert counts["by_status"]["accepted"] == 2  # ADR 2, Evidence 1
    assert "rejected" not in counts["by_status"]  # No rejected artifacts


def test_get_artifact_counts_empty(session: Session):
    """Test getting artifact counts when no artifacts exist."""
    service = ArtifactService(session=session)

    counts = service.get_artifact_counts()

    assert counts["total"] == 0
    assert counts["by_type"] == {}
    assert counts["by_status"] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])