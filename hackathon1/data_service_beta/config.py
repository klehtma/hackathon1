"""
Configuration for data_service_beta.
"""

import os
from dataclasses import dataclass, field

from scrapers import coolbet, optibet, vivatbet


# --------------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------------- #

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

RUN_ONCE = os.environ.get("RUN_ONCE", "true").lower() in ("1", "true", "yes")
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "120"))
MIN_PROFIT_PERCENT = float(os.environ.get("MIN_PROFIT_PERCENT", "0"))
MATCH_TIME_TOLERANCE_MINUTES = int(os.environ.get("MATCH_TIME_TOLERANCE_MINUTES", "30"))


# --------------------------------------------------------------------------- #
# Which scraper each bookmaker name maps to.
#
# Adding a new book later is: write scrapers/<book>.py with the same
# fetch_competition(driver, url, sport_key) -> list[dict] shape as the
# others, then add one line here.
# --------------------------------------------------------------------------- #

SCRAPERS = {
    "coolbet": coolbet.fetch_competition,
    "optibet": optibet.fetch_competition,
    "vivatbet": vivatbet.fetch_competition,
}


# --------------------------------------------------------------------------- #
# Competitions to scrape
# --------------------------------------------------------------------------- #
# Each entry is one real-world competition/league, with a URL per book you
# want scraped for it. You don't need every book for every competition —
# just include whichever ones you've confirmed carry that league. Matching
# and arbitrage then run across whichever books are present for that entry.


@dataclass(frozen=True)
class Competition:
    sport_key: str
    urls: dict = field(default_factory=dict)  # {bookmaker_name: competition_url}


COMPETITIONS = [
    Competition(
        sport_key="soccer_uefa_champions_league",
        urls={
            "vivatbet": "https://vivatbet.ee/et/line/football/118587-uefa-champions-league",
            # Add "coolbet": "..." here once you've got Coolbet's matching
            # competition-listing URL for the same tournament.
        },
    ),
    # Add more competitions here — same sport_key can appear multiple times
    # if you want to track several leagues under one label, but a distinct
    # sport_key per league is usually clearer.
]
