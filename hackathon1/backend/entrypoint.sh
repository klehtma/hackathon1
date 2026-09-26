#!/bin/sh
set -e

# Apply any pending migrations, then start the server.
# Safe to run on every boot: no-op if the DB is already up to date.
npx prisma migrate deploy

exec node src/server.js
