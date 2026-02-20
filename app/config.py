"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Docker Configuration
    docker_host: Optional[str] = None
    
    # Vast.ai API Configuration
    vast_api_key: Optional[str] = None
    vast_api_url: str = "https://console.vast.ai/api/v0"
    
    # Application Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./openmesh.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

