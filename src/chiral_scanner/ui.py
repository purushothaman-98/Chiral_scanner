from __future__ import annotations

import math
from collections.abc import Sequence


def paginate(items: Sequence, page: int, page_size: int) -> tuple[list, int, int]:
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    total_pages = max(1, math.ceil(len(items) / page_size))
    safe_page = min(max(page, 1), total_pages)
    start = (safe_page - 1) * page_size
    return list(items[start : start + page_size]), total_pages, safe_page


def flatten_unique(papers: list[dict], path: tuple[str, ...]) -> list[str]:
    values: set[str] = set()
    for paper in papers:
        current = paper
        for key in path:
            current = current.get(key, {}) if isinstance(current, dict) else {}
        if isinstance(current, list):
            values.update(str(value) for value in current if value)
    return sorted(values, key=str.casefold)
