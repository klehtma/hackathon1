"""
Epicbet scraper.

Same two-step pattern as Coolbet:
  1. The competition listing call (matches "match.getFoByLeague?input=%")
     gives match ids, team names, kickoff times, and each match's "Money
     Line" market shape (outcome ids + team names, no prices).
  2. A per-match page load (URL = "<competition_url>?matchId=<id>")
     triggers one or more "activeOdds" calls giving outcome_id -> price.

Built from real captured samples in the original data_service/scraping/
epicbet folder (get_urls_data/, get_page_data/) — same technique, LLM step
removed, collapsed into one direct in-memory pass.
"""

import time
from datetime import datetime

BOOKMAKER = "Epicbet"

PRIMARY_MARKET_NAMES = {
    "money line",
    "match result",
    "1x2",
    "full time result",
    "match winner",
}


def _find_primary_market(match: dict) -> dict | None:
    for group in match.get("marketGroups", []):
        name = (group.get("name") or "").strip().lower()
        if name in PRIMARY_MARKET_NAMES:
            markets = group.get("markets", [])
            if markets:
                return markets[0]  # the un-handicapped, straight-up market
    return None


def _role_for_outcome(outcome: dict, match: dict) -> str:
    if outcome.get("teamId") == match.get("homeTeamId"):
        return "home"
    if outcome.get("teamId") == match.get("awayTeamId"):
        return "away"
    return "draw"


def _fetch_listing(driver, competition_url: str, tries: int = 3) -> dict | None:
    for attempt in range(tries):
        try:
            with driver.expect_response(
                lambda r: "public/sport-base/match.getFoByLeague?input=%" in r.url,
                timeout=20000,
            ) as response_info:
                driver.goto(competition_url)
            return response_info.value.json()
        except Exception as e:
            print(f"[epicbet] listing attempt {attempt + 1}/{tries} failed: {e}")
    return None


def _fetch_match_prices(driver, competition_url: str, match_id, tries: int = 3) -> dict:
    """Returns a dict of outcome_id -> price for one match."""
    match_url = f"{competition_url}?matchId={match_id}"

    for attempt in range(tries):
        active_odds_responses = []

        def handle_response(response):
            if "/s/core-proxy/public/sport-odds/activeOdds" in response.url:
                active_odds_responses.append(response)

        try:
            driver.on("response", handle_response)
            driver.goto(match_url, wait_until="domcontentloaded")

            start = time.time()
            while time.time() - start < 10:
                time.sleep(0.2)

            prices = {}
            for response in active_odds_responses:
                try:
                    for entry in response.json()["result"]["data"]:
                        prices[entry["outcomeId"]] = entry["value"]
                except Exception as e:
                    print(f"[epicbet] could not parse an activeOdds response: {e}")

            if prices:
                return prices
            print(f"[epicbet] no price data for match {match_id}, attempt {attempt + 1}/{tries}")
        except Exception as e:
            print(f"[epicbet] price fetch failed for match {match_id}: {e}")
        finally:
            try:
                driver.remove_listener("response", handle_response)
            except Exception:
                pass

    return {}


def fetch_competition(driver, competition_url: str, sport_key: str) -> list[dict]:
    listing = _fetch_listing(driver, competition_url)
    if not listing:
        print(f"[epicbet] giving up on {competition_url} — no listing data")
        return []

    matches = listing.get("result", {}).get("data", {}).get("matches", [])

    results = []
    for match in matches:
        market = _find_primary_market(match)
        if not market:
            continue

        outcomes = market.get("outcomes", [])
        outcome_ids = [o["id"] for o in outcomes]

        prices = _fetch_match_prices(driver, competition_url, match["id"])
        if not prices or any(oid not in prices for oid in outcome_ids):
            print(f"[epicbet] skipping match {match['id']} — incomplete prices")
            continue

        try:
            # e.g. "2026-09-25 16:30:00+00" — Postgres-style offset, not quite
            # ISO 8601 ("+00" needs to become "+00:00" for fromisoformat).
            raw = match["startDate"]
            if raw.endswith("+00"):
                raw = raw + ":00"
            commence_time = datetime.fromisoformat(raw)
        except Exception as e:
            print(f"[epicbet] skipping match {match['id']} — bad startDate: {e}")
            continue

        home_team = match["homeTeamName"].strip()
        away_team = match["awayTeamName"].strip()

        priced_outcomes = [
            {
                "role": _role_for_outcome(o, match),
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

    print(f"[epicbet] {competition_url}: {len(results)}/{len(matches)} matches fully priced")
    return results
