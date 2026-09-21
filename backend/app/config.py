import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "VisionX"
    API_V1_STR: str = "/api/v1"
    
    # Security / JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "visionx-secret-key-super-secure-sih-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://legalmetro:legalmetro123@localhost:5432/legalmetro_db"
    )
    
    # Redis / Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    
    # MinIO / Object Storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET_NAME: str = os.getenv("MINIO_BUCKET_NAME", "legalmetro-storage")
    MINIO_SECURE: bool = False
    
    # Local Storage Fallback
    STORAGE_LOCAL_DIR: str = os.getenv("STORAGE_LOCAL_DIR", "/app/storage_data")
    
    # LLM API
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    
    class Config:
        env_file = [".env", "/app/.env", "../.env"]
        extra = "allow"

settings = Settings()

if settings.GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
