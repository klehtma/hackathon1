# data_service/config.py

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """
    Database configuration for data_service.

    Values are loaded from environment variables / .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
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
    Returns a cached database configuration instance.
    """
    return DatabaseConfig()


db_config = get_database_config()