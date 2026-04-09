"""
Configuration module for Architecture Governance System.

This module contains configuration for role names and other settings
that should be configurable rather than hardcoded.
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with configurable role names."""

    # Role names - can be overridden by environment variables
    PRINCIPAL_ARCHITECT_NAME: str = "Principal Architect"
    ARCHITECT_MANAGER_NAME: str = "Architect Manager"
    BUSINESS_MANAGER_NAME: str = "Business Manager"
    ENGINEERING_MANAGER_NAME: str = "Engineering Manager"

    # Default author name for generated templates
    # When not specified, uses the principal architect role
    DEFAULT_AUTHOR_NAME: str = PRINCIPAL_ARCHITECT_NAME

    # Template configuration
    TEMPLATES_DIR: str = "templates"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create a global settings instance
settings = Settings()
