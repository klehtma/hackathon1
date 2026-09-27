"""
Epicbet scraper.

Like Coolbet, Epicbet needs two network calls to get a fully-priced match:
  1. The competition listing call (`match.getFoByLeague`) gives match ids,
     team names, and kickoff times for every event in the league.
  2. A per-match page load, which triggers two more calls: `match.Get`
     (the market/outcome shape, including each team's id so we can tell
     home from away) and one or more `activeOdds` calls (outcome_id ->
     price).

This mirrors the working approach already in data_service/scraping/epicbet
(proven against real responses, see the sample JSON files in that folder) —
just collapsed into one direct in-memory pass instead of a multi-stage
file-based pipeline.
"""

import time
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

BOOKMAKER = "Epicbet"

# Market-group names that represent the plain match-winner / moneyline
# market, across the sports Epicbet lists. Extend this if you scrape a
# sport whose market is named something else — check a saved match.Get
# response for the marketGroup["name"] your competition actually uses.
PRIMARY_MARKET_NAMES = {"1x2", "moneyline", "money line", "match winner"}


def _match_url(competition_url: str, match_id) -> str:
    """Epicbet loads a specific match by adding ?matchId=<id> to a bare
    sport/country URL, e.g.
    https://epicbet.com/en/sports/football/spain?matchId=2092634 — note
    there's no league slug on that URL. Competition (listing) URLs have
    one extra path segment for the league, so we drop it here."""
    parsed = urlparse(competition_url)
    segments = [s for s in parsed.path.split("/") if s]
    # Expect .../sports/<sport>/<country>/<league-slug> -> keep the first
    # four segments (.../sports/<sport>/<country>).
    base_path = "/" + "/".join(segments[:4])
    base = urlunparse((parsed.scheme, parsed.netloc, base_path, "", "", ""))
    return f"{base}?matchId={match_id}"


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


def _fetch_match_data(driver, match_url: str, tries: int = 3) -> tuple[dict | None, dict]:
    """Returns (match.Get data, outcome_id -> price dict) for one match."""
    for attempt in range(tries):
        responses = {"activeOdds": [], "match_get": None}

        def handle_response(response):
            path = response.url.split("?")[0]
            if "/s/core-proxy/public/sport-odds/activeOdds" in path:
                responses["activeOdds"].append(response)
            elif "/s/core-proxy/public/sport-base/match.getSidebets" in path:
                responses["match_get"] = response

        try:
            driver.on("response", handle_response)
            driver.goto(match_url, wait_until="domcontentloaded")

            # Wait out the full timeout so we catch every activeOdds call,
            # not just the first one (same reasoning as data_service's
            # original get_page.py).
            start = time.time()
            while time.time() - start < 10:
                time.sleep(0.2)

            if not responses["activeOdds"] or responses["match_get"] is None:
                print(
                    f"[epicbet] incomplete responses for {match_url}, "
                    f"attempt {attempt + 1}/{tries}"
                )
                continue

            match_data = responses["match_get"].json()["result"]["data"]

            prices = {}
            for response in responses["activeOdds"]:
                try:
                    for entry in response.json()["result"]["data"]:
                        prices[entry["outcomeId"]] = entry["value"]
                except Exception as e:
                    print(f"[epicbet] could not parse activeOdds for {match_url}: {e}")

            if prices:
                return match_data, prices
        except Exception as e:
            print(f"[epicbet] page fetch failed for {match_url}: {e}")
        finally:
            try:
                driver.remove_listener("response", handle_response)
            except Exception:
                pass

    return None, {}


def _find_primary_market_group(match_data: dict) -> dict | None:
    for group in match_data.get("marketGroups", []):
        name = (group.get("name") or "").strip().lower()
        if name in PRIMARY_MARKET_NAMES:
            return group
    return None


def _role_from_outcome(outcome: dict, home_team_id, away_team_id) -> str:
    team_id = outcome.get("teamId")
    if team_id == home_team_id:
        return "home"
    if team_id == away_team_id:
        return "away"
    return "draw"  # the draw outcome carries no teamId


def fetch_competition(driver, competition_url: str, sport_key: str) -> list[dict]:
    """Returns a list of normalized match dicts, see arbitrage.py for the
    shared shape every scraper must return."""

    listing = _fetch_listing(driver, competition_url)
    if not listing:
        print(f"[epicbet] giving up on {competition_url} — no listing data")
        return []

    matches = listing.get("result", {}).get("data", {}).get("matches", [])

    results = []
    for match in matches:
        match_url = _match_url(competition_url, match["id"])
        match_data, prices = _fetch_match_data(driver, match_url)
        if not match_data or not prices:
            print(f"[epicbet] skipping match {match['id']} — incomplete data")
            continue

        group = _find_primary_market_group(match_data)
        if not group or not group.get("markets"):
            print(f"[epicbet] skipping match {match['id']} — no moneyline market")
            continue

        outcomes = group["markets"][0].get("outcomes", [])
        if not outcomes or any(o["id"] not in prices for o in outcomes):
            print(f"[epicbet] skipping match {match['id']} — incomplete prices")
            continue

        try:
            commence_time = datetime.fromisoformat(match["startDate"]).astimezone(timezone.utc)
        except Exception as e:
            print(f"[epicbet] skipping match {match['id']} — bad startDate: {e}")
            continue

        home_team = match["homeTeamName"].strip()
        away_team = match["awayTeamName"].strip()
        home_team_id = match_data.get("homeTeamId")
        away_team_id = match_data.get("awayTeamId")

        priced_outcomes = [
            {
                "role": _role_from_outcome(o, home_team_id, away_team_id),
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
