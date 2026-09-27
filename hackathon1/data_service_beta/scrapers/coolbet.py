"""
Coolbet scraper.

Coolbet's competition page needs two network calls to get a fully-priced
match:
  1. The competition listing call (gives match ids, team names, kickoff
     times, and the *shape* of each market — outcome ids and names, but
     no prices).
  2. A per-match call (gives outcome_id -> price for that one match).

This mirrors the working approach already in data_service/scraping/coolbet
(proven against real responses, see the sample JSON files in that folder) —
just collapsed into one direct in-memory pass instead of a multi-stage
file-based pipeline, and with the LLM step removed since we don't need it
for exactly two books.
"""

from datetime import datetime

BOOKMAKER = "Coolbet"

# Market names that represent the plain match-winner / moneyline market,
# across the sports Coolbet lists. Extend this list if you scrape a sport
# whose market is named something else — check a saved listing response
# for the market["name"] your competition actually uses.
PRIMARY_MARKET_NAMES = {
    "money line",
    "match result",
    "1x2",
    "full time result",
    "match winner",
}


def _role_from_result_key(result_key: str) -> str:
    key = (result_key or "").lower()
    if "home" in key:
        return "home"
    if "away" in key:
        return "away"
    return "draw"


def _find_primary_market(match: dict) -> dict | None:
    for market in match.get("markets", []):
        name = (market.get("name") or "").strip().lower()
        if name in PRIMARY_MARKET_NAMES:
            return market
    return None


def _fetch_listing(driver, competition_url: str, tries: int = 3) -> dict | None:
    for attempt in range(tries):
        try:
            with driver.expect_response(
                lambda r: "country=EE" in r.url and "limit=6" in r.url,
                timeout=10000,
            ) as response_info:
                driver.goto(competition_url)
            return response_info.value.json()
        except Exception as e:
            print(f"[coolbet] listing attempt {attempt + 1}/{tries} failed: {e}")
    return None


def _fetch_match_prices(driver, match_id, tries: int = 3) -> dict:
    """Returns a dict of outcome_id -> price for one match, using the same
    fo / fo-line endpoints the site itself uses when you open a match page."""
    match_url = f"https://www.coolbet.com/en/sports/match/{match_id}"

    for attempt in range(tries):
        responses = {}

        def handle_response(response):
            path = response.url.split("?")[0]
            if path.endswith("/s/sb-odds/odds/current/fo"):
                responses["fo"] = response
            elif path.endswith("/s/sb-odds/odds/current/fo-line/") or path.endswith(
                "/s/sb-odds/odds/current/fo-line"
            ):
                responses["fo-line"] = response

        try:
            driver.on("response", handle_response)
            driver.goto(match_url, wait_until="domcontentloaded")

            import time

            start = time.time()
            while time.time() - start < 10 and len(responses) < 2:
                time.sleep(0.2)

            prices = {}
            for name in ("fo", "fo-line"):
                if name not in responses:
                    continue
                try:
                    for outcome_id, entry in responses[name].json().items():
                        prices[int(outcome_id)] = entry.get("value")
                except Exception as e:
                    print(f"[coolbet] could not parse {name} for match {match_id}: {e}")

            if prices:
                return prices
            print(f"[coolbet] no price data for match {match_id}, attempt {attempt + 1}/{tries}")
        except Exception as e:
            print(f"[coolbet] price fetch failed for match {match_id}: {e}")
        finally:
            try:
                driver.remove_listener("response", handle_response)
            except Exception:
                pass

    return {}


def fetch_competition(driver, competition_url: str, sport_key: str) -> list[dict]:
    """Returns a list of normalized match dicts, see arbitrage.py for the
    shared shape every scraper must return."""

    listing = _fetch_listing(driver, competition_url)
    if not listing:
        print(f"[coolbet] giving up on {competition_url} — no listing data")
        return []

    matches = []
    for category in listing.get("categories", []):
        matches.extend(category.get("matches", []))

    results = []
    for match in matches:
        market = _find_primary_market(match)
        if not market:
            continue

        outcomes = market.get("outcomes", [])
        outcome_ids = [o["id"] for o in outcomes]

        prices = _fetch_match_prices(driver, match["id"])
        if not prices or any(oid not in prices for oid in outcome_ids):
            print(f"[coolbet] skipping match {match['id']} — incomplete prices")
            continue

        try:
            commence_time = datetime.fromisoformat(match["match_start"])
        except Exception as e:
            print(f"[coolbet] skipping match {match['id']} — bad match_start: {e}")
            continue

        home_team = match["home_team_name"].strip()
        away_team = match["away_team_name"].strip()

        priced_outcomes = [
            {
                "role": _role_from_result_key(o.get("result_key", "")),
                "name": o["name"].strip(),
                "price": prices[o["id"]],
            }
            for o in outcomes
        ]

        results.append(
            {
                "bookmaker": BOOKMAKER,
                "external_id": str(match["id"]),
                "home_team": home_team,
                "away_team": away_team,
                "commence_time": commence_time,
                "sport_key": sport_key,
                "outcomes": priced_outcomes,
            }
        )

    print(f"[coolbet] {competition_url}: {len(results)}/{len(matches)} matches fully priced")
    return results
