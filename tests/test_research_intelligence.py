from chiral_scanner.config import CURATED_ARXIV_SEEDS
from chiral_scanner.research_intelligence import (
    FUNDED_PROJECTS,
    FUNDING_WATCH,
    INDUSTRY_SIGNALS,
    NEWS,
)


def test_curated_arxiv_seeds_are_normalized_and_unique():
    assert len(CURATED_ARXIV_SEEDS) == len(set(CURATED_ARXIV_SEEDS))
    assert all("/" not in item and item.replace(".", "").isdigit() for item in CURATED_ARXIV_SEEDS)


def test_intelligence_records_use_primary_links():
    records = NEWS + FUNDED_PROJECTS + FUNDING_WATCH + INDUSTRY_SIGNALS
    assert records
    assert all(item["url"].startswith("https://") for item in records)


def test_industry_watchlist_keeps_adjacent_activity_scientifically_bounded():
    assert len(INDUSTRY_SIGNALS) >= 5
    assert {item["signal_type"] for item in INDUSTRY_SIGNALS} >= {
        "Commercial instrumentation",
        "Verified adjacent investment",
    }
    assert all(
        item["evidence"] and item["relevance"] and item["boundary"] for item in INDUSTRY_SIGNALS
    )
    assert all("chiral" in item["boundary"].casefold() for item in INDUSTRY_SIGNALS)
