"""Evidence-backed research geography derived from mapped papers."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "verified_institutions.json"


def load_affiliation_registry(path: Path | None = None) -> dict:
    """Load the cited affiliation registry; return an empty compatible schema on failure."""
    source = path or REGISTRY_PATH
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"institutions": {}, "authors": {}, "last_verified": None}
    if not isinstance(payload, dict):
        return {"institutions": {}, "authors": {}, "last_verified": None}
    payload.setdefault("institutions", {})
    payload.setdefault("authors", {})
    return payload


def _year(paper: dict) -> int | None:
    value = paper.get("initial_submission_date") or paper.get("submitted")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).year
    except ValueError:
        return None


def _paper_id(paper: dict) -> str:
    return str(
        paper.get("base_arxiv_id")
        or paper.get("arxiv_id")
        or paper.get("title")
        or id(paper)
    )


def _labels(paper: dict, *keys: str) -> list[str]:
    values: list[str] = []
    for key in keys:
        raw = paper.get(key, [])
        if isinstance(raw, str):
            raw = [raw]
        if isinstance(raw, list):
            values.extend(str(value).strip() for value in raw if str(value).strip())
    return values


def institution_activity(
    field_papers: list[dict], registry: dict | None = None
) -> tuple[list[dict], list[dict], dict[str, int | str | None]]:
    """Join cited affiliations to live papers without inferring unresolved identities."""
    registry = registry or load_affiliation_registry()
    authors = registry.get("authors", {})
    institutions = registry.get("institutions", {})
    archive_authors = {
        str(author).strip()
        for paper in field_papers
        for author in paper.get("authors", [])
        if str(author).strip()
    }
    mapped_authors = archive_authors.intersection(authors)

    institution_papers: dict[str, dict[str, dict]] = defaultdict(dict)
    institution_authors: dict[str, set[str]] = defaultdict(set)
    years: dict[str, set[int]] = defaultdict(set)
    materials: dict[str, Counter] = defaultdict(Counter)
    directions: dict[str, Counter] = defaultdict(Counter)
    links: dict[tuple[str, str], dict] = {}

    for paper in field_papers:
        paper_id = _paper_id(paper)
        paper_institutions: set[str] = set()
        for author in paper.get("authors", []):
            record = authors.get(str(author).strip(), {})
            ids = record.get("institution_ids")
            if ids is None:
                single = record.get("institution_id")
                ids = [single] if single else []
            for institution_id in ids:
                if institution_id in institutions:
                    paper_institutions.add(institution_id)
                    institution_authors[institution_id].add(str(author).strip())

        for institution_id in paper_institutions:
            institution_papers[institution_id][paper_id] = paper
            if (year := _year(paper)) is not None:
                years[institution_id].add(year)
            materials[institution_id].update(
                _labels(paper, "material_systems", "material_families", "materials")
            )
            directions[institution_id].update(
                _labels(paper, "ecosystem_areas", "research_directions", "categories")
            )

        for left, right in combinations(sorted(paper_institutions), 2):
            record = links.setdefault(
                (left, right), {"paper_ids": set(), "titles": [], "materials": Counter()}
            )
            record["paper_ids"].add(paper_id)
            title = str(paper.get("title", paper_id))
            if title not in record["titles"]:
                record["titles"].append(title)
            record["materials"].update(
                _labels(paper, "material_systems", "material_families", "materials")
            )

    rows: list[dict] = []
    for institution_id, paper_map in institution_papers.items():
        institution = institutions[institution_id]
        matched = sorted(institution_authors[institution_id])
        author_records = [authors[name] for name in matched]
        rows.append(
            {
                "id": institution_id,
                **institution,
                "institution": institution["name"],
                "mapped_authors": matched,
                "author_count": len(matched),
                "paper_count": len(paper_map),
                "paper_ids": sorted(paper_map),
                "years": sorted(years[institution_id]),
                "roles": sorted({r.get("role", "research") for r in author_records}),
                "contributions": [
                    r["contribution"] for r in author_records if r.get("contribution")
                ],
                "materials": [name for name, _ in materials[institution_id].most_common(4)],
                "directions": [name for name, _ in directions[institution_id].most_common(4)],
            }
        )
    rows.sort(key=lambda row: (-row["paper_count"], row["institution"]))

    link_rows = [
        {
            "institution_1": left,
            "institution_2": right,
            "joint_papers": len(record["paper_ids"]),
            "titles": record["titles"][:5],
            "materials": [name for name, _ in record["materials"].most_common(3)],
        }
        for (left, right), record in sorted(
            links.items(), key=lambda item: -len(item[1]["paper_ids"])
        )
    ]
    all_paper_ids = {_paper_id(paper) for paper in field_papers}
    covered_paper_ids = {
        paper_id for paper_map in institution_papers.values() for paper_id in paper_map
    }
    coverage: dict[str, int | str | None] = {
        "archive_authors": len(archive_authors),
        "verified_authors": len(mapped_authors),
        "verified_institutions": len(rows),
        "covered_papers": len(covered_paper_ids),
        "total_papers": len(all_paper_ids),
        "uncovered_papers": len(all_paper_ids - covered_paper_ids),
        "countries": len({row["country"] for row in rows}),
        "registry_updated": registry.get("last_verified"),
    }
    return rows, link_rows, coverage
