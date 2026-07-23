"""Author activity and co-authorship summaries for the researcher interface."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from itertools import combinations


def _year(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).year
    except ValueError:
        return None


def author_connections(field_papers: list[dict]) -> tuple[list[dict], list[dict]]:
    """Build author activity and real co-authorship links from mapped archive records."""
    author_records: dict[str, list[dict]] = defaultdict(list)
    pair_counts: Counter[tuple[str, str]] = Counter()
    for paper in field_papers:
        authors = list(
            dict.fromkeys(str(name).strip() for name in paper.get("authors", []) if name)
        )
        for author in authors:
            author_records[author].append(paper)
        for first, second in combinations(sorted(authors), 2):
            pair_counts[(first, second)] += 1

    people = []
    for author, records in author_records.items():
        years = sorted(
            {
                year
                for record in records
                if (year := _year(record.get("initial_submission_date"))) is not None
            }
        )
        materials = Counter(
            value
            for record in records
            for value in (record.get("ai_decision") or {}).get("material_or_system_family", [])
        )
        people.append(
            {
                "author": author,
                "papers": len(records),
                "first_year": years[0] if years else None,
                "latest_year": years[-1] if years else None,
                "years": years,
                "materials": [label for label, _ in materials.most_common(3)],
                "records": sorted(
                    records,
                    key=lambda item: item.get("initial_submission_date", ""),
                    reverse=True,
                ),
            }
        )
    people.sort(key=lambda item: (-item["papers"], item["author"]))
    links = [
        {"author_1": pair[0], "author_2": pair[1], "joint_papers": count}
        for pair, count in pair_counts.most_common()
    ]
    return people, links
