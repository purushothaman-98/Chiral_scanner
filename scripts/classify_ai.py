from __future__ import annotations

import argparse
import logging
import os
import time

from chiral_scanner.ai_classifier import classify_paper
from chiral_scanner.config import DEFAULT_AI_MODEL, PROMPT_VERSION
from chiral_scanner.storage import atomic_write_json, fingerprint, load_json

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default="data/papers.json")
    parser.add_argument("--output", default="/tmp/chiral_ai_results.json")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=2.0)
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_MODELS_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN or GITHUB_MODELS_TOKEN is required")
    model = os.getenv("GITHUB_MODELS_MODEL", DEFAULT_AI_MODEL)
    archive = load_json(args.archive, {"papers": []})
    pending = [
        paper
        for paper in archive.get("papers", [])
        if paper.get("ai_fingerprint") != fingerprint(paper, PROMPT_VERSION)
    ][: args.limit]

    results: list[dict] = []
    for index, paper in enumerate(pending, start=1):
        logging.info("Classifying %s/%s %s", index, len(pending), paper["base_arxiv_id"])
        results.append(classify_paper(paper, token=token, model=model))
        if index < len(pending):
            time.sleep(args.sleep)
    atomic_write_json(args.output, results)
    print(f"Prepared {len(results)} AI decisions")


if __name__ == "__main__":
    main()
