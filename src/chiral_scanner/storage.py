from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import PROMPT_VERSION


def load_json(path: str | Path, default: Any) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        return default
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_json(path: str | Path, data: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=file_path.name, suffix=".tmp", dir=file_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
        os.replace(tmp_name, file_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def empty_archive() -> dict:
    return {
        "schema_version": 1,
        "topic": "chiral phonons",
        "updated_at": None,
        "papers": [],
    }


def fingerprint(paper: dict, prompt_version: str = PROMPT_VERSION) -> str:
    payload = {
        "arxiv_id": paper.get("base_arxiv_id"),
        "version": paper.get("current_version"),
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "categories": paper.get("categories", []),
        "prompt_version": prompt_version,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def merge_papers(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], int, int]:
    by_id = {paper["base_arxiv_id"]: dict(paper) for paper in existing}
    added = 0
    updated = 0

    for candidate in incoming:
        base_id = candidate["base_arxiv_id"]
        previous = by_id.get(base_id)
        if previous is None:
            candidate = dict(candidate)
            candidate["versions_seen"] = sorted(set(candidate.get("versions_seen", [])))
            candidate["first_seen_at"] = datetime.now(timezone.utc).isoformat()
            candidate["last_seen_at"] = candidate["first_seen_at"]
            candidate["ai_decision"] = None
            candidate["ai_fingerprint"] = None
            by_id[base_id] = candidate
            added += 1
            continue

        merged_versions = set(previous.get("versions_seen", []))
        merged_versions.update(candidate.get("versions_seen", []))
        previous_version = int(previous.get("current_version", 1))
        candidate_version = int(candidate.get("current_version", 1))
        changed = candidate_version > previous_version or candidate.get("abstract") != previous.get("abstract")

        if changed:
            preserved = {
                "first_seen_at": previous.get("first_seen_at"),
                "ai_decision": previous.get("ai_decision"),
                "ai_fingerprint": previous.get("ai_fingerprint"),
            }
            previous.update(candidate)
            previous.update({key: value for key, value in preserved.items() if value is not None})
            previous["ai_decision"] = None
            previous["ai_fingerprint"] = None
            updated += 1
        else:
            # Keep newer metadata-derived fields while preserving AI decisions.
            for key, value in candidate.items():
                if key not in {"ai_decision", "ai_fingerprint", "first_seen_at"}:
                    previous[key] = value
        previous["versions_seen"] = sorted(merged_versions)
        previous["last_seen_at"] = datetime.now(timezone.utc).isoformat()
        by_id[base_id] = previous

    merged = sorted(
        by_id.values(),
        key=lambda paper: paper.get("latest_update_date") or paper.get("initial_submission_date") or "",
        reverse=True,
    )
    return merged, added, updated


def merge_ai_results(papers: list[dict], results: list[dict]) -> tuple[list[dict], int]:
    result_by_id = {item["base_arxiv_id"]: item for item in results}
    applied = 0
    for paper in papers:
        result = result_by_id.get(paper["base_arxiv_id"])
        if not result:
            continue
        if result.get("fingerprint") != fingerprint(paper, result.get("prompt_version", PROMPT_VERSION)):
            continue
        paper["ai_decision"] = result["decision"]
        paper["ai_fingerprint"] = result["fingerprint"]
        paper["ai_prompt_version"] = result.get("prompt_version", PROMPT_VERSION)
        paper["ai_model"] = result.get("model")
        paper["ai_classified_at"] = result.get("classified_at")
        applied += 1
    return papers, applied
