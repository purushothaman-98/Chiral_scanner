"""Verified research-location data and geographic summaries."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from itertools import combinations

# Affiliation locations are curated from the linked paper's author-information section.
# Coordinates identify the institution/city, not an individual researcher.
VERIFIED_AFFILIATIONS = [
    {
        "institution": "Tokyo Institute of Technology",
        "city": "Tokyo",
        "country": "Japan",
        "latitude": 35.605,
        "longitude": 139.684,
        "authors": [
            "Kyosuke Ishito",
            "Huiling Mao",
            "Tiantian Zhang",
            "Shuichi Murakami",
            "Takuya Satoh",
        ],
        "evidence_title": "Truly chiral phonons in α-HgS",
        "evidence_url": "https://www.nature.com/articles/s41567-022-01790-x#author-information",
    },
    {
        "institution": "Osaka Metropolitan University",
        "city": "Osaka",
        "country": "Japan",
        "latitude": 34.598,
        "longitude": 135.507,
        "authors": ["Yusuke Kousaka", "Yoshihiko Togawa"],
        "evidence_title": "Truly chiral phonons in α-HgS",
        "evidence_url": "https://www.nature.com/articles/s41567-022-01790-x#author-information",
    },
    {
        "institution": "Okayama University",
        "city": "Okayama",
        "country": "Japan",
        "latitude": 34.687,
        "longitude": 133.920,
        "authors": ["Yusuke Kousaka", "Satoshi Iwasaki"],
        "evidence_title": "Truly chiral phonons in α-HgS",
        "evidence_url": "https://www.nature.com/articles/s41567-022-01790-x#author-information",
    },
    {
        "institution": "Open University of Japan",
        "city": "Chiba",
        "country": "Japan",
        "latitude": 35.647,
        "longitude": 140.049,
        "authors": ["Jun-ichiro Kishine"],
        "evidence_title": "Truly chiral phonons in α-HgS",
        "evidence_url": "https://www.nature.com/articles/s41567-022-01790-x#author-information",
    },
    {
        "institution": "Institute for Molecular Science",
        "city": "Okazaki",
        "country": "Japan",
        "latitude": 34.952,
        "longitude": 137.165,
        "authors": ["Jun-ichiro Kishine"],
        "evidence_title": "Truly chiral phonons in α-HgS",
        "evidence_url": "https://www.nature.com/articles/s41567-022-01790-x#author-information",
    },
]


def _year(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).year
    except ValueError:
        return None


def institution_activity(
    field_papers: list[dict], affiliations: list[dict] | None = None
) -> tuple[list[dict], list[dict], dict[str, int]]:
    """Join verified affiliations to live archive activity and real co-authorship."""
    registry = affiliations if affiliations is not None else VERIFIED_AFFILIATIONS
    author_records: dict[str, list[dict]] = {}
    all_archive_authors = {
        str(author).strip()
        for paper in field_papers
        for author in paper.get("authors", [])
        if str(author).strip()
    }
    for author in all_archive_authors:
        author_records[author] = [
            paper for paper in field_papers if author in paper.get("authors", [])
        ]

    institutions: list[dict] = []
    author_institutions: dict[str, set[str]] = {}
    for item in registry:
        matched_authors = [author for author in item["authors"] if author in author_records]
        records = {
            paper.get("base_arxiv_id", str(id(paper))): paper
            for author in matched_authors
            for paper in author_records[author]
        }
        years = sorted(
            {
                year
                for paper in records.values()
                if (year := _year(paper.get("initial_submission_date"))) is not None
            }
        )
        row = {
            **item,
            "mapped_authors": matched_authors,
            "author_count": len(matched_authors),
            "paper_count": len(records),
            "years": years,
        }
        institutions.append(row)
        for author in matched_authors:
            author_institutions.setdefault(author, set()).add(item["institution"])

    pair_counts: Counter[tuple[str, str]] = Counter()
    for paper in field_papers:
        paper_institutions = sorted(
            {
                institution
                for author in paper.get("authors", [])
                for institution in author_institutions.get(str(author).strip(), set())
            }
        )
        for first, second in combinations(paper_institutions, 2):
            pair_counts[(first, second)] += 1

    links = [
        {"institution_1": pair[0], "institution_2": pair[1], "joint_papers": count}
        for pair, count in pair_counts.most_common()
    ]
    coverage = {
        "archive_authors": len(all_archive_authors),
        "verified_authors": len(set(author_institutions)),
        "verified_institutions": len(registry),
    }
    return institutions, links, coverage
