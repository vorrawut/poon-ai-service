"""
Configuration module for AI microservice
"""

from .settings import settings, setup_logging, validate_environment

__all__ = ["settings", "validate_environment", "setup_logging"]
