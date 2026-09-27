# data_service_beta

A stripped-down version of `data_service`, scraping **only Coolbet and
Optibet**, with no LLM anywhere in the pipeline:

- **Scraping** (`scrapers/coolbet.py`, `scrapers/optibet.py`) — same
  network-interception technique already proven in `data_service` (loading
  the page with Camoufox and grabbing the site's own internal JSON API
  responses), just collapsed into one direct pass with no intermediate
  files.
- **Matching** (`normalize.py`) — plain string normalization + a kickoff-time
  tolerance window instead of an LLM call. With only two books this is a
  much smaller problem than the general N-book case.
- **Arbitrage math** (`arbitrage.py`) — picks the best price per outcome
  across both books, computes total implied probability and per-leg stakes.
- **Storage** (`db.py`) — writes straight into the same `ArbOpportunity` /
  `ArbLeg` tables the backend's Prisma schema already defines, via raw SQL
  (no ORM needed for two tables).

## Before running this

1. **Fill in real competition URLs** in `config.py`. The placeholder pair
   needs a real Optibet group id — open both sites in a browser, navigate
   to the *same* league on each, and copy the competition-listing URLs (not
   a single match URL). Pick a league both books definitely carry — the
   comments in `config.py` suggest the Estonian Meistriliiga as a good bet.
2. **Double check the market names** `scrapers/coolbet.py` looks for
   (`PRIMARY_MARKET_NAMES`) actually match what your chosen sport calls its
   moneyline/match-result market — this was written against a basketball
   sample; a different sport might label it slightly differently.

## Wiring it into docker-compose.yaml

Add a new service (leave the old `data_service` as-is, or remove it if
you're fully replacing it):

```yaml
  data_service_beta:
    build:
      context: ./data_service_beta
      dockerfile: Dockerfile
    restart: unless-stopped
    env_file:
      - .env
    environment:
      DATA_SERVICE_DB_USER: ${DATA_SERVICE_DB_USER}
      DATA_SERVICE_DB_PASSWORD: ${DATA_SERVICE_DB_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_HOST: postgres
      RUN_ONCE: "false"
      POLL_INTERVAL_SECONDS: "120"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - data_network
```

It reuses the same `DATA_SERVICE_DB_USER` role your database init script
already creates, so no new DB permissions are needed.

## Running it once, manually, to test

```bash
docker compose run --rm -e RUN_ONCE=true data_service_beta
```

Watch the logs — every scraper and matching step prints what it found
(or why it skipped something), so a failed run should tell you exactly
which stage to look at.

## Known rough edges (hackathon-speed tradeoffs, not bugs)

- **Team-name matching is simple on purpose.** Exact-or-substring
  comparison after stripping accents/punctuation. Fine for two books on
  one league; will misfire more as you add leagues with very different
  naming conventions between books. An alias dictionary (see the earlier
  suggestion) is the next step up if this starts producing false negatives.
- **Coolbet still needs one page-load per match** to get prices, so it's
  the slower of the two scrapers. Optibet gets everything in one request.
- **No retries across the two scrapers' full run** — if Coolbet's listing
  call fails after its internal retries, that competition is just skipped
  for this cycle; it'll try again next `POLL_INTERVAL_SECONDS`.
