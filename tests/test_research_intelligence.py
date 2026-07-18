from chiral_scanner.config import CURATED_ARXIV_SEEDS
from chiral_scanner.research_intelligence import FUNDED_PROJECTS, FUNDING_WATCH, NEWS


def test_curated_arxiv_seeds_are_normalized_and_unique():
    assert len(CURATED_ARXIV_SEEDS) == len(set(CURATED_ARXIV_SEEDS))
    assert all("/" not in item and item.replace(".", "").isdigit() for item in CURATED_ARXIV_SEEDS)


def test_intelligence_records_use_primary_links():
    records = NEWS + FUNDED_PROJECTS + FUNDING_WATCH
    assert records
    assert all(item["url"].startswith("https://") for item in records)
