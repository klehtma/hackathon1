#!/bin/sh
# Runs once, on first Postgres init, as the admin user.
# Creates the least-privilege roles that the backend and data_service
# connect as (see BACKEND_DB_USER / DATA_SERVICE_DB_USER in .env).
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${BACKEND_DB_USER}') THEN
        CREATE ROLE "${BACKEND_DB_USER}" LOGIN PASSWORD '${BACKEND_DB_PASSWORD}';
      END IF;
      IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DATA_SERVICE_DB_USER}') THEN
        CREATE ROLE "${DATA_SERVICE_DB_USER}" LOGIN PASSWORD '${DATA_SERVICE_DB_PASSWORD}';
      END IF;
    END
    \$\$;

    GRANT ALL PRIVILEGES ON DATABASE "${POSTGRES_DB}" TO "${BACKEND_DB_USER}";
    GRANT ALL PRIVILEGES ON DATABASE "${POSTGRES_DB}" TO "${DATA_SERVICE_DB_USER}";
    GRANT ALL ON SCHEMA public TO "${BACKEND_DB_USER}", "${DATA_SERVICE_DB_USER}";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${BACKEND_DB_USER}", "${DATA_SERVICE_DB_USER}";
SQL
