from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta

from chiral_scanner.arxiv_client import ArxivWindow, fetch_window
from chiral_scanner.config import DEFAULT_INITIAL_DATE, DEFAULT_SCAN_OVERLAP_DAYS
from chiral_scanner.preliminary import classify_preliminary
from chiral_scanner.storage import atomic_write_json

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def parse_date(value: str, *, end_of_day: bool = False) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    if len(value) == 10 and end_of_day:
        parsed = parsed.replace(hour=23, minute=59, second=59)
    return parsed.astimezone(timezone.utc)


def windows(since: datetime, until: datetime, initial: bool) -> list[ArxivWindow]:
    if not initial:
        return [ArxivWindow(since, until)]
    result: list[ArxivWindow] = []
    cursor = since
    while cursor < until:
        next_cursor = min(cursor + relativedelta(years=1), until)
        result.append(ArxivWindow(cursor, next_cursor))
        cursor = next_cursor
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", help="ISO date/datetime. Defaults to a 14-day overlap.")
    parser.add_argument("--until", help="ISO date/datetime. Defaults to now.")
    parser.add_argument("--initial", action="store_true", help="Build archive in safe yearly date batches.")
    parser.add_argument("--output", default="/tmp/chiral_candidates.json")
    parser.add_argument("--summary", default="/tmp/chiral_scan_summary.json")
    args = parser.parse_args()

    until = parse_date(args.until, end_of_day=True) if args.until else datetime.now(timezone.utc)
    if args.since:
        since = parse_date(args.since)
    elif args.initial:
        since = parse_date(DEFAULT_INITIAL_DATE)
    else:
        since = until - timedelta(days=DEFAULT_SCAN_OVERLAP_DAYS)

    all_candidates: dict[str, dict] = {}
    total_queries = 0
    for window in windows(since, until, args.initial):
        papers, query_count = fetch_window(window)
        total_queries += query_count
        for paper in papers:
            classified = classify_preliminary(paper)
            current = all_candidates.get(classified["base_arxiv_id"])
            if current is None or classified["current_version"] > current["current_version"]:
                all_candidates[classified["base_arxiv_id"]] = classified

    candidates = sorted(
        all_candidates.values(), key=lambda item: item["latest_update_date"], reverse=True
    )
    summary = {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "earliest_queried_date": since.isoformat(),
        "latest_queried_date": until.isoformat(),
        "fetched": len(candidates),
        "preliminary_passing": sum(bool(p["preliminary_include"]) for p in candidates),
        "newly_added": 0,
        "updated": 0,
        "total_archive_size": 0,
        "query_count": total_queries,
    }
    atomic_write_json(args.output, candidates)
    atomic_write_json(args.summary, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
