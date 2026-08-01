"""Resilient non-AI affiliation enrichment using arXiv, OpenAlex, Crossref, and ROR."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from chiral_scanner import affiliation_enrichment as base

CROSSREF_API = "https://api.crossref.org"
ROR_API = "https://api.ror.org/v2"
USER_AGENT = "ChiralScanner/0.2 affiliation-enrichment"


def _clean_doi(value: str | None) -> str | None:
    doi = str(value or "").strip().casefold()
    doi = re.sub(r"^(?:doi:|https?://(?:dx\.)?doi\.org/)", "", doi)
    return doi or None


def _date_year(record: dict[str, Any]) -> int | None:
    for field in ("published-print", "published-online", "issued", "created"):
        value = record.get(field)
        if not isinstance(value, dict):
            continue
        parts = value.get("date-parts")
        if isinstance(parts, list) and parts and isinstance(parts[0], list) and parts[0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                pass
    return None


def _crossref_work(record: dict[str, Any]) -> dict[str, Any] | None:
    doi = _clean_doi(record.get("DOI"))
    titles = record.get("title") or []
    title = str(titles[0]).strip() if isinstance(titles, list) and titles else ""
    if not doi or not title:
        return None

    authorships = []
    for contributor in record.get("author", []) or []:
        if not isinstance(contributor, dict):
            continue
        name = " ".join(
            part.strip()
            for part in (
                str(contributor.get("given") or ""),
                str(contributor.get("family") or ""),
            )
            if part.strip()
        )
        name = name or str(contributor.get("name") or "").strip()
        if not name:
            continue
        labels = [
            str(item.get("name") or "").strip()
            for item in contributor.get("affiliation", []) or []
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        ]
        authorships.append(
            {
                "raw_author_name": name,
                "raw_affiliation_strings": labels,
                "author": {
                    "display_name": name,
                    "id": None,
                    "orcid": contributor.get("ORCID"),
                },
                "institutions": [],
            }
        )

    return {
        "id": f"https://doi.org/{doi}",
        "doi": f"https://doi.org/{doi}",
        "display_name": title,
        "title": title,
        "publication_year": _date_year(record),
        "authorships": authorships,
        "locations": [],
        "_metadata_provider": "Crossref",
    }


def _ror_display_name(organization: dict[str, Any]) -> str:
    names = organization.get("names", []) or []
    for preferred_type in ("ror_display", "label"):
        for item in names:
            if (
                isinstance(item, dict)
                and preferred_type in (item.get("types") or [])
                and str(item.get("value") or "").strip()
            ):
                return str(item["value"]).strip()
    for item in names:
        if isinstance(item, dict) and str(item.get("value") or "").strip():
            return str(item["value"]).strip()
    return ""


def _ror_institution(organization: dict[str, Any]) -> dict[str, Any] | None:
    ror_id = str(organization.get("id") or "").strip()
    name = _ror_display_name(organization)
    if not ror_id or not name:
        return None

    locations = organization.get("locations", []) or []
    location = locations[0] if locations and isinstance(locations[0], dict) else {}
    geo = (
        location.get("geonames_details", {})
        if isinstance(location.get("geonames_details"), dict)
        else {}
    )
    code = str(geo.get("country_code") or "").upper()
    types = organization.get("types", []) or []

    return {
        "id": ror_id,
        "display_name": name,
        "country_code": code or None,
        "type": str(types[0]) if types else "Research institution",
        "ror": ror_id,
        "geo": {
            "city": geo.get("name") or "Unresolved",
            "region": geo.get("country_subdivision_name"),
            "country": geo.get("country_name") or base.country_name(code),
            "country_code": code or None,
            "latitude": geo.get("lat"),
            "longitude": geo.get("lng"),
        },
        "_metadata_provider": "ROR",
    }


def institution_record(value: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    identifier = str(value.get("id") or "")
    name = str(value.get("display_name") or "")
    if not identifier or not name:
        return None

    geo = value.get("geo", {}) if isinstance(value.get("geo"), dict) else {}
    code = str(value.get("country_code") or geo.get("country_code") or "").upper()
    provider = str(value.get("_metadata_provider") or "OpenAlex")
    if "ror.org/" in identifier:
        short_id = identifier.rstrip("/").rsplit("/", 1)[-1]
        key = f"ror:{short_id}"
        openalex_id = None
        ror_id = identifier
    else:
        short_id = identifier.rstrip("/").rsplit("/", 1)[-1]
        key = f"openalex:{short_id}"
        openalex_id = identifier
        ror_id = value.get("ror")

    return key, {
        "name": name,
        "short_name": name,
        "city": geo.get("city") or "Unresolved",
        "region": geo.get("region"),
        "country_code": code or None,
        "country": geo.get("country") or base.country_name(code),
        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),
        "institution_type": value.get("type") or "Research institution",
        "openalex_id": openalex_id,
        "ror_id": ror_id,
        "evidence_url": identifier,
        "source": provider,
    }


class ResilientMetadataClient(base.MetadataClient):
    """Metadata client with key-aware OpenAlex and key-free Crossref/ROR fallbacks."""

    def __init__(
        self,
        *,
        mailto: str | None = None,
        openalex_api_key: str | None = None,
        ror_client_id: str | None = None,
        session: requests.Session | None = None,
    ):
        super().__init__(mailto=mailto, session=session)
        self.openalex_api_key = str(openalex_api_key or "").strip()
        self.ror_client_id = str(ror_client_id or "").strip()
        self.ror_cache: dict[str, dict[str, Any] | None] = {}

    @property
    def openalex_enabled(self) -> bool:
        return bool(self.openalex_api_key)

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: bool = True,
    ):
        query = dict(params or {})
        if url.startswith(base.OPENALEX_API):
            if not self.openalex_enabled:
                raise RuntimeError("openalex_api_key_missing")
            query.setdefault("api_key", self.openalex_api_key)
            if self.mailto:
                query.setdefault("mailto", self.mailto)
        elif url.startswith(CROSSREF_API) and self.mailto:
            query.setdefault("mailto", self.mailto)

        headers = {"User-Agent": USER_AGENT}
        if url.startswith(ROR_API) and self.ror_client_id:
            headers["Client-Id"] = self.ror_client_id

        last_error: Exception | None = None
        for attempt in range(5):
            try:
                response = self.session.get(
                    url,
                    params=query,
                    headers=headers,
                    timeout=30,
                )
                if response.status_code == 404:
                    return None
                if response.status_code == 429 or response.status_code >= 500:
                    time.sleep(min(2**attempt, 20))
                    continue
                if 400 <= response.status_code < 500:
                    raise RuntimeError(f"http_{response.status_code}:{url}")
                response.raise_for_status()
                return response.json() if json_data else response.text
            except RuntimeError:
                raise
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                time.sleep(min(2**attempt, 20))
        raise RuntimeError(f"request_failed:{url}:{last_error}")

    def _crossref_by_doi(self, doi: str) -> dict[str, Any] | None:
        value = self.get(f"{CROSSREF_API}/works/{quote(doi, safe='')}")
        message = value.get("message") if isinstance(value, dict) else None
        return _crossref_work(message) if isinstance(message, dict) else None

    def _crossref_works(self, title: str) -> list[dict[str, Any]]:
        value = self.get(
            f"{CROSSREF_API}/works",
            params={"query.title": title, "rows": 5},
        )
        message = value.get("message") if isinstance(value, dict) else None
        items = message.get("items", []) if isinstance(message, dict) else []
        return [
            transformed
            for item in items
            if isinstance(item, dict)
            for transformed in [_crossref_work(item)]
            if transformed
        ]

    def work_by_doi(self, doi: str) -> dict[str, Any] | None:
        errors = []
        if self.openalex_enabled:
            try:
                work = super().work_by_doi(doi)
                if work:
                    return {**work, "_metadata_provider": "OpenAlex"}
            except RuntimeError as exc:
                errors.append(str(exc))
        try:
            return self._crossref_by_doi(doi)
        except RuntimeError as exc:
            errors.append(str(exc))
        if errors:
            raise RuntimeError(";".join(errors))
        return None

    def works(self, title: str) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        errors = []
        if self.openalex_enabled:
            try:
                candidates.extend(
                    {**work, "_metadata_provider": "OpenAlex"}
                    for work in super().works(title)
                    if isinstance(work, dict)
                )
            except RuntimeError as exc:
                errors.append(str(exc))
        try:
            candidates.extend(self._crossref_works(title))
        except RuntimeError as exc:
            errors.append(str(exc))

        deduplicated = {}
        for work in candidates:
            key = str(work.get("doi") or work.get("id") or "")
            if key:
                deduplicated.setdefault(key, work)
        if deduplicated:
            return list(deduplicated.values())
        if errors:
            raise RuntimeError(";".join(errors))
        return []

    def institution(self, institution_id: str) -> dict[str, Any] | None:
        if "ror.org/" in institution_id:
            if institution_id in self.ror_cache:
                return self.ror_cache[institution_id]
            try:
                value = self.get(f"{ROR_API}/organizations/{institution_id.rsplit('/', 1)[-1]}")
            except RuntimeError:
                value = None
            record = _ror_institution(value) if isinstance(value, dict) else None
            self.ror_cache[institution_id] = record
            return record
        if not self.openalex_enabled:
            return None
        value = super().institution(institution_id)
        return {**value, "_metadata_provider": "OpenAlex"} if value else None

    def resolve_affiliation(self, label: str) -> dict[str, Any] | None:
        cache_key = base.norm(label)
        if cache_key in self.ror_cache:
            return self.ror_cache[cache_key]
        try:
            value = self.get(f"{ROR_API}/organizations", params={"affiliation": label})
        except RuntimeError:
            value = None
        items = value.get("items", []) if isinstance(value, dict) else []
        chosen = next(
            (
                item.get("organization")
                for item in items
                if isinstance(item, dict)
                and item.get("chosen") is True
                and isinstance(item.get("organization"), dict)
            ),
            None,
        )
        record = _ror_institution(chosen) if isinstance(chosen, dict) else None
        self.ror_cache[cache_key] = record
        return record

    def resolve_openalex_affiliation(self, label: str) -> dict[str, Any] | None:
        if not self.openalex_enabled:
            return None
        return base.resolve_label(label, self)


def enrich_paper(
    paper: dict[str, Any],
    client: ResilientMetadataClient,
    *,
    arxiv_delay: float = 3.1,
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], str | None]:
    arxiv_id = base.paper_id(paper)
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
    lookup_errors = []
    doi = _clean_doi(metadata.get("doi") or paper.get("doi"))
    if doi:
        try:
            direct = client.work_by_doi(doi)
            if direct:
                work, method, score = base.select_openalex_work(
                    paper, metadata, [direct], doi_match=True
                )
        except RuntimeError as exc:
            lookup_errors.append(str(exc))
    if work is None:
        try:
            candidates = client.works(str(paper.get("title") or metadata.get("title") or ""))
            work, method, score = base.select_openalex_work(paper, metadata, candidates)
        except RuntimeError as exc:
            lookup_errors.append(str(exc))

    arxiv_labels = {
        base.author_sig(str(item.get("name") or "")): item.get("affiliation_labels", [])
        for item in metadata.get("authors", [])
        if isinstance(item, dict)
    }
    paper_authors = [str(name) for name in paper.get("authors", [])]
    institutions: dict[str, dict[str, Any]] = {}
    authors = []
    used_sources = {"arXiv"}
    provider = str(work.get("_metadata_provider") or "OpenAlex") if work else None
    if provider:
        used_sources.add(provider)

    source_authors = work.get("authorships", []) if work else metadata.get("authors", [])
    for item in source_authors or []:
        if not isinstance(item, dict):
            continue
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
            (value for value in paper_authors if base.author_sig(value) == base.author_sig(name)),
            name,
        )
        labels = list(
            dict.fromkeys(
                [
                    str(label).strip()
                    for label in (
                        list(item.get("raw_affiliation_strings") or [])
                        + list(arxiv_labels.get(base.author_sig(name), []))
                    )
                    if str(label).strip()
                ]
            )
        )
        institution_ids = []
        for dehydrated in item.get("institutions", []) if work else []:
            if not isinstance(dehydrated, dict):
                continue
            identifier = str(dehydrated.get("id") or "")
            full = client.institution(identifier) or dehydrated
            pair = institution_record(full)
            if pair:
                key, record = pair
                institutions[key] = record
                institution_ids.append(key)
                used_sources.add(record["source"])

        if not institution_ids:
            for label in labels:
                resolved = client.resolve_affiliation(label)
                if resolved is None:
                    resolved = client.resolve_openalex_affiliation(label)
                pair = institution_record(resolved or {})
                if pair:
                    key, record = pair
                    institutions[key] = record
                    institution_ids.append(key)
                    used_sources.add(record["source"])

        authors.append(
            {
                "paper_author_name": paper_name,
                "name": name,
                "openalex_author_id": (
                    author.get("id") if provider == "OpenAlex" else None
                ),
                "orcid": author.get("orcid"),
                "institution_ids": sorted(set(institution_ids)),
                "affiliation_labels": labels,
            }
        )

    if not any(author["institution_ids"] for author in authors):
        if lookup_errors and not any(arxiv_labels.values()):
            return None, institutions, f"service_error:{';'.join(lookup_errors)}"
        return None, institutions, "no_conservative_match_or_resolved_affiliation"

    provider_prefix = provider.casefold() if provider else "arxiv"
    return (
        {
            "paper_id": arxiv_id,
            "paper_version": paper.get("current_version"),
            "title": paper.get("title"),
            "doi": doi,
            "metadata_work_id": work.get("id") if work else None,
            "openalex_work_id": work.get("id") if provider == "OpenAlex" else None,
            "metadata_provider": provider or "arXiv",
            "match_method": f"{provider_prefix}_{method}" if method else "arxiv_affiliation",
            "match_score": score if work else 1.0,
            "authors": authors,
            "enriched_at": base.now(),
            "sources": sorted(used_sources),
        },
        institutions,
        None,
    )


def run_enrichment(*args, **kwargs):
    original = base.enrich_paper
    base.enrich_paper = enrich_paper
    try:
        return base.run_enrichment(*args, **kwargs)
    finally:
        base.enrich_paper = original


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

    api_key = os.environ.get("OPENALEX_API_KEY") or os.environ.get(
        "OPENALEX_API_KEY_VAR"
    )
    mailto = os.environ.get("METADATA_CONTACT_EMAIL") or os.environ.get(
        "OPENALEX_MAILTO"
    )
    counts = run_enrichment(
        args.input,
        args.output,
        args.state,
        args.limit,
        args.retry_days,
        args.arxiv_delay,
        ResilientMetadataClient(
            mailto=mailto,
            openalex_api_key=api_key,
            ror_client_id=os.environ.get("ROR_CLIENT_ID"),
        ),
    )
    print(json.dumps(counts, indent=2))
    if counts["selected"] and counts["errors"] == counts["selected"]:
        print(
            "::warning::All selected affiliation lookups failed. "
            "Retry diagnostics were written and will be committed."
        )


if __name__ == "__main__":
    main()
