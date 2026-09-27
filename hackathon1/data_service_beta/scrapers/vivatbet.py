"""
Vivatbet scraper.

Like Optibet, one request to a competition/league page gets every match on
that page fully priced — no second per-match request needed.

The page URL looks like:
    https://vivatbet.ee/et/line/football/118587-uefa-champions-league
                                          ^^^^^^ champ id, a leading number
before the slug. Loading that page triggers an XHR to
".../service-api/main-line-feed/v3/games1x2?...&champId=118587...", which
returns every match in that competition with a 1X2 market already priced
(events under eventGroups where groupId == 1, with type 1/2/3 = home/draw/
away — confirmed against real sample data: e.g. a heavy home favourite
shows a low price under type 1, a heavy away favourite shows a low price
under type 3).

The site protects this endpoint with a signed `x-hd` header that appears
to be generated client-side per session/request — we don't attempt to
reproduce it. Camoufox loads the real page in a real browser, the page's
own JS builds that header, and we just intercept whatever comes back.
"""

import re
from datetime import datetime, timezone

BOOKMAKER = "Vivatbet"

_ROLE_BY_TYPE = {1: "home", 2: "draw", 3: "away"}


def _champ_id_from_url(url: str) -> str | None:
    # e.g. ".../line/football/118587-uefa-champions-league" -> "118587"
    match = re.search(r"/(\d+)-[^/]+/?$", url.strip())
    return match.group(1) if match else None


def _fetch_listing(driver, competition_url: str, champ_id: str, tries: int = 3) -> list | None:
    for attempt in range(tries):
        try:
            with driver.expect_response(
                lambda r: "games1x2" in r.url and f"champId={champ_id}" in r.url,
                timeout=10000,
            ) as response_info:
                driver.goto(competition_url)
            return response_info.value.json()
        except Exception as e:
            print(f"[vivatbet] listing attempt {attempt + 1}/{tries} failed: {e}")
    return None


def fetch_competition(driver, competition_url: str, sport_key: str) -> list[dict]:
    champ_id = _champ_id_from_url(competition_url)
    if not champ_id:
        print(f"[vivatbet] could not find a champ id in {competition_url!r} — "
              f"expected it to end in '<digits>-some-slug'")
        return []

    matches = _fetch_listing(driver, competition_url, champ_id)
    if not matches:
        print(f"[vivatbet] giving up on {competition_url} — no listing data")
        return []

    results = []
    for match in matches:
        primary_group = next(
            (g for g in match.get("eventGroups", []) if g.get("groupId") == 1), None
        )
        if not primary_group:
            continue

        # Each entry in "events" is itself a one-item list, e.g. [{"type": 1, "cf": 2.47}]
        prices_by_type = {}
        for entry in primary_group.get("events", []):
            for outcome in entry:
                prices_by_type[outcome["type"]] = outcome["cf"]

        if set(prices_by_type) != {1, 2, 3}:
            print(f"[vivatbet] skipping match {match.get('id')} — incomplete 1X2 market")
            continue

        try:
            commence_time = datetime.fromtimestamp(match["startTs"], tz=timezone.utc)
        except Exception as e:
            print(f"[vivatbet] skipping match {match.get('id')} — bad startTs: {e}")
            continue

        home_team = match["opponent1"]["fullNameEng"].strip()
        away_team = match["opponent2"]["fullNameEng"].strip()

        priced_outcomes = [
            {
                "role": _ROLE_BY_TYPE[type_],
                "name": home_team if type_ == 1 else away_team if type_ == 3 else "Draw",
                "price": price,
            }
            for type_, price in prices_by_type.items()
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

    print(f"[vivatbet] {competition_url}: {len(results)}/{len(matches)} matches fully priced")
    return results
