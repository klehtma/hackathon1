from sqlalchemy import create_engine

from config import db_config

engine = create_engine(db_config.database_url, echo=True)
