"""
Configuration module for AI microservice
"""

from .settings import settings, validate_environment, setup_logging

__all__ = ["settings", "validate_environment", "setup_logging"]
