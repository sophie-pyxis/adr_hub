"""
Simple test suite for database engine configuration.
"""

import pytest
from sqlmodel import Session

from src.database.engine import (
    create_db_and_tables,
    get_database_url,
    get_engine,
    get_session,
)


def test_get_database_url_testing():
    """Test getting database URL for testing environment."""
    url = get_database_url(testing=True)
    assert url == "sqlite:///:memory:"


def test_get_database_url_production():
    """Test getting database URL for production environment."""
    url = get_database_url(testing=False)
    assert url.startswith("sqlite:///")
    # Check for governance.db in the path (handle both forward and backward slashes)
    assert "governance.db" in url
    # Check that it points to locale directory
    assert "locale" in url.lower()


def test_get_engine_testing():
    """Test getting engine for testing environment."""
    engine = get_engine(testing=True)
    assert engine.url.database == ":memory:"


def test_get_engine_production():
    """Test getting engine for production environment."""
    engine = get_engine(testing=False)
    assert engine.url.database is not None
    assert "governance.db" in engine.url.database


def test_get_session_testing():
    """Test getting session for testing environment."""
    session_gen = get_session(testing=True)
    session = next(session_gen)

    assert isinstance(session, Session)
    assert session.bind.url.database == ":memory:"

    # The generator should be exhausted
    with pytest.raises(StopIteration):
        next(session_gen)


def test_create_db_and_tables_smoke_test():
    """Smoke test for creating database and tables."""
    # Just ensure it doesn't crash
    create_db_and_tables(testing=True)
