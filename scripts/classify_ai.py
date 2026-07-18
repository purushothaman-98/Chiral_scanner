from __future__ import annotations

import argparse
import logging
import os
import time

from chiral_scanner.ai_classifier import classify_paper
from chiral_scanner.config import DEFAULT_AI_MODEL, PROMPT_VERSION
from chiral_scanner.scope import has_chiral_phonon_scope
from chiral_scanner.storage import atomic_write_json, fingerprint, load_json

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default="data/papers.json")
    parser.add_argument("--output", default="/tmp/chiral_ai_results.json")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--sleep", type=float, default=2.0)
    parser.add_argument("--summary", default="/tmp/chiral_ai_summary.json")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_MODELS_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN or GITHUB_MODELS_TOKEN is required")
    model = os.getenv("GITHUB_MODELS_MODEL", DEFAULT_AI_MODEL)
    archive = load_json(args.archive, {"papers": []})
    eligible = [
        paper
        for paper in archive.get("papers", [])
        if paper.get("preliminary_include") is True
        or has_chiral_phonon_scope(paper.get("title", ""), paper.get("abstract", ""))
    ]
    pending = [
        paper
        for paper in eligible
        if paper.get("ai_fingerprint") != fingerprint(paper, PROMPT_VERSION)
    ]
    pending.sort(key=lambda paper: paper.get("latest_update_date", ""), reverse=True)
    pending.sort(key=lambda paper: not bool(paper.get("preliminary_include")))
    pending = pending[: args.limit]

    results: list[dict] = []
    failures: list[dict] = []
    for index, paper in enumerate(pending, start=1):
        logging.info("Classifying %s/%s %s", index, len(pending), paper["base_arxiv_id"])
        try:
            results.append(classify_paper(paper, token=token, model=model))
            atomic_write_json(args.output, results)
        except RuntimeError as exc:
            logging.error("Deferring %s after repeated errors: %s", paper["base_arxiv_id"], exc)
            failures.append({"base_arxiv_id": paper["base_arxiv_id"], "error": str(exc)})
        if index < len(pending):
            time.sleep(args.sleep)
    atomic_write_json(args.output, results)
    atomic_write_json(
        args.summary,
        {
            "selected": len(pending),
            "succeeded": len(results),
            "failed": len(failures),
            "failures": failures,
            "eligible_total": len(eligible),
        },
    )
    print(f"Prepared {len(results)}/{len(pending)} AI decisions; {len(failures)} deferred")


if __name__ == "__main__":
    main()
