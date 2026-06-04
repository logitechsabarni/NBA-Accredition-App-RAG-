"""
NBA Enterprise AI Platform — Application Settings
Centralised configuration using pydantic-settings.
All values are loaded from environment variables / .env file.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nba_platform"
    POSTGRES_USER: str = "nba_admin"
    POSTGRES_PASSWORD: str = "changeme"
    DATABASE_URL: str = ""

    # MongoDB
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DB: str = "nba_platform_nosql"
    MONGO_USER: str = "nba_mongo_admin"
    MONGO_PASSWORD: str = "changeme"
    MONGO_URI: str = ""

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "changeme"
    REDIS_URL: str = ""

    def model_post_init(self, __context) -> None:
        if not self.DATABASE_URL:
            object.__setattr__(
                self,
                "DATABASE_URL",
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}",
            )
        if not self.MONGO_URI:
            object.__setattr__(
                self,
                "MONGO_URI",
                f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}"
                f"@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}",
            )
        if not self.REDIS_URL:
            object.__setattr__(
                self,
                "REDIS_URL",
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0",
            )


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    JWT_SECRET_KEY: str = "change-this-secret-in-production-minimum-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.2


class WatsonxSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    GRANITE_MODEL_ID: str = "ibm/granite-13b-instruct-v2"
    GRANITE_MAX_TOKENS: int = 4096
    GRANITE_TEMPERATURE: float = 0.2


class RAGSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "vector_db/faiss_index"
    FAISS_DIMENSION: int = 384
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.7
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "NBA_Enterprise_AI_Platform"
    APP_ENV: Literal["development", "staging", "production"] = "production"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-this-in-production"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    CORS_MAX_AGE: int = 600

    # Security
    RATE_LIMIT_PER_MINUTE: int = 60
    BCRYPT_ROUNDS: int = 12

    # LLM Routing
    DEFAULT_LLM_PROVIDER: Literal["openai", "granite", "auto"] = "auto"
    LLM_FALLBACK_PROVIDER: Literal["openai", "granite"] = "openai"

    # File Storage
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "data/uploads"
    GENERATED_PDF_DIR: str = "data/generated_pdfs"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Monitoring
    PROMETHEUS_PORT: int = 9090
    METRICS_ENABLED: bool = True

    # Database sub-settings (composed)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    watsonx: WatsonxSettings = Field(default_factory=WatsonxSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        return v

    def get_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def ensure_directories(self) -> None:
        """Create required directories on startup."""
        dirs = [
            self.DATA_DIR,
            self.UPLOAD_DIR,
            self.GENERATED_PDF_DIR,
            self.rag.FAISS_INDEX_PATH,
            "logs",
            "vector_db",
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance. Call once per process."""
    settings = Settings()
    settings.ensure_directories()
    return settings


# Module-level singleton
settings: Settings = get_settings()
