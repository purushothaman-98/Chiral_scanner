"""Non-AI, paper-specific affiliation enrichment from arXiv and OpenAlex."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pycountry
import requests

ARXIV_API = "https://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_URL_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([^?#]+?)(?:v\d+)?(?:\.pdf)?$", re.I)
USER_AGENT = "ChiralScanner/0.1 affiliation-enrichment"
AUTHOR_SCOPE = "first_and_corresponding"


def now() -> str:
    return datetime.now(UTC).isoformat()


def paper_id(paper: dict[str, Any]) -> str:
    value = paper.get("base_arxiv_id") or paper.get("arxiv_id") or ""
    return re.sub(r"v\d+$", "", str(value).strip(), flags=re.I)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def author_sig(value: str) -> str:
    parts = norm(value).split()
    return f"{parts[0]}:{parts[-1]}" if parts else ""


def year_of(paper: dict[str, Any]) -> int | None:
    value = paper.get("initial_submission_date") or paper.get("submitted")
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).year if value else None
    except ValueError:
        return None


def country_name(code: str | None) -> str:
    code = str(code or "").upper()
    country = pycountry.countries.get(alpha_2=code) if code else None
    return country.name if country else code or "Unresolved"


def read_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    return value if isinstance(value, dict) else fallback


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class MetadataClient:
    def __init__(self, mailto: str | None = None, session: requests.Session | None = None):
        self.mailto = (mailto or "").strip()
        self.session = session or requests.Session()
        self.institution_cache: dict[str, dict[str, Any]] = {}

    def get(self, url: str, *, params: dict[str, Any] | None = None, json_data: bool = True):
        query = dict(params or {})
        if url.startswith(OPENALEX_API) and self.mailto:
            query.setdefault("mailto", self.mailto)
        last_error: Exception | None = None
        for attempt in range(5):
            try:
                response = self.session.get(
                    url,
                    params=query,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                if response.status_code == 404:
                    return None
                if response.status_code == 429 or response.status_code >= 500:
                    time.sleep(min(2**attempt, 20))
                    continue
                response.raise_for_status()
                return response.json() if json_data else response.text
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                time.sleep(min(2**attempt, 20))
        raise RuntimeError(f"request_failed:{url}:{last_error}")

    def arxiv(self, arxiv_id: str) -> dict[str, Any]:
        xml = self.get(
            ARXIV_API,
            params={"id_list": arxiv_id, "max_results": 1},
            json_data=False,
        )
        return parse_arxiv_atom(str(xml or ""), arxiv_id)

    def work_by_doi(self, doi: str) -> dict[str, Any] | None:
        value = self.get(f"{OPENALEX_API}/works/https://doi.org/{quote(doi, safe='/')}")
        return value if isinstance(value, dict) else None

    def works(self, title: str) -> list[dict[str, Any]]:
        value = self.get(f"{OPENALEX_API}/works", params={"search": title, "per-page": 5})
        return value.get("results", []) if isinstance(value, dict) else []

    def institution(self, institution_id: str) -> dict[str, Any] | None:
        if institution_id in self.institution_cache:
            return self.institution_cache[institution_id]
        value = self.get(f"{OPENALEX_API}/institutions/{institution_id.rsplit('/', 1)[-1]}")
        if isinstance(value, dict):
            self.institution_cache[institution_id] = value
            return value
        return None

    def institutions(self, label: str) -> list[dict[str, Any]]:
        value = self.get(
            f"{OPENALEX_API}/institutions", params={"search": label, "per-page": 3}
        )
        return value.get("results", []) if isinstance(value, dict) else []


def parse_arxiv_atom(xml: str, expected_id: str) -> dict[str, Any]:
    try:
        entry = ET.fromstring(xml).find("atom:entry", NS)
    except ET.ParseError as exc:
        raise ValueError(f"invalid_arxiv_atom:{exc}") from exc
    if entry is None:
        return {"arxiv_id": expected_id, "authors": [], "doi": None}
    authors = []
    for index, item in enumerate(entry.findall("atom:author", NS)):
        name = (item.findtext("atom:name", "", NS) or "").strip()
        labels = [
            (node.text or "").strip()
            for node in item.findall("arxiv:affiliation", NS)
            if (node.text or "").strip()
        ]
        if name:
            authors.append(
                {
                    "name": name,
                    "affiliation_labels": labels,
                    "author_position": "first" if index == 0 else "middle",
                    "is_corresponding": False,
                }
            )
    doi = (entry.findtext("arxiv:doi", "", NS) or "").strip().casefold()
    doi = re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", doi) or None
    return {
        "arxiv_id": expected_id,
        "title": " ".join((entry.findtext("atom:title", "", NS) or "").split()),
        "doi": doi,
        "authors": authors,
    }


def work_arxiv_ids(work: dict[str, Any]) -> set[str]:
    urls = []
    if isinstance(work.get("ids"), dict):
        urls.extend(str(value) for value in work["ids"].values())
    for location in work.get("locations", []) or []:
        if isinstance(location, dict):
            urls.extend(str(location.get(key) or "") for key in ("landing_page_url", "pdf_url"))
    found = set()
    for url in urls:
        match = ARXIV_URL_RE.search(url)
        if match:
            found.add(re.sub(r"v\d+$", "", match.group(1), flags=re.I))
    return found


def work_authors(work: dict[str, Any]) -> list[str]:
    names = []
    for item in work.get("authorships", []) or []:
        author = item.get("author", {}) if isinstance(item, dict) else {}
        name = item.get("raw_author_name") or author.get("display_name")
        if name:
            names.append(str(name))
    return names


def authorship_roles(item: dict[str, Any], index: int) -> list[str]:
    """Return only roles that are safe for the public institution map."""
    roles: list[str] = []
    position = str(item.get("author_position") or "").strip().casefold()
    if index == 0 or position == "first":
        roles.append("first")
    if item.get("is_corresponding") is True:
        roles.append("corresponding")
    return roles


def target_authorships(items: list[dict[str, Any]] | Any) -> list[tuple[dict[str, Any], list[str]]]:
    """Select the first author and explicitly identified corresponding authors only."""
    selected: list[tuple[dict[str, Any], list[str]]] = []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        roles = authorship_roles(item, index)
        if roles:
            selected.append((item, roles))
    return selected


def select_openalex_work(
    paper: dict[str, Any],
    arxiv: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    doi_match: bool = False,
) -> tuple[dict[str, Any] | None, str | None, float]:
    expected = {author_sig(str(name)) for name in paper.get("authors", []) if author_sig(str(name))}
    ranked = []
    for work in candidates:
        title_score = SequenceMatcher(
            None,
            norm(str(paper.get("title") or arxiv.get("title") or "")),
            norm(str(work.get("display_name") or work.get("title") or "")),
        ).ratio()
        observed = {author_sig(name) for name in work_authors(work) if author_sig(name)}
        author_score = (
            len(expected & observed) / min(len(expected), len(observed))
            if expected and observed
            else 0
        )
        expected_year, observed_year = year_of(paper), work.get("publication_year")
        year_score = 1 if expected_year and expected_year == observed_year else 0.5
        if expected_year and isinstance(observed_year, int) and abs(expected_year - observed_year) > 1:
            year_score = 0
        exact_arxiv = paper_id(paper) in work_arxiv_ids(work)
        score = 0.64 * title_score + 0.26 * author_score + 0.10 * year_score
        ranked.append(
            (
                max(score, 0.99 if exact_arxiv else 0.98 if doi_match else 0),
                title_score,
                author_score,
                exact_arxiv,
                work,
            )
        )
    if not ranked:
        return None, None, 0
    score, title_score, author_score, exact_arxiv, work = max(ranked, key=lambda row: row[0])
    if doi_match and title_score >= 0.6:
        return work, "doi", round(score, 4)
    if exact_arxiv and title_score >= 0.6:
        return work, "arxiv_url", round(score, 4)
    if title_score >= 0.93 and author_score >= 0.5 and score >= 0.82:
        return work, "title_author_year", round(score, 4)
    return None, None, round(score, 4)


def institution_record(value: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    institution_id = str(value.get("id") or "")
    name = str(value.get("display_name") or "")
    if not institution_id or not name:
        return None
    geo = value.get("geo", {}) if isinstance(value.get("geo"), dict) else {}
    code = str(value.get("country_code") or geo.get("country_code") or "").upper()
    key = f"openalex:{institution_id.rsplit('/', 1)[-1]}"
    return key, {
        "name": name,
        "short_name": name,
        "city": geo.get("city") or "Unresolved",
        "region": geo.get("region"),
        "country_code": code or None,
        "country": geo.get("country") or country_name(code),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "institution_type": value.get("type") or "Research institution",
        "openalex_id": institution_id,
        "ror_id": value.get("ror"),
        "evidence_url": institution_id,
        "source": "OpenAlex",
    }


def resolve_label(label: str, client: MetadataClient) -> dict[str, Any] | None:
    label_norm = norm(label)
    ranked = []
    for candidate in client.institutions(label):
        name_norm = norm(str(candidate.get("display_name") or ""))
        if not name_norm:
            continue
        name_tokens = set(name_norm.split())
        token_score = len(name_tokens & set(label_norm.split())) / len(name_tokens)
        score = (
            1
            if name_norm in label_norm
            else 0.65 * token_score + 0.35 * SequenceMatcher(None, name_norm, label_norm).ratio()
        )
        ranked.append((score, candidate))
    if not ranked:
        return None
    score, candidate = max(ranked, key=lambda row: row[0])
    if score < 0.78:
        return None
    return client.institution(str(candidate.get("id") or "")) or candidate


def enrich_paper(
    paper: dict[str, Any], client: MetadataClient, *, arxiv_delay: float = 3.1
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], str | None]:
    arxiv_id = paper_id(paper)
    if not arxiv_id:
        return None, {}, "missing_arxiv_id"
    try:
        metadata = client.arxiv(arxiv_id)
    except (RuntimeError, ValueError) as exc:
        return None, {}, f"service_error:{exc}"
    time.sleep(max(arxiv_delay, 0))
    work = None
    method = None
    score = 0.0
    doi = metadata.get("doi")
    if doi:
        try:
            direct = client.work_by_doi(str(doi))
        except RuntimeError:
            direct = None
        if direct:
            work, method, score = select_openalex_work(paper, metadata, [direct], doi_match=True)
    if work is None:
        try:
            candidates = client.works(str(paper.get("title") or metadata.get("title") or ""))
            work, method, score = select_openalex_work(paper, metadata, candidates)
        except RuntimeError as exc:
            return None, {}, f"service_error:{exc}"

    arxiv_labels = {
        author_sig(str(item.get("name") or "")): item.get("affiliation_labels", [])
        for item in metadata.get("authors", [])
        if isinstance(item, dict)
    }
    paper_authors = [str(name) for name in paper.get("authors", [])]
    institutions: dict[str, dict[str, Any]] = {}
    authors = []
    source_authors = work.get("authorships", []) if work else metadata.get("authors", [])
    for item, roles in target_authorships(source_authors):
        author = item.get("author", {}) if isinstance(item.get("author"), dict) else {}
        name = str(
            item.get("raw_author_name")
            or author.get("display_name")
            or item.get("name")
            or ""
        ).strip()
        if not name:
            continue
        paper_name = next(
            (value for value in paper_authors if author_sig(value) == author_sig(name)), name
        )
        labels = list(
            dict.fromkeys(
                list(item.get("raw_affiliation_strings") or [])
                + list(arxiv_labels.get(author_sig(name), []))
            )
        )
        institution_ids = []
        for dehydrated in item.get("institutions", []) if work else []:
            full = client.institution(str(dehydrated.get("id") or "")) or dehydrated
            pair = institution_record(full)
            if pair:
                key, record = pair
                institutions[key] = record
                institution_ids.append(key)
        if not institution_ids:
            for label in labels:
                pair = institution_record(resolve_label(str(label), client) or {})
                if pair:
                    key, record = pair
                    institutions[key] = record
                    institution_ids.append(key)
        authors.append(
            {
                "paper_author_name": paper_name,
                "name": name,
                "openalex_author_id": author.get("id"),
                "orcid": author.get("orcid"),
                "author_position": item.get("author_position") or ("first" if "first" in roles else None),
                "is_corresponding": "corresponding" in roles,
                "author_roles": roles,
                "institution_ids": sorted(set(institution_ids)),
                "affiliation_labels": [str(label) for label in labels if str(label).strip()],
            }
        )
    if not any(author["institution_ids"] for author in authors):
        return None, institutions, "no_conservative_match_or_resolved_affiliation"
    return (
        {
            "paper_id": arxiv_id,
            "paper_version": paper.get("current_version"),
            "title": paper.get("title"),
            "doi": doi,
            "openalex_work_id": work.get("id") if work else None,
            "match_method": method or "arxiv_affiliation",
            "match_score": score if work else 1.0,
            "author_scope": AUTHOR_SCOPE,
            "authors": authors,
            "enriched_at": now(),
            "sources": ["arXiv", "OpenAlex"],
        },
        institutions,
        None,
    )


def eligible_papers(archive: dict[str, Any]) -> list[dict[str, Any]]:
    papers = [
        paper
        for paper in archive.get("papers", [])
        if isinstance(paper, dict)
        and isinstance(paper.get("ai_decision"), dict)
        and paper["ai_decision"].get("include_in_feed") is True
    ]
    return sorted(
        papers,
        key=lambda paper: str(paper.get("initial_submission_date") or ""),
        reverse=True,
    )


def run_enrichment(
    input_path: Path,
    output_path: Path,
    state_path: Path,
    limit: int,
    retry_days: int,
    arxiv_delay: float,
    client: MetadataClient,
) -> dict[str, int]:
    archive = read_json(input_path, {"papers": []})
    output = read_json(output_path, {"institutions": {}, "papers": {}, "unresolved": {}})
    state = read_json(state_path, {"attempts": {}})
    for key in ("institutions", "papers", "unresolved"):
        output.setdefault(key, {})
    state.setdefault("attempts", {})
    selected = []
    for paper in eligible_papers(archive):
        pid = paper_id(paper)
        existing = output["papers"].get(pid, {})
        if (
            existing.get("paper_version") == paper.get("current_version")
            and existing.get("author_scope") == AUTHOR_SCOPE
        ):
            continue
        needs_scope_migration = bool(existing) and existing.get("author_scope") != AUTHOR_SCOPE
        attempt = state["attempts"].get(pid, {})
        if (
            not needs_scope_migration
            and attempt.get("status") != "error"
            and attempt.get("last_attempted_at")
        ):
            previous = datetime.fromisoformat(
                attempt["last_attempted_at"].replace("Z", "+00:00")
            )
            if datetime.now(UTC) - previous < timedelta(days=max(retry_days, 0)):
                continue
        selected.append(paper)
        if len(selected) >= max(limit, 0):
            break
    counts = {"selected": len(selected), "succeeded": 0, "unresolved": 0, "errors": 0}
    for paper in selected:
        pid, attempted = paper_id(paper), now()
        record, institutions, reason = enrich_paper(paper, client, arxiv_delay=arxiv_delay)
        output["institutions"].update(institutions)
        attempt = state["attempts"].setdefault(pid, {"attempt_count": 0})
        attempt.update(
            {
                "attempt_count": attempt["attempt_count"] + 1,
                "last_attempted_at": attempted,
            }
        )
        if record:
            output["papers"][pid] = record
            output["unresolved"].pop(pid, None)
            attempt.update({"status": "resolved", "reason": None})
            counts["succeeded"] += 1
        elif str(reason).startswith("service_error:"):
            attempt.update({"status": "error", "reason": reason})
            counts["errors"] += 1
        else:
            output["papers"].pop(pid, None)
            output["unresolved"][pid] = {
                "paper_id": pid,
                "title": paper.get("title"),
                "reason": reason,
                "last_attempted_at": attempted,
            }
            attempt.update({"status": "unresolved", "reason": reason})
            counts["unresolved"] += 1
    generated = now()
    output.update(
        {
            "schema_version": 2,
            "description": (
                "Paper-specific first-author and explicitly identified corresponding-author "
                "affiliations from arXiv/OpenAlex; uncertain identities remain unresolved."
            ),
            "author_scope": AUTHOR_SCOPE,
            "generated_at": generated,
            "eligible_field_papers": len(eligible_papers(archive)),
            "resolved_papers": len(output["papers"]),
            "unresolved_papers": len(output["unresolved"]),
        }
    )
    state.update({"schema_version": 2, "last_run_at": generated, **counts})
    write_json(output_path, output)
    write_json(state_path, state)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/papers.json"))
    parser.add_argument("--output", type=Path, default=Path("data/paper_affiliations.json"))
    parser.add_argument(
        "--state", type=Path, default=Path("data/affiliation_enrichment_state.json")
    )
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--retry-days", type=int, default=14)
    parser.add_argument("--arxiv-delay", type=float, default=3.1)
    args = parser.parse_args()
    counts = run_enrichment(
        args.input,
        args.output,
        args.state,
        args.limit,
        args.retry_days,
        args.arxiv_delay,
        MetadataClient(os.environ.get("OPENALEX_MAILTO")),
    )
    print(json.dumps(counts, indent=2))
    if counts["selected"] and counts["errors"] == counts["selected"]:
        raise SystemExit("All metadata requests failed; refusing to commit outage data")


if __name__ == "__main__":
    main()
