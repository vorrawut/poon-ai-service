"""Application settings and configuration."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = Field(default="Poon AI Service", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development/staging/production)")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Database settings
    database_url: str = Field(default="sqlite:///./spending.db", description="Database connection URL")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # AI Service settings - Ollama/Llama
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    llama_model: str = Field(default="llama3.2:3b", description="Llama model name")
    llama_timeout: int = Field(default=30, description="Llama API timeout in seconds")
    use_llama: bool = Field(default=True, description="Enable Llama processing")

    # AI Service settings - OpenAI (fallback)
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    openai_timeout: int = Field(default=30, description="OpenAI API timeout in seconds")
    use_openai_fallback: bool = Field(default=True, description="Use OpenAI as fallback")

    # OCR settings
    tesseract_path: str | None = Field(default=None, description="Tesseract executable path")
    tesseract_languages: str = Field(default="eng+tha", description="OCR languages")
    ocr_confidence_threshold: float = Field(default=0.6, description="Minimum OCR confidence")

    # Cache settings
    redis_url: str | None = Field(default=None, description="Redis connection URL")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    enable_caching: bool = Field(default=True, description="Enable caching")

    # Processing settings
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    max_text_length: int = Field(default=2000, description="Maximum text length for processing")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence for auto-acceptance")

    # Security settings
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="CORS allowed origins (comma-separated)"
    )
    api_key: str | None = Field(default=None, description="API key for authentication")

    # Monitoring settings
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # Feature flags
    enable_voice_processing: bool = Field(default=True, description="Enable voice input processing")
    enable_batch_processing: bool = Field(default=True, description="Enable batch file processing")
    enable_ai_enhancement: bool = Field(default=True, description="Enable AI enhancement")
    enable_pattern_analysis: bool = Field(default=True, description="Enable spending pattern analysis")

    @validator("environment")
    def validate_environment(self, v: str) -> str:
        """Validate environment setting."""
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            msg = f"Environment must be one of {allowed}"
            raise ValueError(msg)
        return v.lower()

    @validator("log_level")
    def validate_log_level(self, v: str) -> str:
        """Validate log level setting."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            msg = f"Log level must be one of {allowed}"
            raise ValueError(msg)
        return v.upper()

    @validator("confidence_threshold", "ocr_confidence_threshold")
    def validate_confidence_threshold(self, v: float) -> float:
        """Validate confidence threshold values."""
        if not 0.0 <= v <= 1.0:
            msg = "Confidence threshold must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v

    @validator("port", "metrics_port")
    def validate_port(self, v: int) -> int:
        """Validate port numbers."""
        if not 1 <= v <= 65535:
            msg = "Port must be between 1 and 65535"
            raise ValueError(msg)
        return v

    @validator("max_file_size_mb")
    def validate_max_file_size(self, v: int) -> int:
        """Validate maximum file size."""
        if v <= 0 or v > 100:
            msg = "Max file size must be between 1 and 100 MB"
            raise ValueError(msg)
        return v

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def get_database_url(self) -> str:
        """Get the database URL."""
        return self.database_url

    def get_ollama_url(self) -> str:
        """Get the Ollama server URL."""
        return self.ollama_url.rstrip('/')

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins list."""
        # Parse comma-separated origins
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

        if self.is_development():
            # Add common development origins
            dev_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080",
            ]
            return list(set(origins + dev_origins))
        return origins

    def get_feature_flags(self) -> dict[str, bool]:
        """Get all feature flags as a dictionary."""
        return {
            "voice_processing": self.enable_voice_processing,
            "batch_processing": self.enable_batch_processing,
            "ai_enhancement": self.enable_ai_enhancement,
            "pattern_analysis": self.enable_pattern_analysis,
            "caching": self.enable_caching,
            "metrics": self.enable_metrics,
        }

    def get_ai_config(self) -> dict[str, Any]:
        """Get AI service configuration."""
        return {
            "llama": {
                "enabled": self.use_llama,
                "url": self.get_ollama_url(),
                "model": self.llama_model,
                "timeout": self.llama_timeout,
            },
            "openai": {
                "enabled": self.use_openai_fallback and bool(self.openai_api_key),
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "timeout": self.openai_timeout,
            },
        }



@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    settings = Settings()

    # Validate environment configuration
    try:
        settings.validate_environment()
    except ValueError as e:
        # In development, log warnings instead of failing
        if settings.is_development():
            print(f"Configuration warning: {e}")
        else:
            raise

    return settings
