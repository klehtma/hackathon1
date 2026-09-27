"""
Turns a matched group of events (one per book, 2 or more) into an
ArbOpportunity dict ready for db.py — or returns None if there's no
arbitrage, or the books don't all cover the same set of outcomes.
"""

from datetime import datetime, timezone


def _best_price_per_role(group: dict[str, dict]) -> dict | None:
    events = list(group.values())
    roles_needed = {o["role"] for o in events[0]["outcomes"]}
    for event in events[1:]:
        if {o["role"] for o in event["outcomes"]} != roles_needed:
            return None  # market shapes don't match across books

    best = {}
    for event in events:
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


def compute_arbitrage(group: dict[str, dict], min_profit_percent: float = 0.0) -> dict | None:
    if len(group) < 2:
        return None

    best = _best_price_per_role(group)
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

    # Stable id regardless of dict ordering: sort by bookmaker name.
    any_event = next(iter(group.values()))
    match_id = "-".join(
        f"{book}:{event['external_id']}" for book, event in sorted(group.items())
    )

    return {
        "matchId": match_id,
        "homeTeam": any_event["home_team"],
        "awayTeam": any_event["away_team"],
        "commenceTime": any_event["commence_time"],
        "sportKey": any_event.get("sport_key"),
        "totalImpliedProbability": total_implied,
        "profitPercent": profit_percent,
        "detectedAt": datetime.now(timezone.utc),
        "legs": legs,
    }
