"""
Optibet scraper.

Unlike Coolbet, Optibet's competition-group listing call already embeds
full odds for the main "Match" market for every event in one response —
no second per-match request needed. That makes this scraper both simpler
and faster than Coolbet's.
"""

import re
from datetime import datetime, timezone

BOOKMAKER = "Optibet"


def _role_from_odd(odd: dict) -> str:
    name = (odd.get("name") or "").strip().upper()
    if name == "1":
        return "home"
    if name == "2":
        return "away"
    return "draw"  # covers "X" and anything unexpected


def _group_id_from_url(url: str) -> str | None:
    # Competition URLs look like ".../Meistriliiga-21181" — take the
    # trailing numeric id.
    match = re.search(r"-(\d+)\s*$", url.strip())
    return match.group(1) if match else None


def _fetch_listing(driver, competition_url: str, group_id: str, tries: int = 3) -> list | None:
    expected = f"events/group/{group_id}?gameType=-1&domainId=1"
    for attempt in range(tries):
        try:
            with driver.expect_response(
                lambda r: expected in r.url,
                timeout=10000,
            ) as response_info:
                driver.goto(competition_url)
            return response_info.value.json()
        except Exception as e:
            print(f"[optibet] listing attempt {attempt + 1}/{tries} failed: {e}")
    return None


def fetch_competition(driver, competition_url: str, sport_key: str) -> list[dict]:
    group_id = _group_id_from_url(competition_url)
    if not group_id:
        print(f"[optibet] could not find a group id in {competition_url!r} — "
              f"expected it to end in '-<digits>'")
        return []

    events = _fetch_listing(driver, competition_url, group_id)
    if not events:
        print(f"[optibet] giving up on {competition_url} — no listing data")
        return []

    results = []
    for event in events:
        main_game = next((g for g in event.get("games", []) if g.get("type") == "match"), None)
        if not main_game or not main_game.get("odds"):
            continue

        try:
            commence_time = datetime.fromtimestamp(event["time"], tz=timezone.utc)
        except Exception as e:
            print(f"[optibet] skipping event {event.get('id')} — bad time: {e}")
            continue

        home_team = event["player1"]["name"].strip()
        away_team = event["player2"]["name"].strip()

        priced_outcomes = [
            {
                "role": _role_from_odd(odd),
                "name": odd.get("representationName") or odd["name"],
                "price": odd["value"],
            }
            for odd in main_game["odds"]
        ]

        results.append(
            {
                "bookmaker": BOOKMAKER,
                "external_id": str(event["id"]),
                "home_team": home_team,
                "away_team": away_team,
                "commence_time": commence_time,
                "sport_key": sport_key,
                "outcomes": priced_outcomes,
            }
        )

    print(f"[optibet] {competition_url}: {len(results)}/{len(events)} matches fully priced")
    return results
