from __future__ import annotations

import argparse
from datetime import datetime, timezone

from chiral_scanner.config import PROMPT_VERSION
from chiral_scanner.scope import has_chiral_phonon_scope
from chiral_scanner.storage import atomic_write_json, fingerprint, load_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default="data/papers.json")
    parser.add_argument("--history", default="data/review_history.json")
    parser.add_argument("--summary", required=True)
    args = parser.parse_args()

    archive = load_json(args.archive, {"papers": []})
    history = load_json(args.history, [])
    eligible = [
        paper
        for paper in archive.get("papers", [])
        if paper.get("preliminary_include") is True
        or has_chiral_phonon_scope(paper.get("title", ""), paper.get("abstract", ""))
    ]
    pending = sum(
        paper.get("ai_fingerprint") != fingerprint(paper, PROMPT_VERSION)
        for paper in eligible
    )
    summary = load_json(args.summary, {})
    history.append(
        {
            "review_timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_version": PROMPT_VERSION,
            "selected": int(summary.get("selected", 0)),
            "succeeded": int(summary.get("succeeded", 0)),
            "failed": int(summary.get("failed", 0)),
            "eligible_total": len(eligible),
            "eligible_pending_after_run": pending,
        }
    )
    atomic_write_json(args.history, history[-500:])


if __name__ == "__main__":
    main()
