"""
Turns a matched pair of events (one per book) into an ArbOpportunity dict
ready for db.py — or returns None if there's no arbitrage, or the two
books don't cover the same set of outcomes (e.g. one is 2-way, one is
3-way, which shouldn't normally happen for the same real-world match, but
scrapers can return partial data).
"""

from datetime import datetime, timezone


def _best_price_per_role(event_a: dict, event_b: dict) -> dict | None:
    roles_needed = {o["role"] for o in event_a["outcomes"]}
    if roles_needed != {o["role"] for o in event_b["outcomes"]}:
        return None  # market shapes don't match (e.g. 2-way vs 3-way)

    best = {}
    for event in (event_a, event_b):
        for outcome in event["outcomes"]:
            role = outcome["role"]
            candidate = {
                "bookmaker": event["bookmaker"],
                "name": outcome["name"],
                "price": outcome["price"],
            }
            if role not in best or candidate["price"] > best[role]["price"]:
                best[role] = candidate

    if set(best.keys()) != roles_needed:
        return None
    return best


def compute_arbitrage(event_a: dict, event_b: dict, min_profit_percent: float = 0.0) -> dict | None:
    best = _best_price_per_role(event_a, event_b)
    if not best:
        return None

    total_implied = sum(1 / leg["price"] for leg in best.values())
    profit_percent = (1 / total_implied - 1) * 100

    if profit_percent < min_profit_percent:
        return None

    legs = [
        {
            "outcomeName": leg["name"],
            "bookmaker": leg["bookmaker"],
            "price": leg["price"],
            "stakePercent": (1 / leg["price"]) / total_implied * 100,
        }
        for leg in best.values()
    ]

    match_id = (
        f"{event_a['bookmaker'].lower()}-{event_a['external_id']}-"
        f"{event_b['bookmaker'].lower()}-{event_b['external_id']}"
    )

    return {
        "matchId": match_id,
        "homeTeam": event_a["home_team"],
        "awayTeam": event_a["away_team"],
        "commenceTime": event_a["commence_time"],
        "sportKey": event_a.get("sport_key"),
        "totalImpliedProbability": total_implied,
        "profitPercent": profit_percent,
        "detectedAt": datetime.now(timezone.utc),
        "legs": legs,
    }
