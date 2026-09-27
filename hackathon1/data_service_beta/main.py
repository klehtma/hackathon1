import time

import arbitrage
import config
import db
import normalize
from driver import Driver


def run_once() -> int:
    written = 0

    with Driver() as page:
        with db.get_connection() as conn:
            for comp in config.COMPETITIONS:
                print(f"\n=== {comp.sport_key} ===")

                events_by_book = {}
                for book, url in comp.urls.items():
                    scraper = config.SCRAPERS.get(book)
                    if not scraper:
                        print(f"[main] no scraper registered for {book!r}, skipping")
                        continue
                    events_by_book[book] = scraper(page, url, comp.sport_key)

                if len(events_by_book) < 2:
                    print(f"[main] {comp.sport_key}: fewer than 2 books configured, "
                          f"nothing to compare — skipping")
                    continue

                groups = normalize.match_events(
                    events_by_book, config.MATCH_TIME_TOLERANCE_MINUTES
                )
                counts = ", ".join(f"{b}={len(e)}" for b, e in events_by_book.items())
                print(f"[match] {len(groups)} matched groups out of ({counts})")

                for group in groups:
                    opp = arbitrage.compute_arbitrage(group, config.MIN_PROFIT_PERCENT)
                    if not opp:
                        continue

                    print(
                        f"[arb] {opp['homeTeam']} vs {opp['awayTeam']} "
                        f"({'+'.join(sorted(group.keys()))}): "
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
            print(f"[main] run failed: {e}")
        time.sleep(config.POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
