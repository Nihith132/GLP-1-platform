"""
Configuration management for GLP-1 Regulatory Intelligence Platform
Loads environment variables and provides centralized config access
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project Info
    PROJECT_NAME: str = "GLP-1 Regulatory Intelligence Platform"
    VERSION: str = "1.0.0"
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "eu-north-1"  # Stockholm region
    S3_BUCKET_NAME: str = "glp1-raw-labels"
    
    # PostgreSQL Configuration (Supabase with pgvector)
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Vector Database (using pgvector in PostgreSQL)
    # No separate vector DB needed - pgvector extension handles embeddings
    VECTOR_DIMENSIONS: int = 384  # For all-MiniLM-L6-v2 model
    
    # Groq LLM Configuration
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-70b-versatile"  # Fast and accurate
    
    # Application Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Vector Embedding Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 500  # Characters per chunk for vectorization
    CHUNK_OVERLAP: int = 50
    
    # NER Model Settings
    NER_MODEL: str = "dmis-lab/biobert-base-cased-v1.2"
    NER_CONFIDENCE_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance - loads once and reuses
    Use this function to access settings throughout the app
    """
    return Settings()


# Convenience export
settings = get_settings()
