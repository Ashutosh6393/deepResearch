
from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Values are loaded from environment variables and optionally
    from a local .env file.
    """

    model_config = SettingsConfigDict(
        env_prefix="DEEPRESEARCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    # Application
    app_name: str = "DeepResearch AI"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)

    # Logging
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO"

    # Database
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://deepresearch:deepresearch@localhost:5432/deepresearch"
    )

    @model_validator(mode="after")
    def validate_environment_settings(self) -> "Settings":
        if (
            self.environment == Environment.PRODUCTION
            and self.debug
        ):
            raise ValueError("Debug mode must be disabled in production.")

        if not self.api_v1_prefix.startswith("/"):
            raise ValueError("API prefix must start with '/'.")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached application settings instance.

    The same instance is reused throughout the application.
    """
    return Settings()
