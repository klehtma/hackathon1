# hackathon1/data_service/database/engine.py

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from hackathon1.data_service.database.db_config import get_database_config


@lru_cache
def get_engine() -> Engine:
    """
    Returns a cached SQLAlchemy engine, built from the database config.

    Lazily created on first call so the config (and thus the engine)
    isn't instantiated at import time -- useful for tests that need to
    set environment variables or patch config before the engine exists.
    """
    db_config = get_database_config()

    return create_engine(
        db_config.database_url.get_secret_value(),
        echo=False,
        pool_size=db_config.database_pool_size,
        max_overflow=db_config.database_max_overflow,
        pool_pre_ping=True,
    )


engine = get_engine()