"""
Match sporting events across bookmaker data sources by comparing team names
via a local LLM (ollama).

Logic preserved from the original script:
  1. Load epicbet, coolbet and optibet event data from JSON files.
  2. Sort each source's events by (home_team, away_team).
  3. Take the first (alphabetically earliest) event from epicbet and coolbet.
  4. Ask the LLM whether those two team pairs refer to the same match.
  5. Print the resulting {"match": true/false} dict.

optibet is loaded and sorted for parity with the other sources but is not
part of the comparison, matching the original script's behavior.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import ollama

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

DATA_PATHS: Dict[str, Path] = {
    "epicbet": Path("matching_logic/epicbet/result_epicbet.json"),
    "coolbet": Path("matching_logic/coolbet/result_coolbet.json"),
    "optibet": Path("matching_logic/optibet/result_optibet.json"),
}

LLM_MODEL = "qwen3:0.6b"
LLM_MAX_RETRIES = 3

SYSTEM_PROMPT = """You are given two pairs of teams.

Pair 1 consists of team1 and team2.
Pair 2 consists of team1 and team2.

Determine whether:
- team1 from pair 1 is the same as team1 from pair 2
AND
- team2 from pair 1 is the same as team2 from pair 2.

Return ONLY valid JSON in this exact format:
{"match": true}

or:

{"match": false}
"""


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #

class DataLoadError(Exception):
    """Raised when a bookmaker data file cannot be loaded or parsed."""


class MatchServiceError(Exception):
    """Raised when the LLM matching service fails or returns an invalid payload."""


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class TeamPair:
    home_team: str
    away_team: str

    def as_tuple(self) -> Tuple[str, str]:
        return self.home_team, self.away_team


# --------------------------------------------------------------------------- #
# Loading & sorting
# --------------------------------------------------------------------------- #

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file, raising a descriptive error on failure."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise DataLoadError(f"Data file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DataLoadError(f"Invalid JSON in {path}: {exc}") from exc


def load_all_sources(paths: Dict[str, Path]) -> Dict[str, Dict[str, Any]]:
    """Load every configured bookmaker data source."""
    sources: Dict[str, Dict[str, Any]] = {}
    for name, path in paths.items():
        logger.info("Loading data source '%s' from %s", name, path)
        sources[name] = load_json_file(path)
    return sources


def sort_events_by_teams(events: Dict[str, Any]) -> Dict[str, Any]:
    """Sort events (keyed by event id) by (home_team, away_team)."""
    try:
        return dict(
            sorted(
                events.items(),
                key=lambda item: (item[1]["home_team"], item[1]["away_team"]),
            )
        )
    except KeyError as exc:
        raise DataLoadError(f"Event missing required team field: {exc}") from exc


def first_team_pair(sorted_events: Dict[str, Any]) -> TeamPair:
    """Return the TeamPair of the first (alphabetically earliest) event."""
    if not sorted_events:
        raise DataLoadError("No events available to extract a team pair from.")
    first_event = next(iter(sorted_events.values()))
    try:
        return TeamPair(home_team=first_event["home_team"], away_team=first_event["away_team"])
    except KeyError as exc:
        raise DataLoadError(f"Event missing required team field: {exc}") from exc


# --------------------------------------------------------------------------- #
# LLM matching
# --------------------------------------------------------------------------- #

def build_prompt(pair_a: TeamPair, pair_b: TeamPair) -> str:
    a1, a2 = pair_a.as_tuple()
    b1, b2 = pair_b.as_tuple()
    return (
        f'Pair 1: team1="{a1}", team2="{a2}"\n'
        f'Pair 2: team1="{b1}", team2="{b2}"'
    )


def call_llm_match(
    pair_a: TeamPair,
    pair_b: TeamPair,
    model: str = LLM_MODEL,
    max_retries: int = LLM_MAX_RETRIES,
) -> Dict[str, bool]:
    """Ask the LLM whether two team pairs refer to the same match.

    Retries on transient errors (connection issues, malformed JSON) and
    validates the shape of the returned payload before trusting it.
    """
    prompt = build_prompt(pair_a, pair_b)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            response = ollama.chat(model=model, messages=messages, format="json")
            raw_content = response.message.content
            result = json.loads(raw_content)

            if not isinstance(result, dict) or not isinstance(result.get("match"), bool):
                raise MatchServiceError(f"Unexpected LLM response shape: {raw_content!r}")

            return result

        except (json.JSONDecodeError, MatchServiceError) as exc:
            last_error = exc
            logger.warning("Attempt %d/%d: invalid LLM response (%s)", attempt, max_retries, exc)
        except Exception as exc:  # covers ollama connection/runtime errors
            last_error = exc
            logger.warning("Attempt %d/%d: LLM call failed (%s)", attempt, max_retries, exc)

    raise MatchServiceError(f"LLM matching failed after {max_retries} attempts") from last_error


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

def main() -> int:
    try:
        raw_sources = load_all_sources(DATA_PATHS)
    except DataLoadError as exc:
        logger.error("Failed to load data sources: %s", exc)
        return 1

    logger.debug("Loaded raw sources: %s", raw_sources)

    sorted_sources = {
        name: sort_events_by_teams(events) for name, events in raw_sources.items()
    }

    try:
        epic_pair = first_team_pair(sorted_sources["epicbet"])
        cool_pair = first_team_pair(sorted_sources["coolbet"])
        # optibet is loaded/sorted for parity with the other sources but is
        # not part of the current comparison, matching the original logic.
        _ = first_team_pair(sorted_sources["optibet"])
    except DataLoadError as exc:
        logger.error("Failed to extract team pairs: %s", exc)
        return 1

    try:
        result = call_llm_match(epic_pair, cool_pair)
    except MatchServiceError as exc:
        logger.error("Matching failed: %s", exc)
        return 1

    logger.info("Match result: %s", result)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())