"""
Centralized configuration management for NBA Enterprise AI Platform.
All settings are read from environment variables or .env file.
Never hardcode secrets.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent


@dataclass
class WatsonxConfig:
    api_key: str = field(default_factory=lambda: os.getenv("WATSONX_API_KEY", ""))
    project_id: str = field(default_factory=lambda: os.getenv("WATSONX_PROJECT_ID", ""))
    url: str = field(default_factory=lambda: os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"))
    model_id: str = field(default_factory=lambda: os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"))
    max_new_tokens: int = 1024
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 1.0
    repetition_penalty: float = 1.1
    decoding_method: str = "greedy"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.project_id)


@dataclass
class RAGConfig:
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    vector_db_path: Path = field(default_factory=lambda: BASE_DIR / "vector_db")
    collection_name: str = "nba_documents"
    similarity_threshold: float = 0.3


@dataclass
class AppConfig:
    app_name: str = "NBA Enterprise AI Accreditation Platform"
    app_version: str = "1.0.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    log_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
    vector_db_dir: Path = field(default_factory=lambda: BASE_DIR / "vector_db")
    nba_target_attainment: float = 60.0
    direct_assessment_weight: float = 0.8
    indirect_assessment_weight: float = 0.2


@dataclass
class PlatformSettings:
    watsonx: WatsonxConfig = field(default_factory=WatsonxConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    app: AppConfig = field(default_factory=AppConfig)

    def ensure_dirs(self):
        """Create required directories if they don't exist."""
        for d in [self.app.data_dir, self.app.log_dir, self.app.vector_db_dir]:
            d.mkdir(parents=True, exist_ok=True)


# Singleton
_settings: Optional[PlatformSettings] = None


def get_settings() -> PlatformSettings:
    global _settings
    if _settings is None:
        _settings = PlatformSettings()
        _settings.ensure_dirs()
    return _settings
