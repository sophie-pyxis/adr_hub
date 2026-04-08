"""
Test configuration and fixtures for AI Architecture Governance System.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from src.database import get_session
from src.main import app


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite database session for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Create FastAPI TestClient with overridden database session."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="test_squad_data")
def test_squad_data_fixture():
    """Test squad data for creating squads."""
    return {
        "squad_code": "ai-engineering",
        "name": "AI Engineering Squad",
        "tech_lead": "Carlos Mendes",
        "status": "active"
    }


@pytest.fixture(name="test_adr_data")
def test_adr_data_fixture():
    """Test ADR data for creating ADRs."""
    return {
        "adr_number": "auto",  # Will be auto-generated
        "title": "Adoption of Azure OpenAI as default LLM provider",
        "level": 3,
        "status": "proposed",
        "content": "This ADR proposes adopting Azure OpenAI as our default LLM provider...",
        "tco_estimate": "Estimated $10k/month for initial usage",
        "health_compliance_impact": "HIPAA compliance required for healthcare data",
        "lgpd_analysis": "Data anonymization required for Brazilian LGPD compliance",
        "rfc_status": "RFC-0001 completed",
        "squad_id": 1  # Will be set after squad creation
    }