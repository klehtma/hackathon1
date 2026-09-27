import time

import arbitrage
import config
import db
import normalize
from driver import Driver
from scrapers import epicbet, optibet


def run_once() -> int:
    """One full scrape + match + write pass. Returns the number of
    opportunities written."""

    written = 0

    with Driver() as page:
        with db.get_connection() as conn:
            for comp in config.COMPETITIONS:
                print(f"\n=== {comp.sport_key} ===")

                epic_events = epicbet.fetch_competition(page, comp.epicbet_url, comp.sport_key)
                opti_events = optibet.fetch_competition(page, comp.optibet_url, comp.sport_key)

                pairs = normalize.match_events(
                    epic_events, opti_events, config.MATCH_TIME_TOLERANCE_MINUTES
                )
                print(
                    f"[match] {len(pairs)} matched pairs out of "
                    f"{len(epic_events)} epicbet / {len(opti_events)} optibet events"
                )

                for epic_event, opti_event in pairs:
                    opp = arbitrage.compute_arbitrage(
                        epic_event, opti_event, config.MIN_PROFIT_PERCENT
                    )
                    if not opp:
                        continue

                    print(
                        f"[arb] {opp['homeTeam']} vs {opp['awayTeam']}: "
                        f"{opp['profitPercent']:.2f}% profit"
                    )
                    db.upsert_opportunity(conn, opp)
                    written += 1

    print(f"\nDone. Wrote {written} opportunities.")
    return written


def main():
    if config.RUN_ONCE:
        run_once()
        return

    while True:
        try:
            run_once()
        except Exception as e:
            # Keep the loop alive across a bad run (e.g. a site was briefly
            # unreachable) instead of crashing the whole container.
            print(f"[main] run failed: {e}")
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
