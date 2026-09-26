from sqlalchemy import create_engine

#dialect+driver://username:password@host:port/database

#!replace with .env config!
engine = create_engine("postgresql+psycopg://appuser:1234@localhost:5432/appdb", echo=True)