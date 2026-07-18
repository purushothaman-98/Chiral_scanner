from __future__ import annotations

from chiral_scanner.models import AIDecision, ScanSummary
from chiral_scanner.storage import load_json


def main() -> None:
    archive = load_json("data/papers.json", {"papers": []})
    ids: set[str] = set()
    for paper in archive.get("papers", []):
        base_id = paper["base_arxiv_id"]
        if base_id in ids:
            raise ValueError(f"Duplicate paper: {base_id}")
        ids.add(base_id)
        if paper.get("ai_decision"):
            AIDecision.model_validate(paper["ai_decision"])
    for scan in load_json("data/scan_history.json", []):
        ScanSummary.model_validate(scan)
    print(f"Validated {len(ids)} papers")


if __name__ == "__main__":
    main()
