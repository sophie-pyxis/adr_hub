"""
Test basic imports work correctly from the project root.
Replaces the old subprocess-based debug script.
"""
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def test_project_root_is_correct():
    """Verify PROJECT_ROOT resolves to the adr_hub folder."""
    assert (PROJECT_ROOT / "src").exists(), f"src/ not found under {PROJECT_ROOT}"
    assert (PROJECT_ROOT / "tests").exists(), f"tests/ not found under {PROJECT_ROOT}"


def test_sqlmodel_importable():
    """SQLModel must be installed and importable."""
    import sqlmodel  # noqa: F401
    assert sqlmodel is not None


def test_artifact_base_importable():
    """ArtifactBase must be importable from src.models.artifact."""
    from src.models.artifact import ArtifactBase
    assert ArtifactBase is not None


def test_artifact_model_importable():
    """Full Artifact model must be importable."""
    from src.models.artifact import Artifact, ArtifactCreate, ArtifactRead
    assert Artifact is not None
    assert ArtifactCreate is not None
    assert ArtifactRead is not None


def test_squad_model_importable():
    """Squad model must be importable."""
    from src.models.squad import Squad, SquadCreate, SquadRead
    assert Squad is not None


def test_services_importable():
    """All active services must be importable."""
    from src.services import (
        SquadService,
        TemplateService,
        ArtifactService,
        TriggerService,
        HealthService,
    )
    assert all([SquadService, TemplateService, ArtifactService, TriggerService, HealthService])


def test_app_importable():
    """FastAPI app must be importable without errors."""
    from src.main import app
    assert app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])