"""
Test suite for database engine configuration.
"""

import os
import tempfile
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from src.database.engine import (
    get_database_url,
    get_engine,
    get_session,
    create_db_and_tables,
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
    assert engine.pool.__class__ == StaticPool


def test_get_engine_production():
    """Test getting engine for production environment."""
    engine = get_engine(testing=False)
    assert engine.url.database is not None
    assert "governance.db" in engine.url.database
    # In production, we don't use StaticPool
    assert engine.pool.__class__ != StaticPool


def test_get_session_testing():
    """Test getting session for testing environment."""
    session_gen = get_session(testing=True)
    session = next(session_gen)

    assert isinstance(session, Session)
    assert session.bind.url.database == ":memory:"

    # Clean up
    try:
        next(session_gen)  # This should raise StopIteration
    except StopIteration:
        pass


def test_get_session_production():
    """Test getting session for production environment."""
    session_gen = get_session(testing=False)
    session = next(session_gen)

    assert isinstance(session, Session)
    assert session.bind.url.database is not None
    assert "governance.db" in session.bind.url.database

    # Clean up
    try:
        next(session_gen)  # This should raise StopIteration
    except StopIteration:
        pass


def test_create_db_and_tables_testing():
    """Test creating database and tables in testing environment."""
    # This is a simple smoke test - just ensure it doesn't crash
    create_db_and_tables(testing=True)

    # For production, we can't easily test without creating actual files
    # So we'll skip the production test for now


def test_engine_configuration_options():
    """Test engine configuration options."""
    # Test with echo=True (if we had that option)
    # Currently echo is hardcoded to False, but we can test the structure
    engine = get_engine(testing=True)
    assert hasattr(engine, "echo")
    assert engine.echo == False


def test_session_context_manager():
    """Test that session works as a context manager."""
    session_gen = get_session(testing=True)

    # Test that we can get a session from the generator
    session = next(session_gen)
    assert isinstance(session, Session)
    assert session.is_active

    # Close the session
    session.close()

    # The generator should be exhausted
    with pytest.raises(StopIteration):
        next(session_gen)
