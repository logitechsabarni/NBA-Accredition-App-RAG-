import os
from dataclasses import dataclass


@dataclass
class Settings:
    """
    Central configuration management.
    """

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GRANITE_API_KEY: str = os.getenv("GRANITE_API_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_secret")
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"


settings = Settings()
