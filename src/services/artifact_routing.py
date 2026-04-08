"""
Artifact Routing Service following Fleury taxonomy.

Strict path mapping for artifact types:
- ADR: docs/architecture/decisions/{adr_number}.md
- RFC: docs/architecture/rfcs/{rfc_number}.md
- C4_MODEL: docs/architecture/models/{model_name}.md
- CHECKLIST: docs/checklists/{checklist_name}.md
- TECH_DEBT: docs/tech-debt/{debt_id}.md
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Union
import datetime


class ArtifactType(str, Enum):
    """Artifact types following Fleury taxonomy."""

    ADR = "ADR"
    RFC = "RFC"
    C4_MODEL = "C4_MODEL"
    CHECKLIST = "CHECKLIST"
    TECH_DEBT = "TECH_DEBT"


class ArtifactRouter:
    """Router for artifact paths based on Fleury taxonomy."""

    # Path templates for each artifact type
    _PATH_TEMPLATES = {
        ArtifactType.ADR: "architecture/decisions/{artifact_id}.md",
        ArtifactType.RFC: "architecture/rfcs/{artifact_id}.md",
        ArtifactType.C4_MODEL: "architecture/models/{artifact_id}.md",
        ArtifactType.CHECKLIST: "checklists/{artifact_id}.md",
        ArtifactType.TECH_DEBT: "tech-debt/{artifact_id}.md",
    }

    def __init__(self, base_path: Union[str, Path] = "docs"):
        """
        Initialize ArtifactRouter.

        Args:
            base_path: Base directory for all artifacts (default: "docs")
        """
        self.base_path = Path(base_path)

    def get_path(
        self, artifact_type: Union[ArtifactType, str], artifact_id: str
    ) -> Path:
        """
        Get filesystem path for an artifact.

        Args:
            artifact_type: Type of artifact (ArtifactType enum or string)
            artifact_id: Identifier for the artifact (e.g., ADR-001-001, RFC-001)

        Returns:
            Path object for the artifact file

        Raises:
            ValueError: If artifact_type is unknown
        """
        artifact_type_enum = self._artifact_type_from_string(artifact_type)

        if artifact_type_enum not in self._PATH_TEMPLATES:
            raise ValueError(f"Unknown artifact type: {artifact_type}")

        template = self._PATH_TEMPLATES[artifact_type_enum]
        relative_path = template.format(artifact_id=artifact_id)

        return self.base_path / relative_path

    def ensure_directory_exists(self, path: Path) -> None:
        """
        Ensure the directory for a path exists.

        Args:
            path: Path to ensure directory exists for
        """
        path.parent.mkdir(parents=True, exist_ok=True)

    def generate_markdown_content(
        self, artifact_type: Union[ArtifactType, str], artifact_data: Dict[str, Any]
    ) -> str:
        """
        Generate markdown content for an artifact.

        Args:
            artifact_type: Type of artifact
            artifact_data: Dictionary with artifact data

        Returns:
            Markdown content as string
        """
        artifact_type_enum = self._artifact_type_from_string(artifact_type)

        if artifact_type_enum == ArtifactType.ADR:
            return self._generate_adr_content(artifact_data)
        elif artifact_type_enum == ArtifactType.RFC:
            return self._generate_rfc_content(artifact_data)
        elif artifact_type_enum == ArtifactType.C4_MODEL:
            return self._generate_c4_model_content(artifact_data)
        elif artifact_type_enum == ArtifactType.CHECKLIST:
            return self._generate_checklist_content(artifact_data)
        elif artifact_type_enum == ArtifactType.TECH_DEBT:
            return self._generate_tech_debt_content(artifact_data)
        else:
            raise ValueError(
                f"Unsupported artifact type for content generation: {artifact_type}"
            )

    def save_artifact(
        self,
        artifact_type: Union[ArtifactType, str],
        artifact_id: str,
        artifact_data: Dict[str, Any],
    ) -> Path:
        """
        Save artifact to filesystem.

        Args:
            artifact_type: Type of artifact
            artifact_id: Identifier for the artifact
            artifact_data: Dictionary with artifact data

        Returns:
            Path where artifact was saved
        """
        path = self.get_path(artifact_type, artifact_id)
        self.ensure_directory_exists(path)

        content = self.generate_markdown_content(artifact_type, artifact_data)
        path.write_text(content, encoding="utf-8")

        return path

    def _artifact_type_from_string(
        self, artifact_type: Union[ArtifactType, str]
    ) -> ArtifactType:
        """
        Convert string to ArtifactType enum.

        Args:
            artifact_type: ArtifactType enum or string

        Returns:
            ArtifactType enum

        Raises:
            ValueError: If string doesn't match any ArtifactType
        """
        if isinstance(artifact_type, ArtifactType):
            return artifact_type

        try:
            return ArtifactType(artifact_type)
        except ValueError:
            raise ValueError(f"Unknown artifact type: {artifact_type}")

    def _generate_adr_content(self, adr_data: Dict[str, Any]) -> str:
        """Generate markdown content for ADR."""
        lines = [
            f"# {adr_data.get('adr_number', 'ADR-XXX-XXX')}: {adr_data.get('title', 'Untitled ADR')}",
            "",
            f"**Status**: {adr_data.get('status', 'proposed')}",
            f"**Created**: {adr_data.get('created_at', datetime.datetime.now().isoformat())}",
            f"**Updated**: {adr_data.get('updated_at', datetime.datetime.now().isoformat())}",
            "",
            "## Context",
            "",
            adr_data.get("content", "No content provided."),
            "",
            "## Decision",
            "",
            adr_data.get("decision", "Decision not documented."),
            "",
            "## Consequences",
            "",
            adr_data.get("consequences", "Consequences not documented."),
        ]

        # Add optional fields if present
        if adr_data.get("tco_estimate"):
            lines.extend(["", f"**TCO Estimate**: {adr_data['tco_estimate']}"])

        if adr_data.get("lgpd_analysis"):
            lines.extend(["", f"**LGPD Analysis**: {adr_data['lgpd_analysis']}"])

        if adr_data.get("health_compliance_impact"):
            lines.extend(
                [
                    "",
                    f"**Health Compliance Impact**: {adr_data['health_compliance_impact']}",
                ]
            )

        return "\n".join(lines)

    def _generate_rfc_content(self, rfc_data: Dict[str, Any]) -> str:
        """Generate markdown content for RFC."""
        lines = [
            f"# {rfc_data.get('rfc_number', 'RFC-XXX')}: {rfc_data.get('title', 'Untitled RFC')}",
            "",
            f"**Status**: {rfc_data.get('status', 'draft')}",
            f"**Created**: {rfc_data.get('created_at', datetime.datetime.now().isoformat())}",
            "",
            "## Description",
            "",
            rfc_data.get("description", "No description provided."),
            "",
            "## Motivation",
            "",
            rfc_data.get("motivation", "Motivation not documented."),
            "",
            "## Proposed Solution",
            "",
            rfc_data.get("proposed_solution", "Proposed solution not documented."),
            "",
            "## Alternatives Considered",
            "",
            rfc_data.get("alternatives", "Alternatives not documented."),
        ]

        # Add circuit breaker info if present
        if rfc_data.get("circuit_breaker_enabled"):
            lines.extend(
                [
                    "",
                    "## Circuit Breaker Configuration",
                    "",
                    f"- **Enabled**: Yes",
                    f"- **Max Retries**: {rfc_data.get('max_retries', 3)}",
                    f"- **Retry Delay**: {rfc_data.get('retry_delay_seconds', 1.0)} seconds",
                    f"- **Circuit Open Time**: {rfc_data.get('circuit_open_seconds', 30.0)} seconds",
                ]
            )

        return "\n".join(lines)

    def _generate_c4_model_content(self, model_data: Dict[str, Any]) -> str:
        """Generate markdown content for C4 model."""
        lines = [
            f"# {model_data.get('name', 'Untitled Model')}",
            "",
            f"**Type**: {model_data.get('type', 'C4 Model')}",
            f"**Created**: {model_data.get('created_at', datetime.datetime.now().isoformat())}",
            "",
            "## Description",
            "",
            model_data.get("description", "No description provided."),
            "",
            "## Components",
            "",
            model_data.get("components", "Components not documented."),
            "",
            "## Relationships",
            "",
            model_data.get("relationships", "Relationships not documented."),
        ]

        return "\n".join(lines)

    def _generate_checklist_content(self, checklist_data: Dict[str, Any]) -> str:
        """Generate markdown content for checklist."""
        lines = [
            f"# {checklist_data.get('name', 'Untitled Checklist')}",
            "",
            f"**Category**: {checklist_data.get('category', 'General')}",
            f"**Created**: {checklist_data.get('created_at', datetime.datetime.now().isoformat())}",
            "",
            "## Description",
            "",
            checklist_data.get("description", "No description provided."),
            "",
            "## Items",
            "",
        ]

        # Add checklist items
        items = checklist_data.get("items", [])
        if items:
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. [ ] {item}")
        else:
            lines.append("No items defined.")

        return "\n".join(lines)

    def _generate_tech_debt_content(self, debt_data: Dict[str, Any]) -> str:
        """Generate markdown content for tech debt."""
        lines = [
            f"# {debt_data.get('id', 'TD-XXX')}: {debt_data.get('title', 'Untitled Tech Debt')}",
            "",
            f"**Status**: {debt_data.get('status', 'open')}",
            f"**Priority**: {debt_data.get('priority', 'medium')}",
            f"**Created**: {debt_data.get('created_at', datetime.datetime.now().isoformat())}",
            f"**Due Date**: {debt_data.get('due_date', 'Not specified')}",
            "",
            "## Description",
            "",
            debt_data.get("description", "No description provided."),
            "",
            "## Impact",
            "",
            debt_data.get("impact", "Impact not documented."),
            "",
            "## Proposed Fix",
            "",
            debt_data.get("proposed_fix", "Proposed fix not documented."),
            "",
            "## Notes",
            "",
            debt_data.get("notes", "No additional notes."),
        ]

        return "\n".join(lines)
