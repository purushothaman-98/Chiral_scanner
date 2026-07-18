from __future__ import annotations

import argparse
from datetime import datetime, timezone

from chiral_scanner.storage import atomic_write_json, empty_archive, load_json, merge_papers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--archive", default="data/papers.json")
    parser.add_argument("--history", default="data/scan_history.json")
    args = parser.parse_args()

    archive = load_json(args.archive, empty_archive())
    candidates = load_json(args.candidates, [])
    summary = load_json(args.summary, {})
    merged, added, updated = merge_papers(archive.get("papers", []), candidates)
    archive["papers"] = merged
    archive["updated_at"] = datetime.now(timezone.utc).isoformat()

    summary["newly_added"] = added
    summary["updated"] = updated
    summary["total_archive_size"] = len(merged)
    history = load_json(args.history, [])
    history.append(summary)
    history = history[-1000:]

    atomic_write_json(args.archive, archive)
    atomic_write_json(args.history, history)
    print(f"Merged {len(candidates)} candidates: +{added}, updated {updated}, total {len(merged)}")


if __name__ == "__main__":
    main()
