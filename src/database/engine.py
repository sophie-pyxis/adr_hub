"""
Database engine configuration with support for in-memory testing.
"""

import os
from pathlib import Path
from typing import Optional
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool


# Database URL configuration
def get_database_url(testing: bool = False) -> str:
    """
    Get database URL based on environment.

    Args:
        testing: If True, use in-memory SQLite for tests

    Returns:
        Database URL string
    """
    if testing:
        # In-memory SQLite for tests (as agreed in debate)
        return "sqlite:///:memory:"

    # Production SQLite in locale/ directory (as agreed in debate)
    db_path = Path(__file__).parent.parent.parent / "locale" / "governance.db"
    return f"sqlite:///{db_path}"


def get_engine(testing: bool = False):
    """
    Get SQLAlchemy engine.

    Args:
        testing: If True, configure for in-memory testing

    Returns:
        SQLAlchemy engine
    """
    database_url = get_database_url(testing)

    if testing:
        # In-memory SQLite requires special configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # Required for in-memory SQLite
            echo=False  # Set to True for SQL query logging
        )
    else:
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False  # Set to True for SQL query logging
        )

    return engine


def get_session(testing: bool = False):
    """
    Get database session.

    Args:
        testing: If True, use in-memory database

    Returns:
        Database session context manager
    """
    engine = get_engine(testing)
    with Session(engine) as session:
        yield session


def create_db_and_tables(testing: bool = False):
    """
    Create database and tables.

    Args:
        testing: If True, create in-memory database
    """
    from ..models.squad import Squad
    from ..models.artifact import Artifact
    from ..models.trigger_rule import TriggerRule
    from ..models.artifact_reference import ArtifactReference

    engine = get_engine(testing)
    SQLModel.metadata.create_all(engine)