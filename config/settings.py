"""
Settings configuration for AI microservice
Environment-based configuration with sensible defaults
"""

import os
from typing import Optional, List
from functools import lru_cache

class Settings:
    """Application settings"""
    
    # API Configuration
    app_name: str = "Poon AI Service"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))
    reload: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    # CORS Configuration
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    ).split(",")
    
    # OpenAI Configuration (fallback)
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_max_tokens: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))
    openai_timeout: int = int(os.getenv("OPENAI_TIMEOUT", "30"))
    
    # Llama4/Ollama Configuration (primary AI)
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    llama_model: str = os.getenv("LLAMA_MODEL", "llama2")  # Will be llama4 when available
    llama_timeout: int = int(os.getenv("LLAMA_TIMEOUT", "60"))
    use_llama: bool = os.getenv("USE_LLAMA", "true").lower() == "true"
    
    # OCR Configuration
    tesseract_path: Optional[str] = os.getenv("TESSERACT_PATH")
    tesseract_config: str = os.getenv("TESSERACT_CONFIG", "--oem 3 --psm 6")
    ocr_confidence_threshold: float = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.7"))
    
    # NLP Configuration
    nlp_confidence_threshold: float = float(os.getenv("NLP_CONFIDENCE_THRESHOLD", "0.6"))
    ai_fallback_threshold: float = float(os.getenv("AI_FALLBACK_THRESHOLD", "0.5"))
    
    # File Upload Configuration
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
    allowed_image_types: List[str] = os.getenv(
        "ALLOWED_IMAGE_TYPES",
        "image/jpeg,image/png,image/webp,image/heic"
    ).split(",")
    
    # Cache Configuration
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    
    # Rate Limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security Configuration
    api_key: Optional[str] = os.getenv("API_KEY")
    jwt_secret: Optional[str] = os.getenv("JWT_SECRET")
    
    # Thai Language Support
    thai_nlp_enabled: bool = os.getenv("THAI_NLP_ENABLED", "true").lower() == "true"
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration"""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "max_tokens": self.openai_max_tokens,
            "temperature": self.openai_temperature,
            "timeout": self.openai_timeout
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

def validate_environment():
    """Validate required environment variables"""
    settings = get_settings()
    errors = []
    
    if not settings.openai_api_key and settings.is_production():
        errors.append("OPENAI_API_KEY is required in production")
    
    if settings.is_production() and settings.debug:
        errors.append("DEBUG should be False in production")
    
    if errors:
        raise ValueError(f"Environment validation failed: {', '.join(errors)}")

def setup_logging():
    """Setup logging configuration"""
    import logging
    
    settings = get_settings()
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ai-service.log") if settings.is_production() else logging.NullHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)

# Global settings instance
settings = get_settings()

# Setup logging on import
setup_logging()