"""
Test template service for unified artifact model.

PHASE 2: Template Service
- Templates for 6 missing artifact types: evidence, governance, implementation, visibility, uncommon
- Template placeholder substitution system
- Template validation and schema matching
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

from src.services.template_service import TemplateService, TemplateValidationError
from src.models.artifact import ArtifactCreate


def test_template_service_initialization():
    """Test TemplateService initialization with default and custom paths."""
    # Test with default path
    service = TemplateService()
    assert service.templates_dir == Path("templates")

    # Test with custom path
    custom_path = Path("/custom/templates")
    service = TemplateService(templates_dir=custom_path)
    assert service.templates_dir == custom_path


def test_get_template_path_valid():
    """Test getting template path for valid artifact types."""
    service = TemplateService()

    # Test for each artifact type
    artifact_types = ["adr", "rfc", "evidence", "governance",
                     "implementation", "visibility", "uncommon"]

    for artifact_type in artifact_types:
        template_path = service.get_template_path(artifact_type)
        assert template_path.name == f"{artifact_type}_template.md"
        assert template_path.parent == service.templates_dir


def test_get_template_path_invalid():
    """Test getting template path for invalid artifact type."""
    service = TemplateService()

    with pytest.raises(ValueError, match="No template defined for artifact type"):
        service.get_template_path("invalid_type")


def test_template_exists(tmp_path):
    """Test template file existence check."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a test template
    adr_template = templates_dir / "adr_template.md"
    adr_template.write_text("# ADR Template")

    service = TemplateService(templates_dir=templates_dir)

    # Check existing template
    assert service.template_exists("adr") == True
    assert service.template_exists("adr_template.md") == True

    # Check non-existing template
    assert service.template_exists("rfc") == False


def test_get_all_templates(tmp_path):
    """Test retrieving all available templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create some templates
    for template_name in ["adr_template.md", "rfc_template.md", "evidence_template.md"]:
        (templates_dir / template_name).write_text(f"# {template_name}")

    service = TemplateService(templates_dir=templates_dir)

    templates = service.get_all_templates()

    # Should find all .md files ending with _template.md
    assert len(templates) == 3
    assert all(template_name.endswith("_template.md") for template_name in templates)
    assert "adr_template.md" in templates
    assert "rfc_template.md" in templates
    assert "evidence_template.md" in templates


def test_load_template_content(tmp_path):
    """Test loading template content from file."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a test template with placeholders
    template_content = """# {{title}}

**Status**: {{status}}
**Created**: {{created_at}}

## Context
{{context}}

## Decision
{{decision}}

## Consequences
{{consequences}}
"""
    adr_template = templates_dir / "adr_template.md"
    adr_template.write_text(template_content)

    service = TemplateService(templates_dir=templates_dir)

    content = service.load_template_content("adr")
    assert content == template_content

    # Test with full filename
    content2 = service.load_template_content("adr_template.md")
    assert content2 == template_content


def test_load_template_content_not_found():
    """Test loading non-existent template."""
    service = TemplateService()

    with pytest.raises(FileNotFoundError, match="Template file not found"):
        service.load_template_content("nonexistent_template")


def test_validate_template_schema_valid():
    """Test template schema validation with valid template."""
    service = TemplateService()

    # Mock template with valid placeholders
    template_content = """# {{title}}
{{content}}
**Status**: {{status}}
"""

    # This should not raise an exception
    service.validate_template_schema(template_content)


def test_validate_template_schema_invalid_placeholder():
    """Test template schema validation with invalid placeholder syntax."""
    service = TemplateService()

    # Template with invalid placeholder (missing closing braces)
    template_content = "# {{title}\n{{content"

    with pytest.raises(TemplateValidationError, match="Unmatched opening braces starting at position"):
        service.validate_template_schema(template_content)


def test_validate_template_schema_nested_placeholder():
    """Test template schema validation with nested placeholders."""
    service = TemplateService()

    # Template with nested placeholder (invalid)
    template_content = "# {{title {{nested}} }}"

    with pytest.raises(TemplateValidationError, match="Nested placeholders not allowed"):
        service.validate_template_schema(template_content)


def test_extract_placeholders():
    """Test extracting placeholders from template content."""
    service = TemplateService()

    template_content = """# {{title}}

**Status**: {{status}}
**Created**: {{created_at}}

{{content}}
{{optional_field}}"""

    placeholders = service.extract_placeholders(template_content)

    assert set(placeholders) == {"title", "status", "created_at", "content", "optional_field"}
    assert len(placeholders) == 5


def test_extract_placeholders_duplicate():
    """Test extracting placeholders with duplicates."""
    service = TemplateService()

    template_content = "# {{title}}\n{{title}}\n{{status}}"

    placeholders = service.extract_placeholders(template_content)

    # Duplicates should be removed
    assert set(placeholders) == {"title", "status"}
    assert len(placeholders) == 2


def test_apply_template_valid():
    """Test applying template with valid data."""
    service = TemplateService()

    template_content = """# {{title}}

**Status**: {{status}}
**Created**: {{created_at}}

{{content}}"""

    data = {
        "title": "Test ADR",
        "status": "proposed",
        "created_at": "2024-01-01T00:00:00",
        "content": "This is the content."
    }

    result = service.apply_template(template_content, data)

    expected = """# Test ADR

**Status**: proposed
**Created**: 2024-01-01T00:00:00

This is the content."""

    assert result == expected


def test_apply_template_missing_placeholder():
    """Test applying template with missing data for placeholder."""
    service = TemplateService()

    template_content = "# {{title}}\n{{content}}"

    data = {
        "title": "Test"
        # Missing "content"
    }

    with pytest.raises(ValueError, match="Missing value for placeholder"):
        service.apply_template(template_content, data)


def test_apply_template_extra_data():
    """Test applying template with extra data (should be ignored)."""
    service = TemplateService()

    template_content = "# {{title}}\n{{content}}"

    data = {
        "title": "Test",
        "content": "Content",
        "extra_field": "This should be ignored"
    }

    result = service.apply_template(template_content, data)

    # Should work without error, extra field ignored
    assert "Test" in result
    assert "Content" in result
    assert "extra_field" not in result


def test_apply_template_with_defaults():
    """Test applying template with default values."""
    service = TemplateService()

    template_content = """# {{title}}
{{content}}
**Status**: {{status|proposed}}"""

    data = {
        "title": "Test",
        "content": "Content"
        # status not provided, should use default
    }

    result = service.apply_template(template_content, data)

    assert "**Status**: proposed" in result


def test_apply_template_with_defaults_override():
    """Test applying template overriding default values."""
    service = TemplateService()

    template_content = """# {{title}}
{{content}}
**Status**: {{status|proposed}}"""

    data = {
        "title": "Test",
        "content": "Content",
        "status": "accepted"  # Override default
    }

    result = service.apply_template(template_content, data)

    assert "**Status**: accepted" in result


def test_generate_content_from_template(tmp_path):
    """Test full pipeline: load template and generate content."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a template
    template_content = """# {{title}}
**Type**: {{artifact_type}}
{{content}}"""
    adr_template = templates_dir / "adr_template.md"
    adr_template.write_text(template_content)

    service = TemplateService(templates_dir=templates_dir)

    data = {
        "title": "Test Artifact",
        "artifact_type": "adr",
        "content": "Test content."
    }

    result = service.generate_content_from_template("adr", data)

    expected = """# Test Artifact
**Type**: adr
Test content."""

    assert result == expected


def test_generate_content_for_artifact_create():
    """Test generating content for ArtifactCreate model."""
    service = TemplateService()

    # Mock template content
    template_content = """# {{title}}
**Type**: {{artifact_type}}
**Status**: {{status}}
{{content}}"""

    with patch.object(service, 'load_template_content', return_value=template_content):
        artifact_data = ArtifactCreate(
            artifact_type="adr",
            artifact_number="ADR-001-001",
            title="Test ADR",
            status="proposed",
            content="Test content",
            squad_id=1,
            level=1  # Required for ADR artifacts
        )

        # Convert model to dict for template
        data = artifact_data.model_dump()
        data["artifact_type"] = artifact_data.artifact_type

        result = service.generate_content_for_artifact(artifact_data)

        assert "Test ADR" in result
        assert "adr" in result
        assert "proposed" in result
        assert "Test content" in result


def test_create_missing_templates(tmp_path):
    """Test creating missing template files."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    service = TemplateService(templates_dir=templates_dir)

    # Create missing templates
    created = service.create_missing_templates()

    # Should create templates for all artifact types
    expected_templates = [
        "adr_template.md", "rfc_template.md", "evidence_template.md",
        "governance_template.md", "implementation_template.md",
        "visibility_template.md", "uncommon_template.md"
    ]

    assert len(created) == len(expected_templates)

    for template_name in expected_templates:
        template_path = templates_dir / template_name
        assert template_path.exists()
        assert template_name in created

        # Check content
        content = template_path.read_text()
        # Check for key elements in template
        assert "{{" in content  # Should have placeholders
        assert "}}" in content
        assert "title" in content or "Title" in content  # Should have title placeholder or heading
        assert "content" in content or "Content" in content  # Should have content placeholder or section


def test_validate_artifact_against_template_valid():
    """Test validating artifact data against template schema."""
    service = TemplateService()

    # Mock template with specific placeholders
    template_content = """# {{title}}
{{content}}
**Status**: {{status}}"""

    with patch.object(service, 'load_template_content', return_value=template_content):
        # Valid data with all required placeholders
        data = {
            "title": "Test",
            "content": "Content",
            "status": "proposed"
        }

        # Should not raise exception
        service.validate_artifact_against_template("adr", data)


def test_validate_artifact_against_template_missing_field():
    """Test validating artifact data with missing required field."""
    service = TemplateService()

    template_content = """# {{title}}
{{content}}
**Status**: {{status}}"""

    with patch.object(service, 'load_template_content', return_value=template_content):
        # Missing "content" field
        data = {
            "title": "Test",
            "status": "proposed"
        }

        with pytest.raises(ValueError, match="Missing required fields for template"):
            service.validate_artifact_against_template("adr", data)


def test_get_template_schema():
    """Test getting template schema (required placeholders)."""
    service = TemplateService()

    template_content = """# {{title}}
{{content}}
**Status**: {{status|proposed}}
{{optional_field}}"""

    with patch.object(service, 'load_template_content', return_value=template_content):
        schema = service.get_template_schema("adr")

        # Should include required placeholders (without defaults)
        assert "title" in schema["required"]
        assert "content" in schema["required"]
        assert "optional_field" in schema["required"]  # No default, so required
        assert "status" not in schema["required"]  # Has default

        # Should include all placeholders
        assert set(schema["all_placeholders"]) == {"title", "content", "status", "optional_field"}

        # Should include defaults
        assert schema["defaults"]["status"] == "proposed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])