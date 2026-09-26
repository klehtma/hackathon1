# hackathon1/data_service/database/db_config.py

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """
    Database configuration for data_service.

    Values are loaded from environment variables / .env.
    """

    model_config = SettingsConfigDict(
        env_prefix="DATA_SERVICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr = Field(
        ...,
        validation_alias="DATA_SERVICE_DATABASE_URL",
    )

    database_pool_size: int = Field(
        default=10,
        validation_alias="DATA_SERVICE_DB_POOL_SIZE",
        ge=1,
    )

    database_max_overflow: int = Field(
        default=20,
        validation_alias="DATA_SERVICE_DB_MAX_OVERFLOW",
        ge=0,
    )


@lru_cache
def get_database_config() -> DatabaseConfig:
    """
    Returns a cached (lazily created) database configuration instance.

    Cached via lru_cache so settings are only loaded once, but not
    instantiated at import time -- callers (e.g. tests) can set/patch
    environment variables before the first call.
    """
    return DatabaseConfig()