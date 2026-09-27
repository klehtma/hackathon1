"""
Configuration for data_service_beta.

Everything here is intentionally plain constants + env vars — no framework,
so it's easy to read top to bottom during a hackathon.
"""

import os
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #

# Built the same way the original data_service's DATA_SERVICE_DATABASE_URL is,
# but as a plain "postgresql://" URL since we're using psycopg directly
# (no SQLAlchemy) — see docker-compose.yaml for how this gets assembled.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    user = os.environ["DATA_SERVICE_DB_USER"]
    password = os.environ["DATA_SERVICE_DB_PASSWORD"]
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_DB"]
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"


# --------------------------------------------------------------------------- #
# Run behaviour
# --------------------------------------------------------------------------- #

# If true, scrape once and exit (good for `docker compose run --rm ...` while
# testing). If false, loop forever with POLL_INTERVAL_SECONDS between runs.
RUN_ONCE = os.environ.get("RUN_ONCE", "true").lower() in ("1", "true", "yes")
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "120"))

# Only write an opportunity to the DB if its profit is at least this much.
# 0 = write anything that's mathematically a positive-profit arb.
MIN_PROFIT_PERCENT = float(os.environ.get("MIN_PROFIT_PERCENT", "0"))

# Two events are considered "the same match" if their kickoff times are
# within this many minutes of each other. Books sometimes list slightly
# different start times for the same fixture.
MATCH_TIME_TOLERANCE_MINUTES = int(os.environ.get("MATCH_TIME_TOLERANCE_MINUTES", "30"))


# --------------------------------------------------------------------------- #
# Competitions to scrape
# --------------------------------------------------------------------------- #
# IMPORTANT: fill these in with real, *matching* competition pages — i.e. the
# same league/tournament on both books, or you'll never get a match between
# them. A good starting bet is a competition both Epicbet and Optibet are
# certain to carry, e.g. the Estonian Meistriliiga (football) — since Optibet
# is an Estonian book. Open both sites in a browser, navigate to the same
# league, and copy the competition-listing URL (not a single-match URL) into
# the pairs below.
#
# sport_key is just a free-text label that gets stored on the opportunity
# row (frontend already understands values like "soccer_estonia_meistriliiga",
# see backend/prisma/seed.js for existing examples) — it's not used for
# matching logic itself.


@dataclass(frozen=True)
class CompetitionPair:
    sport_key: str
    epicbet_url: str
    optibet_url: str


COMPETITIONS = [
    CompetitionPair(
        sport_key="soccer_estonia_meistriliiga",
        epicbet_url="https://epicbet.com/en/sports/football/estonia/meistriliiga",
        optibet_url="https://www.optibet.ee/en/sport/prematch/Meistriliiga-<FILL_IN_GROUP_ID>",
    ),
    # Add more pairs here as you validate them.
]
