"""
Matching two books' events to each other without an LLM.

With only two books, this doesn't need to be fancy: normalize each team
name (accents, case, punctuation) and pair up events whose home+away teams
both normalize to the same (or a containing) string, and whose kickoff
times are within a small tolerance of each other.
"""

import re
import unicodedata


def normalize_team_name(name: str) -> str:
    # Strip accents (e.g. "München" -> "munchen") so books that spell the
    # same club differently still line up.
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # drop punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _names_match(a: str, b: str) -> bool:
    a, b = normalize_team_name(a), normalize_team_name(b)
    if not a or not b:
        return False
    # Exact match, or one is a substring of the other (handles e.g.
    # "Bayern Munich" vs "FC Bayern Munich", "Man Utd" vs "Manchester United"
    # only partially — for real coverage you'd want an alias table, but this
    # covers most common cases with zero maintenance).
    return a == b or a in b or b in a


def match_events(
    events_a: list[dict],
    events_b: list[dict],
    time_tolerance_minutes: int = 30,
) -> list[tuple[dict, dict]]:
    """Greedy pairing: each event from `a` is matched to at most one event
    from `b`, and vice versa."""

    tolerance = time_tolerance_minutes * 60
    used_b = set()
    pairs = []

    for event_a in events_a:
        best_match = None
        for i, event_b in enumerate(events_b):
            if i in used_b:
                continue

            time_diff = abs((event_a["commence_time"] - event_b["commence_time"]).total_seconds())
            if time_diff > tolerance:
                continue

            if _names_match(event_a["home_team"], event_b["home_team"]) and _names_match(
                event_a["away_team"], event_b["away_team"]
            ):
                best_match = i
                break

        if best_match is not None:
            used_b.add(best_match)
            pairs.append((event_a, events_b[best_match]))

    return pairs
