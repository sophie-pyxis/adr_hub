"""
Template Service for unified artifact model.

PHASE 2: Template Service
- Templates for 7 artifact types: adr, rfc, evidence, governance, implementation, visibility, uncommon
- Template placeholder substitution system with Jinja2-like syntax
- Template validation and schema matching
"""

import datetime
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class TemplateValidationError(Exception):
    """Exception raised for template validation errors."""

    pass


class TemplateService:
    """Service for managing and applying templates for artifacts."""

    # Map artifact types to template file names
    TEMPLATE_MAP = {
        "adr": "adr_template.md",
        "rfc": "rfc_template.md",
        "evidence": "evidence_template.md",
        "governance": "governance_template.md",
        "implementation": "implementation_template.md",
        "visibility": "visibility_template.md",
        "uncommon": "uncommon_template.md",
    }

    # Default template directory
    DEFAULT_TEMPLATES_DIR = Path("templates")

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize TemplateService.

        Args:
            templates_dir: Directory containing template files.
                          If None, uses DEFAULT_TEMPLATES_DIR.
        """
        self.templates_dir = templates_dir or self.DEFAULT_TEMPLATES_DIR

    def get_template_path(self, artifact_type: str) -> Path:
        """
        Get the file path for a template by artifact type.

        Args:
            artifact_type: Type of artifact (e.g., 'adr', 'rfc')

        Returns:
            Path to template file

        Raises:
            ValueError: If no template is defined for the artifact type
        """
        if artifact_type not in self.TEMPLATE_MAP:
            raise ValueError(
                f"No template defined for artifact type: {artifact_type}. "
                f"Available types: {', '.join(self.TEMPLATE_MAP.keys())}"
            )

        template_filename = self.TEMPLATE_MAP[artifact_type]
        return self.templates_dir / template_filename

    def template_exists(self, artifact_type_or_filename: str) -> bool:
        """
        Check if a template exists.

        Args:
            artifact_type_or_filename: Either an artifact type or template filename

        Returns:
            True if template exists, False otherwise
        """
        try:
            # Try as artifact type first
            template_path = self.get_template_path(artifact_type_or_filename)
        except ValueError:
            # If not an artifact type, try as filename
            template_path = self.templates_dir / artifact_type_or_filename

        return template_path.exists()

    def get_all_templates(self) -> List[str]:
        """
        Get list of all available templates.

        Returns:
            List of template filenames
        """
        if not self.templates_dir.exists():
            return []

        templates = []
        for filename in self.templates_dir.glob("*_template.md"):
            templates.append(filename.name)

        return sorted(templates)

    def load_template_content(self, artifact_type_or_filename: str) -> str:
        """
        Load template content from file.

        Args:
            artifact_type_or_filename: Either an artifact type or template filename

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        # Try as artifact type first
        try:
            template_path = self.get_template_path(artifact_type_or_filename)
        except ValueError:
            # If not an artifact type, try as filename
            template_path = self.templates_dir / artifact_type_or_filename

        if not template_path.exists():
            raise FileNotFoundError(
                f"Template file not found: {template_path}. "
                f"Run create_missing_templates() to create default templates."
            )

        return template_path.read_text(encoding="utf-8")

    def validate_template_schema(self, template_content: str) -> None:
        """
        Validate template schema for proper placeholder syntax.

        Args:
            template_content: Template content to validate

        Raises:
            TemplateValidationError: If template has invalid syntax
        """
        # Find all {{ positions
        open_positions = [m.start() for m in re.finditer(r"\{\{", template_content)]
        close_positions = [m.start() for m in re.finditer(r"\}\}", template_content)]

        i = 0  # index for close_positions
        for open_pos in open_positions:
            # Find the next }} after this {{
            while i < len(close_positions) and close_positions[i] <= open_pos:
                i += 1

            if i >= len(close_positions):
                # No closing }} found for this {{
                raise TemplateValidationError(
                    f"Unmatched opening braces starting at position {open_pos}"
                )

            close_pos = close_positions[i]

            # Extract placeholder
            placeholder = template_content[open_pos : close_pos + 2]  # +2 for }}

            # Check for nested placeholders within this placeholder
            # Count how many {{ are between open_pos and close_pos
            inner_open = sum(1 for pos in open_positions if open_pos < pos < close_pos)
            if inner_open > 0:
                raise TemplateValidationError(
                    f"Nested placeholders not allowed: {placeholder}"
                )

            # Check for unmatched braces within placeholder
            if placeholder.count("{") != placeholder.count("}"):
                raise TemplateValidationError(
                    f"Unmatched braces in placeholder: {placeholder}"
                )

            # Remove surrounding braces for content validation
            content = placeholder[2:-2].strip()

            if not content:
                raise TemplateValidationError(f"Empty placeholder: {placeholder}")

            # Check for invalid characters
            if re.search(r"[^\w\-_|]", content):
                raise TemplateValidationError(
                    f"Invalid characters in placeholder name: {content}. "
                    f"Only alphanumeric, underscore, and hyphen allowed."
                )

            # Check for pipe (|) usage - only allowed for defaults
            if "|" in content:
                parts = content.split("|")
                if len(parts) != 2:
                    raise TemplateValidationError(
                        f"Invalid default syntax in placeholder: {placeholder}. "
                        f"Expected format: {{placeholder|default}}"
                    )
                placeholder_name, default_value = parts
                if not placeholder_name.strip() or not default_value.strip():
                    raise TemplateValidationError(
                        f"Invalid default syntax: {placeholder}"
                    )

            i += 1  # Move to next close position

    def extract_placeholders(self, template_content: str) -> Set[str]:
        """
        Extract all unique placeholder names from template content.

        Args:
            template_content: Template content

        Returns:
            Set of placeholder names (without braces or defaults)
        """
        placeholder_pattern = r"\{\{([^}]+)\}\}"
        placeholders = set()

        for match in re.finditer(placeholder_pattern, template_content):
            placeholder_content = match.group(1).strip()

            # Extract placeholder name (before pipe if default exists)
            if "|" in placeholder_content:
                placeholder_name = placeholder_content.split("|")[0].strip()
            else:
                placeholder_name = placeholder_content

            placeholders.add(placeholder_name)

        return placeholders

    def apply_template(self, template_content: str, data: Dict[str, Any]) -> str:
        """
        Apply data to template content, replacing placeholders.

        Args:
            template_content: Template content with placeholders
            data: Dictionary with values for placeholders

        Returns:
            Template with placeholders replaced

        Raises:
            ValueError: If data is missing for a required placeholder
        """
        # First, validate the template
        self.validate_template_schema(template_content)

        # Extract all placeholders and their defaults
        placeholder_pattern = r"\{\{([^}]+)\}\}"
        placeholders_with_defaults = {}

        for match in re.finditer(placeholder_pattern, template_content):
            full_placeholder = match.group(0)
            placeholder_content = match.group(1).strip()

            if "|" in placeholder_content:
                placeholder_name, default_value = placeholder_content.split("|")
                placeholder_name = placeholder_name.strip()
                default_value = default_value.strip()
            else:
                placeholder_name = placeholder_content
                default_value = None

            placeholders_with_defaults[full_placeholder] = {
                "name": placeholder_name,
                "default": default_value,
            }

        # Replace placeholders
        result = template_content
        for full_placeholder, info in placeholders_with_defaults.items():
            placeholder_name = info["name"]
            default_value = info["default"]

            if placeholder_name in data:
                value = data[placeholder_name]
            elif default_value is not None:
                value = default_value
            else:
                raise ValueError(
                    f"Missing value for placeholder '{placeholder_name}' "
                    f"and no default provided"
                )

            # Ensure value is string
            if not isinstance(value, str):
                value = str(value)

            result = result.replace(full_placeholder, value)

        return result

    def generate_content_from_template(
        self, artifact_type: str, data: Dict[str, Any]
    ) -> str:
        """
        Generate content by loading template and applying data.

        Args:
            artifact_type: Type of artifact
            data: Dictionary with values for placeholders

        Returns:
            Generated content with placeholders replaced
        """
        template_content = self.load_template_content(artifact_type)
        return self.apply_template(template_content, data)

    def generate_content_for_artifact(self, artifact_data: Any) -> str:
        """
        Generate content for an artifact model.

        Args:
            artifact_data: Artifact model instance (e.g., ArtifactCreate)

        Returns:
            Generated content
        """
        # Convert artifact to dictionary
        data = artifact_data.model_dump()

        # Add additional fields that might be needed
        data["artifact_type"] = getattr(artifact_data, "artifact_type", "")
        data["artifact_number"] = getattr(artifact_data, "artifact_number", "")
        data["title"] = getattr(artifact_data, "title", "")
        data["status"] = getattr(artifact_data, "status", "proposed")
        data["content"] = getattr(artifact_data, "content", "")

        # Add timestamp if not present
        if "created_at" not in data:
            data["created_at"] = datetime.datetime.now().isoformat()

        return self.generate_content_from_template(data["artifact_type"], data)

    def create_missing_templates(self) -> Dict[str, Path]:
        """
        Create missing template files with default content.

        Returns:
            Dictionary mapping template names to created file paths
        """
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True)

        created_templates = {}

        for artifact_type, template_filename in self.TEMPLATE_MAP.items():
            template_path = self.templates_dir / template_filename

            if not template_path.exists():
                default_content = self._get_default_template_content(artifact_type)
                template_path.write_text(default_content, encoding="utf-8")
                created_templates[template_filename] = template_path

        return created_templates

    def _get_default_template_content(self, artifact_type: str) -> str:
        """
        Get default template content for an artifact type.

        Args:
            artifact_type: Type of artifact

        Returns:
            Default template content
        """
        templates = {
            "adr": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Context
{{content}}

## Decision
[Decision goes here]

## Consequences
[Consequences go here]""",
            "rfc": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Description
{{content}}

## Motivation
[Motivation for this RFC]

## Proposed Solution
[Detailed solution description]

## Alternatives Considered
[Alternative approaches considered]""",
            "evidence": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Evidence Summary
{{content}}

## Source
[Source of evidence]

## Reliability Assessment
[Assessment of evidence reliability]

## Implications
[Implications for decision-making]""",
            "governance": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Governance Context
{{content}}

## Compliance Requirements
[Compliance requirements]

## Approval Process
[Approval process description]

## Monitoring
[Monitoring and enforcement mechanisms]""",
            "implementation": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Implementation Details
{{content}}

## Dependencies
[Dependencies required]

## Testing Strategy
[Testing approach]

## Rollout Plan
[Rollout and deployment plan]""",
            "visibility": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Visibility Requirements
{{content}}

## Stakeholders
[Key stakeholders]

## Communication Plan
[Communication strategy]

## Feedback Mechanisms
[Feedback collection methods]""",
            "uncommon": """# {{title}}

**Artifact Number**: {{artifact_number}}
**Type**: {{artifact_type}}
**Status**: {{status}}
**Created**: {{created_at}}

## Uncommon Context
{{content}}

## Special Considerations
[Special considerations or exceptions]

## Justification
[Justification for uncommon approach]

## Risk Assessment
[Risk assessment and mitigation]""",
        }

        return templates.get(artifact_type, f"# {{title}}\n\n{{content}}")

    def validate_artifact_against_template(
        self, artifact_type: str, data: Dict[str, Any]
    ) -> None:
        """
        Validate that artifact data has all required fields for template.

        Args:
            artifact_type: Type of artifact
            data: Artifact data to validate

        Raises:
            ValueError: If data is missing required fields
        """
        template_content = self.load_template_content(artifact_type)
        placeholders = self.extract_placeholders(template_content)

        # Check for required placeholders (those without defaults)
        missing_fields = []
        for placeholder in placeholders:
            if placeholder not in data:
                # Check if this placeholder has a default in the template
                if not self._placeholder_has_default(template_content, placeholder):
                    missing_fields.append(placeholder)

        if missing_fields:
            raise ValueError(
                f"Missing required fields for template '{artifact_type}': "
                f"{', '.join(missing_fields)}"
            )

    def _placeholder_has_default(self, template_content: str, placeholder: str) -> bool:
        """Check if a placeholder has a default value in the template."""
        pattern = rf"\{{{{\s*{re.escape(placeholder)}\s*\|\s*[^}}]+\s*}}}}"
        return bool(re.search(pattern, template_content))

    def get_template_schema(self, artifact_type: str) -> Dict[str, Any]:
        """
        Get schema information for a template.

        Args:
            artifact_type: Type of artifact

        Returns:
            Dictionary with schema information:
            - required: List of required placeholder names
            - defaults: Dict of placeholder names to default values
            - all_placeholders: List of all placeholder names
        """
        template_content = self.load_template_content(artifact_type)
        placeholders = self.extract_placeholders(template_content)

        schema = {
            "required": [],
            "defaults": {},
            "all_placeholders": list(placeholders),
        }

        # Check each placeholder for defaults
        for placeholder in placeholders:
            # Find the placeholder in the template
            pattern = rf"\{{{{\s*{re.escape(placeholder)}(?:\s*\|\s*([^}}]+))?\s*}}}}"
            match = re.search(pattern, template_content)

            if match and match.group(1):
                # Has default
                schema["defaults"][placeholder] = match.group(1).strip()
            else:
                # No default - required
                schema["required"].append(placeholder)

        return schema
