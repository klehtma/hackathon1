"""
Writes ArbOpportunity / ArbLeg rows using plain SQL via psycopg — no ORM.

These are the exact tables Prisma created for the backend (see
backend/prisma/schema.prisma and its migration), so column names are
camelCase and double-quoted to match Postgres's case-sensitive identifiers.
Prisma normally generates the "id" values client-side (cuid()); since we're
writing directly, we generate our own opaque unique string instead — it
doesn't need to look like a cuid, it just needs to be unique.
"""

import uuid

import psycopg

import config


def _new_id() -> str:
    return uuid.uuid4().hex


def get_connection():
    return psycopg.connect(config.DATABASE_URL)


def upsert_opportunity(conn, opp: dict) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO "ArbOpportunity"
                    ("id", "matchId", "homeTeam", "awayTeam", "commenceTime",
                     "totalImpliedProbability", "profitPercent", "detectedAt", "sportKey")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("matchId") DO UPDATE SET
                    "homeTeam" = EXCLUDED."homeTeam",
                    "awayTeam" = EXCLUDED."awayTeam",
                    "commenceTime" = EXCLUDED."commenceTime",
                    "totalImpliedProbability" = EXCLUDED."totalImpliedProbability",
                    "profitPercent" = EXCLUDED."profitPercent",
                    "detectedAt" = EXCLUDED."detectedAt",
                    "sportKey" = EXCLUDED."sportKey"
                RETURNING "id"
                """,
                (
                    _new_id(),
                    opp["matchId"],
                    opp["homeTeam"],
                    opp["awayTeam"],
                    opp["commenceTime"],
                    opp["totalImpliedProbability"],
                    opp["profitPercent"],
                    opp["detectedAt"],
                    opp.get("sportKey"),
                ),
            )
            (opportunity_id,) = cur.fetchone()

            # Replace legs wholesale each time, same as the Prisma seed script
            # does with `deleteMany: {}` — simpler than diffing old vs new.
            cur.execute('DELETE FROM "ArbLeg" WHERE "opportunityId" = %s', (opportunity_id,))

            cur.executemany(
                """
                INSERT INTO "ArbLeg"
                    ("id", "outcomeName", "bookmaker", "price", "stakePercent", "opportunityId")
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        _new_id(),
                        leg["outcomeName"],
                        leg["bookmaker"],
                        leg["price"],
                        leg["stakePercent"],
                        opportunity_id,
                    )
                    for leg in opp["legs"]
                ],
            )
