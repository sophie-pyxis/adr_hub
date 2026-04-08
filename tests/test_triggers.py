"""
Test trigger service for unified artifact model.

PHASE 4: Trigger Service
- Business logic for evaluating trigger conditions
- Auto-creation of artifacts based on trigger rules
- Integration with artifact service
- Safe evaluation of condition expressions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session, select
from datetime import datetime

from src.models.trigger_rule import TriggerRule, TriggerRuleCreate
from src.models.artifact import Artifact, ArtifactCreate
from src.models.squad import Squad
from src.services.trigger_service import TriggerService
from src.services.artifact_service import ArtifactService


def test_trigger_service_initialization():
    """Test TriggerService initialization."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    assert service.session == mock_session
    assert service.artifact_service == mock_artifact_service


def test_get_rules_for_source_type():
    """Test retrieving trigger rules for a source artifact type."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    # Mock database query
    mock_rules = [
        TriggerRule(
            id=1,
            source_type="adr",
            source_condition="level >= 4",
            target_type="governance",
            auto_create=True,
            required=True,
            description="ADR level 4+ requires governance artifact"
        ),
        TriggerRule(
            id=2,
            source_type="adr",
            source_condition="status == 'accepted'",
            target_type="implementation",
            auto_create=False,
            required=False,
            description="Accepted ADRs may need implementation artifact"
        )
    ]

    mock_session.exec.return_value.all.return_value = mock_rules

    rules = service.get_rules_for_source_type("adr")

    mock_session.exec.assert_called_once()
    assert len(rules) == 2
    assert rules[0].source_type == "adr"
    assert rules[1].source_type == "adr"


def test_get_rules_for_source_type_no_rules():
    """Test retrieving trigger rules when no rules exist."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    mock_session.exec.return_value.all.return_value = []

    rules = service.get_rules_for_source_type("nonexistent_type")

    assert len(rules) == 0


def test_evaluate_condition_simple():
    """Test evaluating a simple condition."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    # Test artifact
    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="proposed",
        level=3,
        content="Test content",
        squad_id=1
    )

    # Simple condition
    condition = "level >= 3"
    result = service.evaluate_condition(artifact, condition)

    assert result == True

    # Test false condition
    condition2 = "level < 2"
    result2 = service.evaluate_condition(artifact, condition2)

    assert result2 == False


def test_evaluate_condition_complex():
    """Test evaluating a complex condition with multiple operators."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Complex condition
    condition = "level >= 4 and status == 'accepted'"
    result = service.evaluate_condition(artifact, condition)

    assert result == True

    # False complex condition
    condition2 = "level >= 5 or status == 'rejected'"
    result2 = service.evaluate_condition(artifact, condition2)

    assert result2 == False


def test_evaluate_condition_with_string_literal():
    """Test evaluating condition with string literal."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        artifact_type="rfc",
        artifact_number="RFC-2024-001",
        title="Test RFC",
        status="proposed",
        content="Test content",
        squad_id=1
    )

    condition = "status == 'proposed'"
    result = service.evaluate_condition(artifact, condition)

    assert result == True

    # Test with double quotes
    condition2 = 'status == "proposed"'
    result2 = service.evaluate_condition(artifact, condition2)

    assert result2 == True


def test_evaluate_condition_invalid_attribute():
    """Test evaluating condition with invalid attribute (should return False)."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="proposed",
        level=3,
        content="Test content",
        squad_id=1
    )

    # Invalid attribute (should be caught by safe evaluation)
    condition = "invalid_attr == 'value'"
    result = service.evaluate_condition(artifact, condition)

    # Should return False for safety
    assert result == False


def test_evaluate_condition_malformed():
    """Test evaluating malformed condition (should return False)."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="proposed",
        level=3,
        content="Test content",
        squad_id=1
    )

    # Malformed condition
    condition = "level >= "  # Incomplete expression
    result = service.evaluate_condition(artifact, condition)

    # Should return False for safety
    assert result == False


def test_check_triggers_for_artifact():
    """Test checking all triggers for an artifact."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Mock rules
    mock_rules = [
        TriggerRule(
            id=1,
            source_type="adr",
            source_condition="level >= 4",
            target_type="governance",
            auto_create=True,
            required=True,
            description="ADR level 4+ requires governance artifact"
        ),
        TriggerRule(
            id=2,
            source_type="adr",
            source_condition="status == 'rejected'",
            target_type="evidence",
            auto_create=False,
            required=False,
            description="Rejected ADRs may need evidence"
        )
    ]

    with patch.object(service, 'get_rules_for_source_type', return_value=mock_rules):
        with patch.object(service, 'evaluate_condition', side_effect=[True, False]):
            triggers = service.check_triggers_for_artifact(artifact)

    assert len(triggers) == 2
    assert triggers[0]["rule"].id == 1
    assert triggers[0]["condition_met"] == True
    assert triggers[0]["auto_create"] == True
    assert triggers[0]["required"] == True
    assert triggers[1]["rule"].id == 2
    assert triggers[1]["condition_met"] == False
    assert triggers[1]["auto_create"] == False
    assert triggers[1]["required"] == False


def test_check_triggers_for_artifact_no_matches():
    """Test checking triggers when no conditions are met."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        artifact_type="rfc",
        artifact_number="RFC-2024-001",
        title="Test RFC",
        status="proposed",
        content="Test content",
        squad_id=1
    )

    mock_rules = [
        TriggerRule(
            id=1,
            source_type="rfc",
            source_condition="status == 'accepted'",
            target_type="implementation",
            auto_create=False,
            required=False,
            description="Accepted RFCs may need implementation"
        )
    ]

    with patch.object(service, 'get_rules_for_source_type', return_value=mock_rules):
        with patch.object(service, 'evaluate_condition', return_value=False):
            triggers = service.check_triggers_for_artifact(artifact)

    assert len(triggers) == 1
    assert triggers[0]["rule"].id == 1
    assert triggers[0]["condition_met"] == False
    assert triggers[0]["auto_create"] == False
    assert triggers[0]["required"] == False


def test_create_target_artifact_auto():
    """Test auto-creating target artifact when condition is met."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    source_artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    trigger_rule = TriggerRule(
        id=1,
        source_type="adr",
        source_condition="level >= 4",
        target_type="governance",
        auto_create=True,
        required=True,
        description="ADR level 4+ requires governance artifact"
    )

    # Mock artifact creation
    mock_created_artifact = Artifact(
        id=2,
        artifact_type="governance",
        artifact_number="GOV-2024-001",
        title="Governance for Test ADR",
        status="proposed",
        content="Auto-generated governance artifact",
        squad_id=1,
        triggered_by_id=1,
        trigger_reason="Auto-created by trigger rule: ADR level 4+ requires governance artifact"
    )

    mock_artifact_service.create_artifact.return_value = mock_created_artifact

    result = service.create_target_artifact(source_artifact, trigger_rule)

    # Verify artifact service was called with correct parameters
    mock_artifact_service.create_artifact.assert_called_once()
    call_args = mock_artifact_service.create_artifact.call_args

    artifact_data = call_args[0][0]  # First positional argument (ArtifactCreate)
    assert artifact_data.artifact_type == "governance"
    assert artifact_data.title == "Governance for Test ADR"
    assert artifact_data.squad_id == 1
    assert artifact_data.triggered_by_id == 1
    assert "Auto-created by trigger rule" in artifact_data.trigger_reason

    assert result == mock_created_artifact


def test_create_target_artifact_not_auto():
    """Test handling trigger rule with auto_create=False."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    source_artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=3,
        content="Test content",
        squad_id=1
    )

    trigger_rule = TriggerRule(
        id=1,
        source_type="adr",
        source_condition="level >= 3",
        target_type="rfc",
        auto_create=False,
        required=False,
        description="ADR level 3+ may need RFC"
    )

    result = service.create_target_artifact(source_artifact, trigger_rule)

    # Should not call artifact service when auto_create is False
    mock_artifact_service.create_artifact.assert_not_called()
    assert result is None


def test_process_artifact_triggers():
    """Test processing all triggers for an artifact (full integration)."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Mock rules
    mock_rules = [
        TriggerRule(
            id=1,
            source_type="adr",
            source_condition="level >= 4",
            target_type="governance",
            auto_create=True,
            required=True,
            description="ADR level 4+ requires governance artifact"
        ),
        TriggerRule(
            id=2,
            source_type="adr",
            source_condition="status == 'accepted'",
            target_type="implementation",
            auto_create=True,
            required=False,
            description="Accepted ADRs may need implementation"
        )
    ]

    # Mock created artifacts
    mock_governance_artifact = Artifact(
        id=2,
        artifact_type="governance",
        artifact_number="GOV-2024-001",
        title="Governance for Test ADR",
        status="proposed",
        content="Auto-generated governance artifact",
        squad_id=1
    )

    mock_implementation_artifact = Artifact(
        id=3,
        artifact_type="implementation",
        artifact_number="IMP-001",
        title="Implementation for Test ADR",
        status="proposed",
        content="Auto-generated implementation artifact",
        squad_id=1
    )

    with patch.object(service, 'check_triggers_for_artifact', return_value=[
        {"rule": mock_rules[0], "condition_met": True, "auto_create": True, "required": True},
        {"rule": mock_rules[1], "condition_met": True, "auto_create": True, "required": False}
    ]):
        with patch.object(service, 'create_target_artifact', side_effect=[
            mock_governance_artifact, mock_implementation_artifact
        ]):
            results = service.process_artifact_triggers(artifact)

    assert len(results) == 2
    assert results[0].artifact_type == "governance"
    assert results[1].artifact_type == "implementation"


def test_process_artifact_triggers_no_auto_create():
    """Test processing triggers where auto_create is False."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    mock_rules = [
        TriggerRule(
            id=1,
            source_type="adr",
            source_condition="level >= 4",
            target_type="governance",
            auto_create=False,
            required=True,
            description="ADR level 4+ requires governance artifact"
        )
    ]

    with patch.object(service, 'check_triggers_for_artifact', return_value=[
        {"rule": mock_rules[0], "condition_met": True, "auto_create": False, "required": True}
    ]):
        results = service.process_artifact_triggers(artifact)

    # Should return empty list when no auto_create
    assert len(results) == 0


def test_process_artifact_triggers_condition_not_met():
    """Test processing triggers where condition is not met."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="proposed",
        level=2,
        content="Test content",
        squad_id=1
    )

    mock_rules = [
        TriggerRule(
            id=1,
            source_type="adr",
            source_condition="level >= 4",
            target_type="governance",
            auto_create=True,
            required=True,
            description="ADR level 4+ requires governance artifact"
        )
    ]

    with patch.object(service, 'check_triggers_for_artifact', return_value=[]):
        results = service.process_artifact_triggers(artifact)

    assert len(results) == 0


def test_validate_required_triggers_all_met():
    """Test validating required triggers when all are met."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Mock triggers with one required and met
    mock_triggers = [
        {
            "rule": TriggerRule(
                id=1,
                source_type="adr",
                source_condition="level >= 4",
                target_type="governance",
                auto_create=True,
                required=True,
                description="ADR level 4+ requires governance artifact"
            ),
            "condition_met": True,
            "auto_create": True,
            "required": True
        }
    ]

    with patch.object(service, 'check_triggers_for_artifact', return_value=mock_triggers):
        # This should not raise an exception
        service.validate_required_triggers(artifact)


def test_validate_required_triggers_not_met():
    """Test validating required triggers when one is not met."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Mock triggers with one required but condition not met
    mock_triggers = [
        {
            "rule": TriggerRule(
                id=1,
                source_type="adr",
                source_condition="level >= 5",
                target_type="governance",
                auto_create=True,
                required=True,
                description="ADR level 5 requires governance artifact"
            ),
            "condition_met": False,
            "auto_create": True,
            "required": True
        }
    ]

    with patch.object(service, 'check_triggers_for_artifact', return_value=mock_triggers):
        with pytest.raises(ValueError, match="Required trigger not satisfied"):
            service.validate_required_triggers(artifact)


def test_validate_required_triggers_no_required():
    """Test validating triggers when no required triggers exist."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Mock triggers with none required
    mock_triggers = [
        {
            "rule": TriggerRule(
                id=1,
                source_type="adr",
                source_condition="level >= 4",
                target_type="governance",
                auto_create=True,
                required=False,
                description="ADR level 4+ suggests governance artifact"
            ),
            "condition_met": True,
            "auto_create": True,
            "required": False
        }
    ]

    with patch.object(service, 'check_triggers_for_artifact', return_value=mock_triggers):
        # This should not raise an exception even if condition not met
        service.validate_required_triggers(artifact)


def test_get_trigger_suggestions():
    """Test getting trigger suggestions for an artifact."""
    mock_session = Mock()
    mock_artifact_service = Mock()

    service = TriggerService(mock_session, mock_artifact_service)

    artifact = Artifact(
        id=1,
        artifact_type="adr",
        artifact_number="ADR-001-001",
        title="Test ADR",
        status="accepted",
        level=4,
        content="Test content",
        squad_id=1
    )

    # Mock rules
    mock_rules = [
        TriggerRule(
            id=1,
            source_type="adr",
            source_condition="level >= 4",
            target_type="governance",
            auto_create=True,
            required=True,
            description="ADR level 4+ requires governance artifact"
        ),
        TriggerRule(
            id=2,
            source_type="adr",
            source_condition="status == 'accepted'",
            target_type="implementation",
            auto_create=False,
            required=False,
            description="Accepted ADRs may need implementation artifact"
        ),
        TriggerRule(
            id=3,
            source_type="adr",
            source_condition="level >= 5",
            target_type="uncommon",
            auto_create=False,
            required=False,
            description="ADR level 5 may need uncommon artifact"
        )
    ]

    with patch.object(service, 'get_rules_for_source_type', return_value=mock_rules):
        with patch.object(service, 'evaluate_condition', side_effect=[True, True, False]):
            suggestions = service.get_trigger_suggestions(artifact)

    assert len(suggestions) == 2
    assert suggestions[0]["rule"].id == 1
    assert suggestions[0]["condition_met"] == True
    assert suggestions[1]["rule"].id == 2
    assert suggestions[1]["condition_met"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])