"""Evidence-backed research geography derived from mapped papers."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "verified_institutions.json"
PAPER_AFFILIATIONS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "paper_affiliations.json"
)


def load_affiliation_registry(path: Path | None = None) -> dict:
    """Load the cited manual registry; return an empty compatible schema on failure."""
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


def load_paper_affiliations(path: Path | None = None) -> dict:
    """Load automated paper-specific affiliations without failing the website."""
    source = path or PAPER_AFFILIATIONS_PATH
    empty = {
        "institutions": {},
        "papers": {},
        "unresolved": {},
        "generated_at": None,
    }
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty
    if not isinstance(payload, dict):
        return empty
    payload.setdefault("institutions", {})
    payload.setdefault("papers", {})
    payload.setdefault("unresolved", {})
    payload.setdefault("generated_at", None)
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


def _normalise(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value.casefold()))


def _is_mappable(institution: dict[str, Any]) -> bool:
    latitude = institution.get("latitude")
    longitude = institution.get("longitude")
    country = institution.get("country") or institution.get("country_code")
    return isinstance(latitude, (int, float)) and isinstance(longitude, (int, float)) and bool(
        country
    )


def _merge_institutions(
    manual: dict[str, dict], automatic: dict[str, dict]
) -> tuple[dict[str, dict], dict[str, str]]:
    """Merge sources and alias exact same-name/ROR institutions to manual IDs."""
    institutions = {
        str(key): dict(value) for key, value in automatic.items() if isinstance(value, dict)
    }
    aliases = {key: key for key in institutions}
    manual_by_name = {
        _normalise(str(record.get("name") or "")): institution_id
        for institution_id, record in manual.items()
        if isinstance(record, dict) and record.get("name")
    }
    manual_by_ror = {
        str(record.get("ror_id")): institution_id
        for institution_id, record in manual.items()
        if isinstance(record, dict) and record.get("ror_id")
    }
    for automatic_id, record in list(institutions.items()):
        target = None
        ror_id = str(record.get("ror_id") or "")
        if ror_id and ror_id in manual_by_ror:
            target = manual_by_ror[ror_id]
        elif record.get("name"):
            target = manual_by_name.get(_normalise(str(record["name"])))
        if target:
            aliases[automatic_id] = target
            institutions.pop(automatic_id, None)
            institutions[target] = {**record, **manual[target]}
    for institution_id, record in manual.items():
        if isinstance(record, dict):
            institutions[institution_id] = {**institutions.get(institution_id, {}), **record}
    return institutions, aliases


def institution_activity(
    field_papers: list[dict],
    registry: dict | None = None,
    paper_affiliations: dict | None = None,
) -> tuple[list[dict], list[dict], dict[str, int | str | None]]:
    """Join cited and verified paper-specific affiliations without inferring identities."""
    registry = registry or load_affiliation_registry()
    paper_affiliations = (
        paper_affiliations if paper_affiliations is not None else load_paper_affiliations()
    )
    manual_authors = registry.get("authors", {})
    institutions, aliases = _merge_institutions(
        registry.get("institutions", {}), paper_affiliations.get("institutions", {})
    )
    paper_records = paper_affiliations.get("papers", {})

    archive_authors = {
        str(author).strip()
        for paper in field_papers
        for author in paper.get("authors", [])
        if str(author).strip()
    }
    mapped_authors: set[str] = set()

    institution_papers: dict[str, dict[str, dict]] = defaultdict(dict)
    institution_authors: dict[str, set[str]] = defaultdict(set)
    institution_author_records: dict[str, dict[str, dict]] = defaultdict(dict)
    institution_affiliation_labels: dict[str, set[str]] = defaultdict(set)
    years: dict[str, set[int]] = defaultdict(set)
    materials: dict[str, Counter] = defaultdict(Counter)
    directions: dict[str, Counter] = defaultdict(Counter)
    links: dict[tuple[str, str], dict] = {}
    automatically_covered: set[str] = set()

    for paper in field_papers:
        paper_id = _paper_id(paper)
        paper_institutions: set[str] = set()
        automatically_mapped_authors: set[str] = set()
        automatic_record = paper_records.get(paper_id, {})
        if isinstance(automatic_record, dict):
            for author_record in automatic_record.get("authors", []) or []:
                if not isinstance(author_record, dict):
                    continue
                author_name = str(
                    author_record.get("paper_author_name")
                    or author_record.get("name")
                    or ""
                ).strip()
                if not author_name:
                    continue
                accepted = False
                for raw_id in author_record.get("institution_ids", []) or []:
                    institution_id = aliases.get(str(raw_id), str(raw_id))
                    institution = institutions.get(institution_id)
                    if not isinstance(institution, dict) or not _is_mappable(institution):
                        continue
                    accepted = True
                    paper_institutions.add(institution_id)
                    institution_authors[institution_id].add(author_name)
                    institution_author_records[institution_id].setdefault(
                        author_name,
                        {
                            "role": "research",
                            "contribution": None,
                            "source": "Verified paper-specific affiliation",
                        },
                    )
                    institution_affiliation_labels[institution_id].update(
                        str(label).strip()
                        for label in author_record.get("affiliation_labels", []) or []
                        if str(label).strip()
                    )
                if accepted:
                    automatically_mapped_authors.add(author_name)
                    mapped_authors.add(author_name)
                    automatically_covered.add(paper_id)

        for author in paper.get("authors", []):
            author_name = str(author).strip()
            # A paper-specific affiliation is stronger than a static author registry.
            # Use the manual registry only as a fallback for this paper so author
            # mobility cannot create a false institution or collaboration link.
            if author_name in automatically_mapped_authors:
                continue
            record = manual_authors.get(author_name, {})
            ids = record.get("institution_ids")
            if ids is None:
                single = record.get("institution_id")
                ids = [single] if single else []
            accepted = False
            for raw_id in ids:
                institution_id = aliases.get(str(raw_id), str(raw_id))
                institution = institutions.get(institution_id)
                if not isinstance(institution, dict) or not _is_mappable(institution):
                    continue
                accepted = True
                paper_institutions.add(institution_id)
                institution_authors[institution_id].add(author_name)
                institution_author_records[institution_id][author_name] = record
            if accepted:
                mapped_authors.add(author_name)

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
        author_records = [institution_author_records[institution_id][name] for name in matched]
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
                "affiliation_labels": sorted(institution_affiliation_labels[institution_id]),
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
    countries = {
        str(row.get("country") or row.get("country_code"))
        for row in rows
        if row.get("country") or row.get("country_code")
    }
    coverage: dict[str, int | str | None] = {
        "archive_authors": len(archive_authors),
        "verified_authors": len(archive_authors.intersection(mapped_authors)),
        "verified_institutions": len(rows),
        "covered_papers": len(covered_paper_ids),
        "automatically_covered_papers": len(automatically_covered),
        "total_papers": len(all_paper_ids),
        "uncovered_papers": len(all_paper_ids - covered_paper_ids),
        "countries": len(countries),
        "registry_updated": paper_affiliations.get("generated_at")
        or registry.get("last_verified"),
        "manual_registry_updated": registry.get("last_verified"),
        "automatic_registry_updated": paper_affiliations.get("generated_at"),
        "automatic_unresolved_papers": len(paper_affiliations.get("unresolved", {})),
    }
    return rows, link_rows, coverage
