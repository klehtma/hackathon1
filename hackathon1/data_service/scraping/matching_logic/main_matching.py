from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import requests


# ============================================================
# Configuration
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:0.6b"

CACHE_DB = Path("match_resolution_cache.sqlite3")

# If True, home/away are considered directional.
# For basketball this should normally remain True:
# Team A vs Team B != Team B vs Team A.
#
# NOTE: this assumes every source reports home/away consistently for
# the same real-world game. If two sources ever disagree on which
# team was "home" for the same fixture, this pipeline will treat them
# as different games. That's a data-quality assumption, not something
# fixable purely in code without ground truth on venue/orientation.
HOME_AWAY_DIRECTIONAL = True

# Minimum LLM confidence required to accept a resolution as final.
# Anything below this is NOT auto-merged and NOT auto-rejected -- it
# is routed into the "needs_review" bucket for a human to check. This
# is the main lever controlling how conservative the pipeline is.
MIN_CONFIDENCE = 0.75

# Two fixtures are only ever considered *candidates* for being the
# same game if their dates are within this many days of each other.
# This is what prevents two genuinely different games between the
# same two teams (e.g. a home-and-away league schedule, a two-legged
# cup tie) from ever being compared as if they might be duplicates.
#
# Keep this at 0 unless you know some sources log late-night kickoffs
# under the following calendar day in a different timezone than
# others -- in which case 1 is usually enough.
DATE_TOLERANCE_DAYS = 0


# ============================================================
# Data model
# ============================================================

@dataclass(frozen=True)
class Match:
    source: str
    source_id: str
    home_team: str
    away_team: str
    match_date: date  # required: see _parse_date for why


@dataclass(frozen=True)
class Resolution:
    is_match: bool
    confidence: float
    reason: str
    needs_review: bool = False


class LLMResolutionError(RuntimeError):
    """Raised when the LLM can't be reached or returns something unusable."""


# ============================================================
# Team-name normalization
# ============================================================

# Words that frequently occur in league/team naming variations.
#
# Do NOT aggressively remove arbitrary words here. The LLM should
# handle ambiguous cases.
TEAM_ALIASES = {
    "ratiopharm ulm": "ulm",
    "telekom baskets bonn": "bonn",
    "romerstrom gladiators trier": "gladiators trier",
    "gladiators trier": "gladiators trier",
    "phoenix hagen": "phoenix hagen",
    "sc jena": "jena",
    "mbc": "mbc",
    "besiktas": "besiktas",
    "valencia basket": "valencia",
    "fenerbahce": "fenerbahce",
    "virtus bologna": "virtus bologna",
    "partizan belgrade": "partizan belgrade",
    "olimpia milano": "olimpia milano",
    "kauno zalgiris": "zalgiris",
    "olympiacos pireaus": "olympiacos",
}


def normalize_text(value: str) -> str:
    """
    Conservative normalization.

    Important:
    We intentionally do NOT perform aggressive fuzzy matching here.
    This function exists to make cache keys stable.
    """
    value = unicodedata.normalize("NFKD", value)

    # Remove accents.
    value = "".join(
        char for char in value
        if not unicodedata.combining(char)
    )

    value = value.lower().strip()

    # Normalize punctuation.
    value = re.sub(r"[^\w\s]", " ", value)

    # Collapse whitespace.
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_team_name(team: str) -> str:
    normalized = normalize_text(team)

    return TEAM_ALIASES.get(normalized, normalized)


def canonical_pair(home: str, away: str) -> tuple[str, str]:
    """
    Canonical representation of a home/away team pair.

    We retain home/away direction because basketball fixtures are
    directional. NOTE: this does not include the date -- callers that
    need to identify a specific fixture (not just a team pairing)
    must combine this with match_date. See canonical_fixture_key.
    """
    home = normalize_team_name(home)
    away = normalize_team_name(away)

    if HOME_AWAY_DIRECTIONAL:
        return home, away

    return tuple(sorted((home, away)))


def canonical_key(home: str, away: str) -> str:
    home, away = canonical_pair(home, away)
    return f"{home}|||{away}"


def canonical_fixture_key(match: Match) -> tuple[str, str, str]:
    """
    Canonical representation of a *specific fixture*: team pairing
    AND date. Two fixtures should only ever be considered identical
    (deterministically, without an LLM call) if this whole tuple
    matches -- team names alone are not enough, because the same two
    teams can legitimately play more than once.
    """
    home, away = canonical_pair(match.home_team, match.away_team)
    return home, away, match.match_date.isoformat()


# ============================================================
# Flatten input dictionaries
# ============================================================

def _parse_date(value: Any, *, source: str, source_id: str) -> date:
    if value is None or value == "":
        raise ValueError(
            f"Missing 'date' field for {source}:{source_id}. A date is "
            "required for every fixture -- without it, two different "
            "games between the same two teams (e.g. a home/away league "
            "pair, or a rematch) cannot be told apart and would be "
            "wrongly merged as duplicates."
        )

    if isinstance(value, date):
        return value

    text = str(value).strip()

    try:
        # Accepts both plain dates ("2024-11-02") and full ISO
        # timestamps ("2024-11-02T20:00:00") by taking the date part.
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(
            f"Could not parse date {text!r} for {source}:{source_id}. "
            "Expected an ISO date or datetime string, e.g. "
            "'2024-11-02' or '2024-11-02T20:00:00'."
        ) from exc


def flatten_dataset(
    dataset_name: str,
    dataset: dict[str, dict[str, Any]],
) -> list[Match]:
    result: list[Match] = []

    for source_id, match in dataset.items():
        source_id = str(source_id)

        result.append(
            Match(
                source=dataset_name,
                source_id=source_id,
                home_team=match["home_team"],
                away_team=match["away_team"],
                match_date=_parse_date(
                    match.get("date"),
                    source=dataset_name,
                    source_id=source_id,
                ),
            )
        )

    return result


def flatten_all(
    datasets: dict[str, dict[str, dict[str, Any]]],
) -> list[Match]:
    matches: list[Match] = []

    for dataset_name, dataset in datasets.items():
        matches.extend(
            flatten_dataset(dataset_name, dataset)
        )

    # Required sorting.
    matches.sort(
        key=lambda m: (
            normalize_team_name(m.home_team),
            normalize_team_name(m.away_team),
            m.match_date,
            m.source,
            m.source_id,
        )
    )

    return matches


# ============================================================
# SQLite cache
# ============================================================

class ResolutionCache:
    def __init__(self, path: Path):
        self.path = path

        self.connection = sqlite3.connect(
            self.path,
            timeout=30,
        )

        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")

        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS match_resolution (
                cache_key TEXT PRIMARY KEY,

                home_team_a TEXT NOT NULL,
                away_team_a TEXT NOT NULL,
                date_a TEXT NOT NULL DEFAULT '',

                home_team_b TEXT NOT NULL,
                away_team_b TEXT NOT NULL,
                date_b TEXT NOT NULL DEFAULT '',

                is_match INTEGER NOT NULL,
                confidence REAL NOT NULL,
                needs_review INTEGER NOT NULL DEFAULT 0,
                reason TEXT NOT NULL,

                model TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Lightweight migration in case an older cache DB (from before
        # dates/needs_review existed) is reused. Old rows simply won't
        # match the new cache-key format (which now embeds dates) and
        # will be recomputed -- that's safe, just a cache miss, never
        # a wrong answer.
        existing_cols = {
            row[1]
            for row in self.connection.execute(
                "PRAGMA table_info(match_resolution)"
            ).fetchall()
        }

        migrations = {
            "date_a": (
                "ALTER TABLE match_resolution "
                "ADD COLUMN date_a TEXT NOT NULL DEFAULT ''"
            ),
            "date_b": (
                "ALTER TABLE match_resolution "
                "ADD COLUMN date_b TEXT NOT NULL DEFAULT ''"
            ),
            "needs_review": (
                "ALTER TABLE match_resolution "
                "ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0"
            ),
        }

        for column, statement in migrations.items():
            if column not in existing_cols:
                self.connection.execute(statement)

        self.connection.commit()

    def get(
        self,
        cache_key: str,
    ) -> Resolution | None:
        row = self.connection.execute(
            """
            SELECT
                is_match,
                confidence,
                reason,
                needs_review
            FROM match_resolution
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()

        if row is None:
            return None

        return Resolution(
            is_match=bool(row[0]),
            confidence=float(row[1]),
            reason=row[2],
            needs_review=bool(row[3]),
        )

    def put(
        self,
        cache_key: str,
        match_a: Match,
        match_b: Match,
        resolution: Resolution,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO match_resolution (
                cache_key,
                home_team_a,
                away_team_a,
                date_a,
                home_team_b,
                away_team_b,
                date_b,
                is_match,
                confidence,
                needs_review,
                reason,
                model
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(cache_key)
            DO UPDATE SET
                is_match = excluded.is_match,
                confidence = excluded.confidence,
                needs_review = excluded.needs_review,
                reason = excluded.reason,
                model = excluded.model
            """,
            (
                cache_key,
                match_a.home_team,
                match_a.away_team,
                match_a.match_date.isoformat(),
                match_b.home_team,
                match_b.away_team,
                match_b.match_date.isoformat(),
                int(resolution.is_match),
                resolution.confidence,
                int(resolution.needs_review),
                resolution.reason,
                OLLAMA_MODEL,
            ),
        )

        self.connection.commit()

    def close(self) -> None:
        self.connection.close()


# ============================================================
# Qwen resolver
# ============================================================

class QwenMatchResolver:
    def __init__(
        self,
        url: str = OLLAMA_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = 60,
    ):
        self.url = url
        self.model = model
        self.timeout = timeout

        self.session = requests.Session()

    def resolve(
        self,
        a: Match,
        b: Match,
    ) -> Resolution:
        """
        Ask the LLM whether two fixtures are the same game.

        Raises LLMResolutionError on any network failure, malformed
        response, or missing/invalid fields, so callers can isolate
        the failure to this one pair instead of crashing the whole
        batch.
        """

        prompt = f"""
You are an entity-resolution system for sports fixtures.

Determine whether these two fixtures represent the SAME sports game.

Fixture A:
Home: {a.home_team}
Away: {a.away_team}
Date: {a.match_date.isoformat()}

Fixture B:
Home: {b.home_team}
Away: {b.away_team}
Date: {b.match_date.isoformat()}

Rules:
- Different spellings or abbreviations of the same team are allowed.
- Sponsor names may be present in one name and absent in another.
- League/team branding differences are allowed.
- Home and away teams must correspond.
- The dates are close together but may not be byte-identical
  (e.g. timezone logging differences); if the teams clearly match
  but the date differs by more than a day, treat it as NOT a match,
  since it is more likely a genuinely different fixture (rematch,
  home/away leg) than a data error.
- Do not assume two teams are identical merely because one word matches.
- If you are not confident, reflect that honestly in "confidence"
  rather than guessing -- a low-confidence answer is fine and expected
  for genuinely ambiguous cases.
- Return ONLY valid JSON.
- Do not include markdown.
- confidence must be between 0 and 1.

JSON format:
{{
  "is_match": true,
  "confidence": 0.99,
  "reason": "short explanation"
}}
""".strip()

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a deterministic basketball "
                        "fixture entity-resolution service."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
            },
        }

        try:
            response = self.session.post(
                self.url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["message"]["content"]
            result = json.loads(content)

            is_match = bool(result["is_match"])
            confidence = float(result["confidence"])
            reason = str(result.get("reason", ""))
        except requests.RequestException as exc:
            raise LLMResolutionError(
                f"Network error contacting {self.url}: {exc}"
            ) from exc
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LLMResolutionError(
                f"Malformed response from model {self.model}: {exc}"
            ) from exc

        if not 0 <= confidence <= 1:
            raise LLMResolutionError(
                f"Invalid confidence returned by model: {confidence}"
            )

        return Resolution(
            is_match=is_match,
            confidence=confidence,
            reason=reason,
        )


# ============================================================
# Resolver service
# ============================================================

class MatchResolver:
    def __init__(
        self,
        cache: ResolutionCache,
        llm: QwenMatchResolver,
    ):
        self.cache = cache
        self.llm = llm

    def _cache_key(
        self,
        a: Match,
        b: Match,
    ) -> str:
        # Cache key now embeds each fixture's date, not just the team
        # names. Without this, two different-dated fixtures between
        # the same two teams would collide in the cache and silently
        # reuse each other's resolution.
        pair_a = canonical_key(a.home_team, a.away_team)
        pair_b = canonical_key(b.home_team, b.away_team)

        fixture_a = f"{pair_a}@{a.match_date.isoformat()}"
        fixture_b = f"{pair_b}@{b.match_date.isoformat()}"

        # For the pair-of-fixtures cache key, ordering does not matter.
        return "MATCH_PAIR::" + "###".join(sorted((fixture_a, fixture_b)))

    def resolve(
        self,
        a: Match,
        b: Match,
    ) -> Resolution:

        key = self._cache_key(a, b)

        # ----------------------------------------------------
        # 1. Cache first
        # ----------------------------------------------------

        cached = self.cache.get(key)

        if cached is not None:
            return cached

        # ----------------------------------------------------
        # 2. Deterministic exact comparison: teams AND date.
        #
        # Team names alone are NOT sufficient here -- the same two
        # teams can play more than once (home/away legs, rematches).
        # Only an exact match on the full fixture key is treated as
        # certain without asking the LLM.
        # ----------------------------------------------------

        if canonical_fixture_key(a) == canonical_fixture_key(b):
            resolution = Resolution(
                is_match=True,
                confidence=1.0,
                reason=(
                    "Exact match after deterministic normalization "
                    "(same teams, same date)."
                ),
            )

            self.cache.put(key, a, b, resolution)

            return resolution

        # ----------------------------------------------------
        # 3. LLM, with failure isolation and confidence gating.
        # ----------------------------------------------------

        try:
            resolution = self.llm.resolve(a, b)
        except LLMResolutionError as exc:
            # Do NOT cache this -- it's a transient failure (network,
            # bad output, etc.), not a real answer, and should be
            # retried on a future run rather than permanently stuck.
            return Resolution(
                is_match=False,
                confidence=0.0,
                reason=f"LLM resolution failed, needs manual review: {exc}",
                needs_review=True,
            )

        if resolution.confidence < MIN_CONFIDENCE:
            # A real answer, but not confident enough to auto-apply.
            # We still cache it (it's deterministic given the model
            # and prompt) but flag it so it's never auto-merged.
            resolution = Resolution(
                is_match=resolution.is_match,
                confidence=resolution.confidence,
                reason=f"[low confidence, needs review] {resolution.reason}",
                needs_review=True,
            )

        self.cache.put(key, a, b, resolution)

        return resolution
# ============================================================
# Canonical match graph
# ============================================================
class MatchClusterer:
    def __init__(self, matches: list[Match]):
        self.matches = matches

        self.parent: dict[str, str] = {
            self.node_id(m): self.node_id(m)
            for m in matches
        }

    @staticmethod
    def node_id(match: Match) -> str:
        return f"{match.source}:{match.source_id}"

    def find(self, node: str) -> str:
        parent = self.parent[node]

        if parent != node:
            self.parent[node] = self.find(parent)

        return self.parent[node]

    def union(self, a: str, b: str) -> None:
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a != root_b:
            self.parent[root_b] = root_a

    def mapping(self) -> dict[str, str]:
        return {
            node: self.find(node)
            for node in self.parent
        }


# ============================================================
# Candidate generation
# ============================================================

def same_normalized_home_or_away(
    a: Match,
    b: Match,
) -> bool:
    
    ah = normalize_team_name(a.home_team)
    aa = normalize_team_name(a.away_team)

    bh = normalize_team_name(b.home_team)
    ba = normalize_team_name(b.away_team)

    return (
        ah == bh
        or aa == ba
        or ah == ba
        or aa == bh
    )


def generate_candidates(
    matches: list[Match],
) -> Iterable[tuple[Match, Match]]:
    """
    Yields candidate pairs, bounded by DATE_TOLERANCE_DAYS.

    Matches are sorted by date first so the date window can be swept
    with an early break, instead of comparing every fixture against
    every other fixture regardless of date. This is both a
    correctness fix (fixtures far apart in time are never compared,
    so they can never be merged) and a performance improvement.
    """
    by_date = sorted(matches, key=lambda m: m.match_date)
    n = len(by_date)

    for i, a in enumerate(by_date):
        for j in range(i + 1, n):
            b = by_date[j]

            if (b.match_date - a.match_date).days > DATE_TOLERANCE_DAYS:
                break  # sorted by date -- nothing further can be in range

            if a.source == b.source and a.source_id == b.source_id:
                continue

            if same_normalized_home_or_away(a, b):
                yield a, b


# ============================================================
# Main resolution pipeline
# ============================================================

@dataclass
class PipelineResult:
    mapping: dict[str, str]
    # Pairs the pipeline could not confidently resolve one way or the
    # other (low LLM confidence, or an LLM call that failed). These
    # are NOT merged and NOT treated as distinct -- they need a human
    # to look at them before you trust the mapping fully.
    needs_review: list[tuple[Match, Match, Resolution]]


def resolve_datasets(
    datasets: dict[str, dict[str, dict[str, Any]]],
) -> PipelineResult:

    matches = flatten_all(datasets)

    cache = ResolutionCache(CACHE_DB)
    llm = QwenMatchResolver()
    resolver = MatchResolver(cache, llm)

    clusterer = MatchClusterer(matches)
    needs_review: list[tuple[Match, Match, Resolution]] = []

    try:
        for a, b in generate_candidates(matches):

            resolution = resolver.resolve(a, b)

            if resolution.needs_review:
                needs_review.append((a, b, resolution))
                continue

            if resolution.is_match:
                clusterer.union(
                    clusterer.node_id(a),
                    clusterer.node_id(b),
                )

    finally:
        cache.close()

    return PipelineResult(
        mapping=clusterer.mapping(),
        needs_review=needs_review,
    )