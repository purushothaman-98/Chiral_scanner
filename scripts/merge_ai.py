from __future__ import annotations

import argparse
from datetime import datetime, timezone

from chiral_scanner.storage import atomic_write_json, load_json, merge_ai_results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default="data/papers.json")
    parser.add_argument("--results", required=True)
    args = parser.parse_args()

    archive = load_json(args.archive, {"schema_version": 1, "topic": "chiral phonons", "papers": []})
    results = load_json(args.results, [])
    papers, applied = merge_ai_results(archive.get("papers", []), results)
    archive["papers"] = papers
    archive["updated_at"] = datetime.now(timezone.utc).isoformat()
    atomic_write_json(args.archive, archive)
    print(f"Applied {applied}/{len(results)} AI decisions")


if __name__ == "__main__":
    main()
