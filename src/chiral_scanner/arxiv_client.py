from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode

import feedparser
import requests

from .config import ARXIV_CATEGORIES, QUERY_EXPRESSIONS

LOGGER = logging.getLogger(__name__)
ARXIV_API = "https://export.arxiv.org/api/query"
VERSION_RE = re.compile(r"v(?P<version>\d+)$", re.IGNORECASE)
ID_RE = re.compile(r"(?:abs/)?(?P<base>\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v(?P<version>\d+))?$")


@dataclass(frozen=True)
class ArxivWindow:
    since: datetime
    until: datetime

    def date_clause(self) -> str:
        start = self.since.astimezone(timezone.utc).strftime("%Y%m%d%H%M")
        end = self.until.astimezone(timezone.utc).strftime("%Y%m%d%H%M")
        submitted = f"submittedDate:[{start} TO {end}]"
        updated = f"lastUpdatedDate:[{start} TO {end}]"
        return f"({submitted} OR {updated})"


def normalize_arxiv_id(raw_id: str) -> tuple[str, str, int]:
    token = raw_id.rstrip("/").split("/abs/")[-1]
    match = ID_RE.search(token)
    if not match:
        raise ValueError(f"Unrecognized arXiv ID: {raw_id}")
    base = match.group("base")
    version = int(match.group("version") or 1)
    return base, f"{base}v{version}", version


def build_queries(window: ArxivWindow) -> list[str]:
    category_clause = " OR ".join(f"cat:{cat}" for cat in ARXIV_CATEGORIES)
    date_clause = window.date_clause()
    return [
        f"({category_clause}) AND ({expression}) AND {date_clause}"
        for expression in QUERY_EXPRESSIONS
    ]


def parse_atom_feed(raw: bytes) -> list[dict]:
    feed = feedparser.parse(raw)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise ValueError(f"Invalid arXiv Atom feed: {feed.bozo_exception}")

    papers: list[dict] = []
    for entry in feed.entries:
        base_id, versioned_id, version = normalize_arxiv_id(entry.id)
        links = {link.get("type", ""): link.get("href") for link in entry.get("links", [])}
        abstract_url = next(
            (link.get("href") for link in entry.get("links", []) if link.get("rel") == "alternate"),
            f"https://arxiv.org/abs/{versioned_id}",
        )
        pdf_url = links.get("application/pdf", f"https://arxiv.org/pdf/{versioned_id}")
        authors = [author.get("name", "").strip() for author in entry.get("authors", [])]
        categories = [tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term")]
        papers.append(
            {
                "base_arxiv_id": base_id,
                "current_version": version,
                "versioned_arxiv_id": versioned_id,
                "title": " ".join(entry.title.split()),
                "authors": authors,
                "abstract": " ".join(entry.summary.split()),
                "initial_submission_date": entry.published,
                "latest_update_date": entry.updated,
                "categories": categories,
                "abstract_url": abstract_url,
                "pdf_url": pdf_url,
                "versions_seen": [versioned_id],
            }
        )
    return papers


def fetch_window(
    window: ArxivWindow,
    *,
    page_size: int = 100,
    max_results_per_query: int = 2000,
    request_delay: float = 3.1,
    user_agent: str = "ChiralScanner/0.1 (https://github.com/purushothaman-98/Chiral_scanner)",
) -> tuple[list[dict], int]:
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})
    deduped: dict[str, dict] = {}
    queries = build_queries(window)

    for query_index, query in enumerate(queries):
        start = 0
        while start < max_results_per_query:
            params = {
                "search_query": query,
                "start": start,
                "max_results": min(page_size, max_results_per_query - start),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            url = f"{ARXIV_API}?{urlencode(params)}"
            LOGGER.info("arXiv query %s/%s page start=%s", query_index + 1, len(queries), start)
            response = session.get(url, timeout=90)
            response.raise_for_status()
            page = parse_atom_feed(response.content)
            if not page:
                break
            for paper in page:
                current = deduped.get(paper["base_arxiv_id"])
                if current is None or paper["current_version"] > current["current_version"]:
                    deduped[paper["base_arxiv_id"]] = paper
            if len(page) < params["max_results"]:
                break
            start += len(page)
            time.sleep(request_delay)
        if query_index < len(queries) - 1:
            time.sleep(request_delay)

    papers = sorted(deduped.values(), key=lambda item: item["latest_update_date"], reverse=True)
    return papers, len(queries)
