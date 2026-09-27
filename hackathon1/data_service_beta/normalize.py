"""
Matching events across any number of books, without an LLM.

Normalize each team name (accents, case, punctuation) and group together
one event per book that all refer to the same real-world match — matched
by team names + a kickoff-time tolerance window.
"""

import re
import unicodedata


def normalize_team_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _names_match(a: str, b: str) -> bool:
    a, b = normalize_team_name(a), normalize_team_name(b)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def _same_match(event_a: dict, event_b: dict, tolerance_seconds: float) -> bool:
    time_diff = abs((event_a["commence_time"] - event_b["commence_time"]).total_seconds())
    if time_diff > tolerance_seconds:
        return False
    return _names_match(event_a["home_team"], event_b["home_team"]) and _names_match(
        event_a["away_team"], event_b["away_team"]
    )


def match_events(
    events_by_book: dict[str, list[dict]],
    time_tolerance_minutes: int = 30,
) -> list[dict[str, dict]]:
    """
    events_by_book: {"coolbet": [event, ...], "vivatbet": [event, ...], ...}

    Returns a list of "match groups" — each one a dict of
    {bookmaker_name: event} for whichever books had a matching event for
    that real-world match. A group only needs 2+ books to be useful for
    arbitrage; groups with just 1 book (no match found elsewhere) are
    dropped, since there's nothing to compare them against.
    """

    tolerance_seconds = time_tolerance_minutes * 60
    books = list(events_by_book.keys())
    if len(books) < 2:
        return []

    # Anchor on whichever book has the most events — arbitrary but keeps
    # the loop simple, and doesn't affect which groups get found.
    anchor_book = max(books, key=lambda b: len(events_by_book[b]))
    other_books = [b for b in books if b != anchor_book]

    used = {b: set() for b in other_books}
    groups = []

    for anchor_event in events_by_book[anchor_book]:
        group = {anchor_book: anchor_event}

        for book in other_books:
            match_index = None
            for i, event in enumerate(events_by_book[book]):
                if i in used[book]:
                    continue
                if _same_match(anchor_event, event, tolerance_seconds):
                    match_index = i
                    break
            if match_index is not None:
                used[book].add(match_index)
                group[book] = events_by_book[book][match_index]

        if len(group) >= 2:
            groups.append(group)

    return groups
