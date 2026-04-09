"""
Role configuration utilities for template generation.

This module provides functions to get role names and apply role-based
placeholders in templates.
"""

from typing import Any, Dict

from .config import settings


def get_role_names() -> Dict[str, str]:
    """Get all role names as a dictionary."""
    return {
        "PRINCIPAL_ARCHITECT": settings.PRINCIPAL_ARCHITECT_NAME,
        "ARCHITECT_MANAGER": settings.ARCHITECT_MANAGER_NAME,
        "BUSINESS_MANAGER": settings.BUSINESS_MANAGER_NAME,
        "ENGINEERING_MANAGER": settings.ENGINEERING_MANAGER_NAME,
        "DEFAULT_AUTHOR": settings.DEFAULT_AUTHOR_NAME,
    }


def inject_role_placeholders(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject role placeholders into template data.

    Args:
        data: Template data dictionary

    Returns:
        Updated data dictionary with role placeholders
    """
    role_names = get_role_names()
    data.update(role_names)
    return data


def get_role_placeholder_mapping() -> Dict[str, str]:
    """
    Get mapping of hardcoded names to role placeholders.

    Returns:
        Dictionary mapping hardcoded names to role placeholders
    """
    role_names = get_role_names()

    # Map specific hardcoded names to their corresponding roles
    # This is based on the original template structure:
    # - Sophie Pyxis de Paula → PRINCIPAL_ARCHITECT (or DEFAULT_AUTHOR)
    # - Thiago → ARCHITECT_MANAGER
    # - Silvana → BUSINESS_MANAGER
    # - Rodrigo → ENGINEERING_MANAGER

    return {
        "Sophie Pyxis de Paula": role_names["PRINCIPAL_ARCHITECT"],
        "Sophie": role_names["PRINCIPAL_ARCHITECT"],
        "Sophie propõe": f"{role_names['PRINCIPAL_ARCHITECT']} propõe",
        "Thiago": role_names["ARCHITECT_MANAGER"],
        "Thiago aprova": f"{role_names['ARCHITECT_MANAGER']} aprova",
        "Silvana": role_names["BUSINESS_MANAGER"],
        "Silvana endossa": f"{role_names['BUSINESS_MANAGER']} endossa",
        "Rodrigo": role_names["ENGINEERING_MANAGER"],
        "Thiago + Silvana": f"{role_names['ARCHITECT_MANAGER']} + {role_names['BUSINESS_MANAGER']}",
        "Thiago aprova, Silvana endossa": f"{role_names['ARCHITECT_MANAGER']} aprova, {role_names['BUSINESS_MANAGER']} endossa",
    }
